"""Dispensary listing and detail endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from database import get_db
from models import Dispensary, Price, Product, Promotion
from datetime import datetime
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/dispensaries", tags=["dispensaries"])


@router.get("/")
async def list_dispensaries(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
) -> List[Dict[str, Any]]:
    """
    List all Utah dispensaries with inventory counts.

    Args:
        db: Database session
        limit: Maximum number of dispensaries to return (1-100)
        skip: Number of dispensaries to skip (pagination)

    Returns:
        List of dispensaries with product counts and hours
    """

    dispensaries = db.query(Dispensary).offset(skip).limit(limit).all()

    results = []
    for disp in dispensaries:
        # Count distinct products in stock at this dispensary
        product_count = (
            db.query(func.count(func.distinct(Price.product_id)))
            .filter(
                Price.dispensary_id == disp.id,
                Price.in_stock == True
            )
            .scalar()
        )

        # Count active promotions
        current_time = datetime.utcnow()
        promo_count = (
            db.query(func.count(Promotion.id))
            .filter(
                and_(
                    Promotion.dispensary_id == disp.id,
                    Promotion.is_active == True,
                    Promotion.start_date <= current_time,
                    or_(
                        Promotion.end_date == None,
                        Promotion.end_date > current_time
                    )
                )
            )
            .scalar()
        )

        results.append({
            "id": str(disp.id),
            "name": disp.name,
            "location": disp.location,
            "hours": disp.hours,
            "website": disp.website,
            "product_count": product_count or 0,
            "active_promotions": promo_count or 0,
            "created_at": disp.created_at.isoformat() if disp.created_at else None
        })

    return results


@router.get("/{dispensary_id}")
async def get_dispensary_detail(
    dispensary_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed dispensary information including promotions.

    Args:
        dispensary_id: UUID of the dispensary
        db: Database session

    Returns:
        Dispensary details with active promotions

    Raises:
        HTTPException: 404 if dispensary not found
    """

    disp = db.query(Dispensary).filter(Dispensary.id == dispensary_id).first()
    if not disp:
        raise HTTPException(status_code=404, detail="Dispensary not found")

    # Count products in stock
    product_count = (
        db.query(func.count(func.distinct(Price.product_id)))
        .filter(
            Price.dispensary_id == dispensary_id,
            Price.in_stock == True
        )
        .scalar()
    )

    # Get active promotions
    current_time = datetime.utcnow()
    promotions = (
        db.query(Promotion)
        .filter(
            and_(
                Promotion.dispensary_id == dispensary_id,
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

    promotion_list = []
    for promo in promotions:
        promotion_list.append({
            "id": str(promo.id),
            "title": promo.title,
            "description": promo.description,
            "discount_percentage": promo.discount_percentage,
            "discount_amount": float(promo.discount_amount) if promo.discount_amount else None,
            "recurring_pattern": promo.recurring_pattern,
            "start_date": promo.start_date.isoformat(),
            "end_date": promo.end_date.isoformat() if promo.end_date else None
        })

    return {
        "id": str(disp.id),
        "name": disp.name,
        "location": disp.location,
        "hours": disp.hours,
        "website": disp.website,
        "product_count": product_count or 0,
        "promotions": promotion_list,
        "created_at": disp.created_at.isoformat() if disp.created_at else None
    }


@router.get("/{dispensary_id}/inventory")
async def get_dispensary_inventory(
    dispensary_id: str,
    product_type: Optional[str] = None,
    in_stock_only: bool = True,
    sort_by: str = Query("name", pattern="^(name|price_low|price_high|thc|cbd)$"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get inventory (products and prices) for a dispensary.

    Args:
        dispensary_id: UUID of the dispensary
        product_type: Filter by product type (Flower, Vape, etc.)
        in_stock_only: Only show in-stock items (default True)
        sort_by: Sort order (name, price_low, price_high, thc, cbd)
        limit: Maximum items to return
        skip: Items to skip (pagination)
        db: Database session

    Returns:
        List of products with prices at this dispensary
    """

    # Verify dispensary exists
    disp = db.query(Dispensary).filter(Dispensary.id == dispensary_id).first()
    if not disp:
        raise HTTPException(status_code=404, detail="Dispensary not found")

    # Build query for prices at this dispensary
    query = (
        db.query(Price)
        .options(joinedload(Price.product).joinedload(Product.brand))
        .filter(Price.dispensary_id == dispensary_id)
    )

    if in_stock_only:
        query = query.filter(Price.in_stock == True)

    prices = query.all()

    # Filter by product type if specified (case-insensitive)
    if product_type:
        normalized_type = product_type.lower()
        prices = [p for p in prices if p.product and p.product.product_type.lower() == normalized_type]

    # Build result list
    results = []
    for price in prices:
        product = price.product
        if not product:
            continue

        # Resolve to parent product for display name/brand
        display_product = product
        parent_id = str(product.id)
        if not product.is_master and product.master_product_id:
            parent = db.query(Product).filter(Product.id == product.master_product_id).first()
            if parent:
                display_product = parent
                parent_id = str(parent.id)

        results.append({
            "product_id": parent_id,
            "variant_id": str(product.id),
            "product_name": display_product.name,
            "brand": display_product.brand.name if display_product.brand else None,
            "product_type": display_product.product_type,
            "thc_percentage": display_product.thc_percentage,
            "cbd_percentage": display_product.cbd_percentage,
            "weight": product.weight,
            "weight_grams": product.weight_grams,
            "price": float(price.amount),
            "in_stock": price.in_stock,
            "last_updated": price.last_updated.isoformat() if price.last_updated else None
        })

    # Sort results
    if sort_by == "name":
        results.sort(key=lambda x: x["product_name"].lower())
    elif sort_by == "price_low":
        results.sort(key=lambda x: x["price"])
    elif sort_by == "price_high":
        results.sort(key=lambda x: x["price"], reverse=True)
    elif sort_by == "thc":
        results.sort(key=lambda x: x["thc_percentage"] or 0, reverse=True)
    elif sort_by == "cbd":
        results.sort(key=lambda x: x["cbd_percentage"] or 0, reverse=True)

    # Apply pagination
    return results[skip:skip + limit]
