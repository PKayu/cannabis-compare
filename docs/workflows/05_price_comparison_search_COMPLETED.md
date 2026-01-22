---
description: Implement product search with fuzzy matching, build price comparison table UI, add filtering and sorting, and display daily deals.
auto_execution_mode: 1
---

## Context

This workflow implements the core user-facing feature from PRD sections 4.1 and 5:
- Product search endpoint with fuzzy matching
- Price comparison across dispensaries
- Filtering by product type, price range, THC/CBD%
- Daily deals display with MSRP vs Deal Price
- Performance target: <200ms response time

## Steps

### 1. Read PRD User Flow

Read PRD section 5 to understand the user experience:
- User searches for specific strain
- Sees comparison table with prices
- Filters by product type, price
- Views current promotions/deals

### 2. Create Product Search API Endpoint

Create `backend/routers/search.py`:

```python
"""Product search and filtering endpoints"""
from fastapi import APIRouter, Query, Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Product, Brand, Price, Dispensary, Promotion
from rapidfuzz import fuzz
from typing import List, Optional

router = APIRouter(prefix="/api/products", tags=["products"])

@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=2),
    product_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_thc: Optional[float] = None,
    max_thc: Optional[float] = None,
    sort_by: str = Query("relevance", regex="^(relevance|price_low|price_high|thc)$"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search products with fuzzy matching and filtering.
    Performance target: <200ms
    """

    # Fuzzy search on product names and brands
    products = db.query(Product).filter(Product.is_master == True).all()

    # Score each product by relevance
    scored_products = []
    for product in products:
        name_score = fuzz.token_sort_ratio(q.lower(), product.name.lower()) / 100
        brand_score = fuzz.token_sort_ratio(q.lower(), product.brand.name.lower()) / 100

        relevance_score = max(name_score * 0.8, brand_score * 0.2)

        if relevance_score > 0.5:  # Only return matches >50% similar
            scored_products.append((product, relevance_score))

    # Sort by relevance
    scored_products.sort(key=lambda x: x[1], reverse=True)

    # Apply filters
    filtered = []
    for product, score in scored_products:
        if product_type and product.product_type != product_type:
            continue

        if min_thc and (product.thc_percentage is None or product.thc_percentage < min_thc):
            continue

        if max_thc and (product.thc_percentage is None or product.thc_percentage > max_thc):
            continue

        # Check price ranges across dispensaries
        prices = db.query(Price).filter(Price.product_id == product.id).all()

        if min_price or max_price:
            valid_prices = [p for p in prices if (
                (not min_price or p.amount >= min_price) and
                (not max_price or p.amount <= max_price)
            )]
            if not valid_prices:
                continue

        filtered.append((product, score, prices))

    # Sort results
    if sort_by == "price_low":
        filtered.sort(key=lambda x: min(p.amount for p in x[2]) if x[2] else float('inf'))
    elif sort_by == "price_high":
        filtered.sort(key=lambda x: max(p.amount for p in x[2]) if x[2] else 0, reverse=True)
    elif sort_by == "thc":
        filtered.sort(key=lambda x: x[0].thc_percentage or 0, reverse=True)

    # Return top results
    results = []
    for product, score, prices in filtered[:limit]:
        min_price_val = min(p.amount for p in prices) if prices else None
        max_price_val = max(p.amount for p in prices) if prices else None

        results.append({
            "id": product.id,
            "name": product.name,
            "brand": product.brand.name,
            "thc": product.thc_percentage,
            "cbd": product.cbd_percentage,
            "type": product.product_type,
            "min_price": min_price_val,
            "max_price": max_price_val,
            "dispensary_count": len(prices),
            "relevance_score": round(score, 2)
        })

    return results
```

### 3. Implement Filtering

(Filtering already in step 2 - product_type, price, THC filtering)

### 4. Build Price Comparison Query

Add to `backend/routers/products.py`:

```python
@router.get("/{product_id}/prices")
async def get_price_comparison(
    product_id: str,
    db: Session = Depends(get_db)
):
    """Get all prices for a product across dispensaries"""

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    prices = db.query(Price).filter(Price.product_id == product_id).all()

    comparison = []
    for price in prices:
        # Check for active promotions
        promotions = db.query(Promotion).filter(
            and_(
                Promotion.dispensary_id == price.dispensary_id,
                Promotion.is_active == True,
                Promotion.start_date <= datetime.utcnow(),
                or_(
                    Promotion.end_date == None,
                    Promotion.end_date > datetime.utcnow()
                )
            )
        ).all()

        deal_price = price.amount
        promotion_details = None

        if promotions:
            best_promo = max(
                promotions,
                key=lambda p: p.discount_percentage or 0
            )

            if best_promo.discount_percentage:
                deal_price = price.amount * (1 - best_promo.discount_percentage / 100)

            promotion_details = {
                "title": best_promo.title,
                "discount_percent": best_promo.discount_percentage,
                "discount_amount": best_promo.discount_amount
            }

        comparison.append({
            "dispensary_id": price.dispensary_id,
            "dispensary_name": price.dispensary.name,
            "location": price.dispensary.location,
            "msrp": price.amount,
            "deal_price": deal_price if deal_price != price.amount else None,
            "in_stock": price.in_stock,
            "promotion": promotion_details,
            "last_updated": price.last_updated
        })

    # Sort by price (lowest first)
    comparison.sort(key=lambda x: x["deal_price"] or x["msrp"])

    return comparison
```

### 5. Create Frontend Search Page Component

Create `frontend/app/products/search/page.tsx`:

```typescript
'use client'

import React, { useState } from 'react'
import { api } from '@/lib/api'
import SearchBar from '@/components/SearchBar'
import FilterPanel from '@/components/FilterPanel'
import ResultsTable from '@/components/ResultsTable'

export default function SearchPage() {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState({
    productType: '',
    minPrice: undefined,
    maxPrice: undefined,
    minThc: undefined,
    maxThc: undefined,
    sortBy: 'relevance'
  })

  const handleSearch = async (searchQuery: string) => {
    setQuery(searchQuery)
    setLoading(true)

    try {
      const res = await api.get('/api/products/search', {
        params: {
          q: searchQuery,
          ...filters
        }
      })
      setResults(res.data)
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Compliance Banner */}
      <div className="compliance-banner max-w-6xl mx-auto">
        <p className="text-sm">
          ⚠️ For informational purposes only. Not affiliated with any dispensary.
        </p>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold mb-8 text-cannabis-700">Find Your Strain</h1>

        <SearchBar onSearch={handleSearch} />

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mt-8">
          <div>
            <FilterPanel filters={filters} onChange={setFilters} />
          </div>

          <div className="md:col-span-3">
            {loading && <div className="text-center py-8">Searching...</div>}
            {!loading && results.length === 0 && query && (
              <div className="text-center py-8 text-gray-600">No results found</div>
            )}
            {results.length > 0 && (
              <>
                <p className="text-gray-600 mb-4">{results.length} results found</p>
                <ResultsTable products={results} />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
```

### 6. Build Search Bar with Autocomplete

Create `frontend/components/SearchBar.tsx`:

```typescript
import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface SearchBarProps {
  onSearch: (query: string) => Promise<void>
}

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState([])

  const handleInputChange = async (value: string) => {
    setQuery(value)

    if (value.length > 2) {
      try {
        const res = await api.get('/api/products/autocomplete', {
          params: { q: value }
        })
        setSuggestions(res.data)
      } catch (error) {
        console.error('Autocomplete failed:', error)
      }
    } else {
      setSuggestions([])
    }
  }

  const handleSubmit = async (e: React.FormEvent, value?: string) => {
    e.preventDefault()
    const searchTerm = value || query
    setSuggestions([])
    await onSearch(searchTerm)
  }

  return (
    <div className="relative">
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => handleInputChange(e.target.value)}
            placeholder="Search for strains, brands, or effects..."
            className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-cannabis-500"
          />
          <button
            type="submit"
            className="px-6 py-3 bg-cannabis-600 text-white rounded-lg hover:bg-cannabis-700"
          >
            Search
          </button>
        </div>
      </form>

      {suggestions.length > 0 && (
        <div className="absolute z-10 w-full bg-white border rounded-lg shadow-lg">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.id}
              onClick={(e) => handleSubmit(e, suggestion.name)}
              className="w-full text-left px-4 py-2 hover:bg-gray-100"
            >
              <strong>{suggestion.name}</strong> · {suggestion.brand}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
```

### 7. Implement Comparison Table UI

Create `frontend/components/ResultsTable.tsx` showing product name, brand, prices, stock status.

### 8. Add Deal Badge Display

Add promotion display to results showing MSRP vs Deal Price with discount badge.

### 9. Implement Sorting

(Sorting already in API endpoint - relevance, price_low, price_high, thc)

### 10. Test Search Performance

```bash
# Test search response time
time curl "http://localhost:8000/api/products/search?q=gorilla&limit=50"

# Should return <200ms
```

## Success Criteria

- [ ] Search endpoint returns results in <200ms
- [ ] Fuzzy matching works for similar strain names
- [ ] Product type filtering functional
- [ ] Price range filtering works
- [ ] THC/CBD filtering operational
- [ ] Price comparison shows all dispensaries
- [ ] Sorting by price, relevance working
- [ ] Frontend search page displays results
- [ ] Search bar with autocomplete functional
- [ ] Comparison table shows MSRP and deal prices
- [ ] Deal badges display correctly
- [ ] Mobile responsive design
- [ ] No TypeScript errors in frontend
