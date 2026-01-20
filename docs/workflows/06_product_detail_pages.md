---
description: Create dynamic product detail pages with pharmacy prices, historical pricing charts, promotion badges, and deep-linking to pharmacies.
auto_execution_mode: 1
---

## Context

This workflow implements individual product pages as defined in PRD section 5 (Finding a Deal):
- Dynamic routes for each product
- All pharmacies and prices for that product
- Historical pricing trends
- Current promotions with deal badges
- External pharmacy checkout links

## Steps

### 1. Create Dynamic Route for /products/[id]

Create `frontend/app/products/[id]/page.tsx`:

```typescript
'use client'

import React, { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { api } from '@/lib/api'
import PriceComparisonTable from '@/components/PriceComparisonTable'
import PricingChart from '@/components/PricingChart'
import ReviewsSection from '@/components/ReviewsSection'

export default function ProductDetailPage() {
  const params = useParams()
  const productId = params.id as string
  const [product, setProduct] = useState(null)
  const [prices, setPrices] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProductData()
  }, [productId])

  const loadProductData = async () => {
    try {
      const [productRes, pricesRes] = await Promise.all([
        api.get(`/api/products/${productId}`),
        api.get(`/api/products/${productId}/prices`)
      ])
      setProduct(productRes.data)
      setPrices(pricesRes.data)
    } catch (error) {
      console.error('Failed to load product:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div>Loading...</div>
  if (!product) return <div>Product not found</div>

  const bestPrice = prices.length > 0 ? prices[0] : null

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Product Header */}
      <div className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <h1 className="text-4xl font-bold text-cannabis-700">{product.name}</h1>
          <p className="text-xl text-gray-600 mt-2">{product.brand}</p>

          <div className="grid grid-cols-3 gap-4 mt-6">
            {product.thc !== null && (
              <div className="bg-cannabis-50 p-4 rounded">
                <p className="text-gray-600">THC</p>
                <p className="text-2xl font-bold text-cannabis-700">{product.thc}%</p>
              </div>
            )}
            {product.cbd !== null && (
              <div className="bg-blue-50 p-4 rounded">
                <p className="text-gray-600">CBD</p>
                <p className="text-2xl font-bold text-blue-700">{product.cbd}%</p>
              </div>
            )}
            {bestPrice && (
              <div className="bg-green-50 p-4 rounded">
                <p className="text-gray-600">Best Price</p>
                <p className="text-2xl font-bold text-green-700">
                  ${bestPrice.deal_price || bestPrice.msrp}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Price Comparison */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold mb-4">Prices Across Dispensaries</h2>
          <PriceComparisonTable prices={prices} productId={productId} />
        </section>

        {/* Pricing History */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold mb-4">Price History</h2>
          <PricingChart productId={productId} />
        </section>

        {/* Reviews */}
        <section>
          <h2 className="text-2xl font-bold mb-4">Community Reviews</h2>
          <ReviewsSection productId={productId} />
        </section>
      </div>
    </div>
  )
}
```

### 2. Build Product Detail API Endpoint

Create `backend/routers/products.py`:

```python
"""Product endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Product, Price, Review

router = APIRouter(prefix="/api/products", tags=["products"])

@router.get("/{product_id}", response_model=dict)
async def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get product details"""

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    review_count = db.query(Review).filter(Review.product_id == product_id).count()
    avg_rating = db.query(Review).filter(Review.product_id == product_id).with_entities(
        func.avg(Review.rating)
    ).scalar()

    return {
        "id": product.id,
        "name": product.name,
        "brand": product.brand.name,
        "type": product.product_type,
        "thc": product.thc_percentage,
        "cbd": product.cbd_percentage,
        "review_count": review_count,
        "avg_rating": round(avg_rating, 1) if avg_rating else None,
        "created_at": product.created_at
    }
```

### 3. Add Historical Pricing Query

Add to `backend/routers/products.py`:

```python
@router.get("/{product_id}/pricing-history")
async def get_pricing_history(
    product_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get historical pricing for a product"""

    from datetime import datetime, timedelta

    start_date = datetime.utcnow() - timedelta(days=days)

    prices = db.query(Price).filter(
        and_(
            Price.product_id == product_id,
            Price.last_updated >= start_date
        )
    ).all()

    if not prices:
        return []

    # Group by date
    history_by_date = {}
    for price in prices:
        date = price.last_updated.date()
        if date not in history_by_date:
            history_by_date[date] = []
        history_by_date[date].append(price.amount)

    # Calculate daily min/max/avg
    return [
        {
            "date": str(date),
            "min": min(amounts),
            "max": max(amounts),
            "avg": sum(amounts) / len(amounts)
        }
        for date, amounts in sorted(history_by_date.items())
    ]
```

### 4. Create Product Detail Page Component

(Already in step 1)

### 5. Build Pharmacy Price Table with Stock Status

Create `frontend/components/PriceComparisonTable.tsx`:

```typescript
interface Price {
  dispensary_id: string
  dispensary_name: string
  location: string
  msrp: number
  deal_price: number | null
  in_stock: boolean
  promotion: {
    title: string
    discount_percent: number
  } | null
}

export default function PriceComparisonTable({ prices, productId }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="text-left px-4 py-2">Dispensary</th>
            <th className="text-right px-4 py-2">MSRP</th>
            <th className="text-right px-4 py-2">Deal Price</th>
            <th className="text-center px-4 py-2">In Stock</th>
            <th className="text-center px-4 py-2">Action</th>
          </tr>
        </thead>
        <tbody>
          {prices.map((price) => (
            <tr key={price.dispensary_id} className="border-b hover:bg-gray-50">
              <td className="px-4 py-3">
                <div>
                  <p className="font-semibold">{price.dispensary_name}</p>
                  <p className="text-sm text-gray-600">{price.location}</p>
                </div>
              </td>
              <td className="text-right px-4 py-3">${price.msrp.toFixed(2)}</td>
              <td className="text-right px-4 py-3">
                {price.deal_price ? (
                  <div>
                    <p className="text-green-600 font-bold">${price.deal_price.toFixed(2)}</p>
                    {price.promotion && (
                      <p className="text-xs text-green-600">{price.promotion.discount_percent}% off</p>
                    )}
                  </div>
                ) : (
                  <span className="text-gray-400">-</span>
                )}
              </td>
              <td className="text-center px-4 py-3">
                {price.in_stock ? (
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                    In Stock
                  </span>
                ) : (
                  <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
                    Out of Stock
                  </span>
                )}
              </td>
              <td className="text-center px-4 py-3">
                <a
                  href={`https://${price.dispensary_id}.com/products/${productId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1 bg-cannabis-600 text-white rounded text-sm hover:bg-cannabis-700"
                >
                  Order
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

### 6. Add Promotion Badges

(Shown in PriceComparisonTable component above)

### 7. Implement "Order at Pharmacy X" Deep-Linking

Create `backend/utils/deep_linker.py`:

```python
"""Generate deep links to pharmacy checkout pages"""

DISPENSARY_CHECKOUT_PATTERNS = {
    "wholesome-co": "https://www.wholesomeco.com/products/{product_id}",
    "dragonfly": "https://dragonfly.menu/product/{product_id}",
    "curaleaf": "https://curaleaf.com/dispensaries/utah/products/{product_id}"
}

def generate_pharmacy_deep_link(dispensary_id: str, product_name: str, product_id: str) -> str:
    """Generate deep link to pharmacy product page"""

    if dispensary_id in DISPENSARY_CHECKOUT_PATTERNS:
        base_url = DISPENSARY_CHECKOUT_PATTERNS[dispensary_id]
        return base_url.format(product_id=product_id)

    # Fallback: search on dispensary main page
    return f"https://{dispensary_id}.com/search?q={product_name.replace(' ', '+')}"
```

### 8. Add Metadata for SEO

Update `frontend/app/products/[id]/page.tsx`:

```typescript
import { Metadata } from 'next'

export async function generateMetadata({ params }): Promise<Metadata> {
  const product = await api.get(`/api/products/${params.id}`)

  return {
    title: `${product.data.name} - Utah Cannabis Aggregator`,
    description: `Compare prices for ${product.data.name} by ${product.data.brand} across Utah dispensaries`,
    openGraph: {
      title: product.data.name,
      description: `${product.data.thc}% THC - Best price: See all dispensaries`
    }
  }
}
```

### 9. Verify Mobile Responsiveness

Test on mobile devices:
- Table should scroll horizontally on small screens
- Product header should stack vertically
- Buttons should be touch-friendly (min 44px)

## Success Criteria

- [ ] Dynamic product routes working for all products
- [ ] Product detail API endpoint returns correct data
- [ ] Historical pricing query functional
- [ ] Product detail page displays all information
- [ ] Pharmacy price table shows all dispensaries
- [ ] Stock status shows correctly (In Stock / Out of Stock)
- [ ] Promotion badges display discount information
- [ ] Deep links to pharmacy sites functional
- [ ] SEO metadata included for search engines
- [ ] Mobile responsive layout verified
- [ ] No TypeScript errors
