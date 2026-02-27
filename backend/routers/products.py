"""Product detail and price comparison endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from database import get_db
from models import Product, Price, Dispensary, Promotion
from rapidfuzz import fuzz
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed product information by ID.

    Args:
        product_id: UUID of the product
        db: Database session

    Returns:
        Product details with brand information

    Raises:
        HTTPException: 404 if product not found
    """

    product = (
        db.query(Product)
        .options(joinedload(Product.brand))
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # If this is a variant, resolve to its parent
    if not product.is_master and product.master_product_id:
        product = (
            db.query(Product)
            .options(joinedload(Product.brand))
            .filter(Product.id == product.master_product_id)
            .first()
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

    # Get variants for this parent
    variants = (
        db.query(Product)
        .filter(
            Product.master_product_id == product.id,
            Product.is_master == False
        )
        .order_by(Product.weight_grams.asc().nullslast())
        .all()
    )

    return {
        "id": str(product.id),
        "name": product.name,
        "brand": product.brand.name if product.brand else None,
        "brand_id": str(product.brand_id) if product.brand_id else None,
        "product_type": product.product_type,
        "thc_percentage": product.thc_percentage,
        "cbd_percentage": product.cbd_percentage,
        "is_master": product.is_master,
        "normalization_confidence": product.normalization_confidence,
        "variants": [
            {
                "id": str(v.id),
                "weight": v.weight,
                "weight_grams": v.weight_grams,
            }
            for v in variants
        ],
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None
    }


@router.get("/{product_id}/prices")
async def get_price_comparison(
    product_id: str,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get price comparison for a product across all dispensaries, grouped by weight.

    Returns prices grouped by variant weight for apples-to-apples comparison.

    Args:
        product_id: UUID of the product (parent or variant)
        db: Database session

    Returns:
        List of weight groups, each containing prices sorted by lowest first

    Raises:
        HTTPException: 404 if product not found
    """

    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Resolve to parent if variant
    parent_id = product.id if product.is_master else product.master_product_id
    if not parent_id:
        parent_id = product.id

    # Get all variants for this parent
    variants = (
        db.query(Product)
        .filter(
            Product.master_product_id == parent_id,
            Product.is_master == False
        )
        .order_by(Product.weight_grams.asc().nullslast())
        .all()
    )

    # If no variants exist yet, fall back to querying prices on the product itself
    if not variants:
        variants = [product]

    current_time = datetime.now(timezone.utc)
    result = []

    for variant in variants:
        prices = (
            db.query(Price)
            .options(joinedload(Price.dispensary))
            .filter(Price.product_id == variant.id)
            .all()
        )

        if not prices:
            continue

        comparison = []
        for price in prices:
            # Find active promotions for this dispensary
            active_promotions = (
                db.query(Promotion)
                .filter(
                    and_(
                        Promotion.dispensary_id == price.dispensary_id,
                        Promotion.is_active == True,
                        Promotion.start_date <= current_time,
                        or_(
                            Promotion.end_date == None,
                            Promotion.end_date > current_time
                        )
                    )
                )
                .all()
            )

            # Calculate best deal price
            deal_price = price.amount
            best_promotion = None

            if active_promotions:
                for promo in active_promotions:
                    if promo.discount_percentage:
                        promo_price = price.amount * (1 - promo.discount_percentage / 100)
                        if promo_price < deal_price:
                            deal_price = promo_price
                            best_promotion = promo
                    elif promo.discount_amount:
                        promo_price = max(0, price.amount - promo.discount_amount)
                        if promo_price < deal_price:
                            deal_price = promo_price
                            best_promotion = promo

            promotion_details = None
            if best_promotion:
                promotion_details = {
                    "id": str(best_promotion.id),
                    "title": best_promotion.title,
                    "description": best_promotion.description,
                    "discount_percentage": best_promotion.discount_percentage,
                    "discount_amount": float(best_promotion.discount_amount) if best_promotion.discount_amount else None,
                    "recurring_pattern": best_promotion.recurring_pattern,
                    "start_date": best_promotion.start_date.isoformat(),
                    "end_date": best_promotion.end_date.isoformat() if best_promotion.end_date else None
                }

            savings = price.amount - deal_price if deal_price < price.amount else 0
            savings_percentage = (savings / price.amount * 100) if savings > 0 else 0

            comparison.append({
                "dispensary_id": str(price.dispensary_id),
                "dispensary_name": price.dispensary.name,
                "dispensary_location": price.dispensary.location,
                "dispensary_hours": price.dispensary.hours,
                "dispensary_website": price.dispensary.website,
                "product_url": price.product_url,
                "msrp": float(price.amount),
                "deal_price": float(deal_price) if deal_price < price.amount else None,
                "savings": float(savings) if savings > 0 else None,
                "savings_percentage": round(savings_percentage, 1) if savings > 0 else None,
                "in_stock": price.in_stock,
                "promotion": promotion_details,
                "price_change_percentage": price.price_change_percentage,
                "last_updated": price.last_updated.isoformat() if price.last_updated else None
            })

        comparison.sort(key=lambda x: x["deal_price"] if x["deal_price"] else x["msrp"])

        result.append({
            "variant_id": str(variant.id),
            "weight": variant.weight,
            "weight_grams": variant.weight_grams,
            "prices": comparison
        })

    return result


@router.get("/{product_id}/related")
async def get_related_products(
    product_id: str,
    limit: int = Query(8, ge=1, le=20, description="Maximum number of related products"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get similar products using fuzzy name matching within the same product type.

    Scores all same-type products against the target using WRatio fuzzy matching,
    returning the most similar products sorted by similarity score.

    Args:
        product_id: UUID of the product
        limit: Maximum number of related products (default 8)
        db: Database session

    Returns:
        List of similar products with similarity scores and pricing

    Raises:
        HTTPException: 404 if product not found
    """

    product = (
        db.query(Product)
        .options(joinedload(Product.brand))
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Resolve to master product if this is a variant
    target = product
    if not product.is_master and product.master_product_id:
        master = db.query(Product).options(joinedload(Product.brand)).filter(
            Product.id == product.master_product_id
        ).first()
        if master:
            target = master

    # Load all master products of the same type (excluding the target)
    candidates = (
        db.query(Product)
        .options(joinedload(Product.brand))
        .filter(
            Product.is_master.is_(True),
            Product.id != target.id,
            Product.product_type == target.product_type,
        )
        .all()
    )

    # Score each candidate by fuzzy name similarity
    target_name = target.name.lower()
    scored = []
    for c in candidates:
        score = fuzz.WRatio(target_name, c.name.lower()) / 100.0
        if score >= 0.60:
            scored.append((c, score))

    # Sort by similarity descending, take top N
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:limit]

    results = []
    for p, similarity in top:
        # Get price range across all variants
        variant_ids = [
            v.id for v in
            db.query(Product.id).filter(Product.master_product_id == p.id).all()
        ]
        price_product_ids = variant_ids if variant_ids else [p.id]

        prices = db.query(Price).filter(
            Price.product_id.in_(price_product_ids),
            Price.in_stock.is_(True)
        ).all()

        if prices:
            min_price = min(price.amount for price in prices)
            max_price = max(price.amount for price in prices)
        else:
            min_price = None
            max_price = None

        results.append({
            "id": str(p.id),
            "name": p.name,
            "brand": p.brand.name if p.brand else None,
            "product_type": p.product_type,
            "thc_percentage": p.thc_percentage,
            "cbd_percentage": p.cbd_percentage,
            "min_price": float(min_price) if min_price else None,
            "max_price": float(max_price) if max_price else None,
            "similarity_score": round(similarity, 2),
        })

    return results


@router.get("/{product_id}/pricing-history")
async def get_pricing_history(
    product_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get historical pricing for a product over the specified number of days.

    Args:
        product_id: UUID of the product
        days: Number of days of history (1-365, default 30)
        db: Database session

    Returns:
        List of daily price statistics (min, max, avg) sorted by date
    """

    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Resolve to parent
    parent_id = product.id if product.is_master else (product.master_product_id or product.id)

    # Get all variant IDs for this parent
    variant_ids = [
        v.id for v in
        db.query(Product.id).filter(Product.master_product_id == parent_id).all()
    ]
    # Include parent ID as fallback
    price_product_ids = variant_ids if variant_ids else [parent_id]

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get price records within the date range across all variants
    prices = (
        db.query(Price)
        .filter(
            and_(
                Price.product_id.in_(price_product_ids),
                Price.last_updated >= start_date
            )
        )
        .all()
    )

    if not prices:
        return []

    # Group prices by date
    history_by_date: Dict[str, List[float]] = {}
    for price in prices:
        if price.last_updated:
            date_str = price.last_updated.strftime("%Y-%m-%d")
            if date_str not in history_by_date:
                history_by_date[date_str] = []
            history_by_date[date_str].append(float(price.amount))

    # Calculate daily statistics
    return [
        {
            "date": date,
            "min": min(amounts),
            "max": max(amounts),
            "avg": round(sum(amounts) / len(amounts), 2)
        }
        for date, amounts in sorted(history_by_date.items())
    ]
