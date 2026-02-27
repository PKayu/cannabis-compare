"""Product search and autocomplete endpoints with fuzzy matching"""
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from database import get_db
from models import Product, Brand, Price, Dispensary
from rapidfuzz import fuzz
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/api/products", tags=["products", "search"])


@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=2, description="Search query for product names or brands"),
    product_type: Optional[str] = Query(None, description="Filter by product type (Flower, Concentrate, Edible, etc.)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    min_thc: Optional[float] = Query(None, ge=0, le=100, description="Minimum THC percentage"),
    max_thc: Optional[float] = Query(None, ge=0, le=100, description="Maximum THC percentage"),
    min_cbd: Optional[float] = Query(None, ge=0, le=100, description="Minimum CBD percentage"),
    max_cbd: Optional[float] = Query(None, ge=0, le=100, description="Maximum CBD percentage"),
    sort_by: str = Query("relevance", pattern="^(relevance|price_low|price_high|thc|cbd)$", description="Sort order"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Search products with fuzzy matching and filtering.

    Uses ILIKE pre-filtering to narrow candidates, then WRatio multi-strategy
    fuzzy scoring with an exact-substring bonus for precise relevancy.

    Args:
        q: Search query string (minimum 2 characters)
        product_type: Optional filter by product category
        min_price: Optional minimum price across all dispensaries
        max_price: Optional maximum price across all dispensaries
        min_thc: Optional minimum THC percentage
        max_thc: Optional maximum THC percentage
        min_cbd: Optional minimum CBD percentage
        max_cbd: Optional maximum CBD percentage
        sort_by: Sort order (relevance, price_low, price_high, thc, cbd)
        limit: Maximum results to return
        db: Database session

    Returns:
        List of product dictionaries with pricing and relevance info
    """

    query_lower = q.strip().lower()

    # Pre-filter: only load products whose name contains at least one query word.
    # This dramatically reduces the candidate pool before expensive fuzzy matching.
    # Falls back to all products if the pre-filter yields no candidates (handles
    # plural/singular mismatches like "gummies" vs "gummy").
    words = [w for w in query_lower.split() if len(w) >= 2]
    base_query = (
        db.query(Product)
        .options(joinedload(Product.brand))
        .filter(Product.is_master.is_(True))
    )
    if words:
        ilike_filters = []
        for w in words:
            ilike_filters.append(Product.name.ilike(f"%{w}%"))
        filtered_query = base_query.filter(or_(*ilike_filters))
        products = filtered_query.all()

        # Fallback: if ILIKE pre-filter is too strict (e.g. plural/singular mismatch),
        # load all products and let fuzzy matching handle it
        if not products:
            products = base_query.all()
    else:
        products = base_query.all()

    # Score each product using WRatio (best-of multiple fuzzy strategies)
    scored_products = []

    for product in products:
        product_name_lower = product.name.lower()

        # WRatio automatically picks the best of ratio, partial_ratio,
        # token_sort_ratio, and token_set_ratio per comparison
        name_score = fuzz.WRatio(query_lower, product_name_lower) / 100.0
        brand_score = (
            fuzz.WRatio(query_lower, product.brand.name.lower()) / 100.0
            if product.brand else 0.0
        )

        # Weighted relevance: 80% product name, 20% brand name
        relevance_score = (name_score * 0.8) + (brand_score * 0.2)

        # Exact-substring bonus: if the query appears verbatim in the product name
        if query_lower in product_name_lower:
            relevance_score = min(relevance_score + 0.15, 1.0)

        # Threshold: 40% minimum to reduce false positives
        if relevance_score >= 0.4:
            scored_products.append((product, relevance_score))

    # Sort by relevance initially
    scored_products.sort(key=lambda x: x[1], reverse=True)

    # Apply filters and gather price data
    filtered = []
    for product, score in scored_products:
        # Filter by product type (case-insensitive)
        if product_type:
            if product.product_type.lower() != product_type.lower():
                continue

        # Filter by THC percentage
        if min_thc is not None and (product.thc_percentage is None or product.thc_percentage < min_thc):
            continue
        if max_thc is not None and (product.thc_percentage is None or product.thc_percentage > max_thc):
            continue

        # Filter by CBD percentage
        if min_cbd is not None and (product.cbd_percentage is None or product.cbd_percentage < min_cbd):
            continue
        if max_cbd is not None and (product.cbd_percentage is None or product.cbd_percentage > max_cbd):
            continue

        # Get prices across all variants for this parent product
        variant_ids = [
            v.id for v in
            db.query(Product.id).filter(Product.master_product_id == product.id).all()
        ]
        price_product_ids = variant_ids if variant_ids else [product.id]
        prices = db.query(Price).filter(
            Price.product_id.in_(price_product_ids),
            Price.in_stock == True
        ).all()

        # Skip products with no prices
        if not prices:
            continue

        # Filter by price range if specified
        if min_price is not None or max_price is not None:
            valid_prices = [
                p for p in prices
                if (min_price is None or p.amount >= min_price) and
                   (max_price is None or p.amount <= max_price)
            ]
            # Don't skip product entirely, just use filtered prices
            prices = valid_prices

        # Skip products with no valid prices after all filtering
        if not prices:
            continue

        filtered.append((product, score, prices))

    # Apply sorting
    if sort_by == "price_low":
        filtered.sort(key=lambda x: min(p.amount for p in x[2]))
    elif sort_by == "price_high":
        filtered.sort(key=lambda x: min(p.amount for p in x[2]), reverse=True)
    elif sort_by == "thc":
        filtered.sort(key=lambda x: x[0].thc_percentage or 0, reverse=True)
    elif sort_by == "cbd":
        filtered.sort(key=lambda x: x[0].cbd_percentage or 0, reverse=True)
    # else: relevance sort already applied

    # Build response data
    results = []
    for product, score, prices in filtered[:limit]:
        min_price_val = min(p.amount for p in prices)
        max_price_val = max(p.amount for p in prices)

        # Collect available weights from variants
        variants = db.query(Product).filter(
            Product.master_product_id == product.id,
            Product.is_master == False
        ).all()
        available_weights = sorted(set(
            v.weight for v in variants if v.weight
        ))

        results.append({
            "id": str(product.id),
            "name": product.name,
            "brand": product.brand.name if product.brand else None,
            "brand_id": str(product.brand_id) if product.brand_id else None,
            "thc": product.thc_percentage,
            "cbd": product.cbd_percentage,
            "type": product.product_type,
            "min_price": float(min_price_val),
            "max_price": float(max_price_val),
            "dispensary_count": len(set(p.dispensary_id for p in prices)),
            "available_weights": available_weights,
            "relevance_score": round(score, 2)
        })

    return results


@router.get("/autocomplete")
async def autocomplete_products(
    q: str = Query(..., min_length=2, description="Autocomplete query"),
    limit: int = Query(10, ge=1, le=20, description="Maximum suggestions"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Autocomplete endpoint for search suggestions.

    Uses fast ILIKE prefix matching for quick suggestions.

    Args:
        q: Query string (minimum 2 characters)
        limit: Maximum number of suggestions
        db: Database session

    Returns:
        List of product suggestions with id, name, and brand
    """

    # Use ILIKE for fast prefix matching (case-insensitive)
    query_pattern = f"%{q}%"

    products = (
        db.query(Product)
        .options(joinedload(Product.brand))
        .filter(
            Product.is_master == True,
            Product.name.ilike(query_pattern)
        )
        .limit(limit)
        .all()
    )

    suggestions = [
        {
            "id": str(product.id),
            "name": product.name,
            "brand": product.brand.name if product.brand else None,
            "type": product.product_type
        }
        for product in products
    ]

    return suggestions
