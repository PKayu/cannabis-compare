"""Product detail and price comparison endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from database import get_db
from models import Product, Price, Dispensary, Promotion
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
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None
    }


@router.get("/{product_id}/prices")
async def get_price_comparison(
    product_id: str,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get price comparison for a product across all dispensaries.

    Includes active promotions and calculates deal prices.

    Args:
        product_id: UUID of the product
        db: Database session

    Returns:
        List of prices sorted by final price (lowest first)

    Raises:
        HTTPException: 404 if product not found
    """

    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get all prices for this product with dispensary info
    prices = (
        db.query(Price)
        .options(joinedload(Price.dispensary))
        .filter(Price.product_id == product_id)
        .all()
    )

    if not prices:
        return []

    # Build comparison data
    comparison = []
    current_time = datetime.now(timezone.utc)

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
            # Find promotion with highest discount
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

        # Build promotion details if applicable
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

        # Calculate savings
        savings = price.amount - deal_price if deal_price < price.amount else 0
        savings_percentage = (savings / price.amount * 100) if savings > 0 else 0

        comparison.append({
            "dispensary_id": str(price.dispensary_id),
            "dispensary_name": price.dispensary.name,
            "dispensary_location": price.dispensary.location,
            "dispensary_hours": price.dispensary.hours,
            "dispensary_website": price.dispensary.website,
            "msrp": float(price.amount),
            "deal_price": float(deal_price) if deal_price < price.amount else None,
            "savings": float(savings) if savings > 0 else None,
            "savings_percentage": round(savings_percentage, 1) if savings > 0 else None,
            "in_stock": price.in_stock,
            "promotion": promotion_details,
            "price_change_percentage": price.price_change_percentage,
            "last_updated": price.last_updated.isoformat() if price.last_updated else None
        })

    # Sort by final price (deal price if available, otherwise MSRP)
    comparison.sort(key=lambda x: x["deal_price"] if x["deal_price"] else x["msrp"])

    return comparison


@router.get("/{product_id}/related")
async def get_related_products(
    product_id: str,
    limit: int = 5,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get related products based on brand and product type.

    Args:
        product_id: UUID of the product
        limit: Maximum number of related products
        db: Database session

    Returns:
        List of related products

    Raises:
        HTTPException: 404 if product not found
    """

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Find products from same brand or same type
    related = (
        db.query(Product)
        .options(joinedload(Product.brand))
        .filter(
            Product.is_master == True,
            Product.id != product_id,
            or_(
                Product.brand_id == product.brand_id,
                Product.product_type == product.product_type
            )
        )
        .limit(limit)
        .all()
    )

    results = []
    for p in related:
        # Get price range
        prices = db.query(Price).filter(Price.product_id == p.id, Price.in_stock == True).all()
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
            "max_price": float(max_price) if max_price else None
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

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get price records within the date range
    # Note: In production, you'd want a separate price_history table
    # For now, we'll use the current prices table with last_updated
    prices = (
        db.query(Price)
        .filter(
            and_(
                Price.product_id == product_id,
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
