"""Watchlist endpoints for managing user's watched products"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Watchlist, Product, Price, User
from routers.auth import get_current_user

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


class WatchlistAdd(BaseModel):
    product_id: str
    alert_on_stock: bool = True
    alert_on_price_drop: bool = True
    price_drop_threshold: Optional[float] = 10.0


class WatchlistResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    product_type: str
    alert_on_stock: bool
    alert_on_price_drop: bool
    price_drop_threshold: Optional[float]
    created_at: str


@router.post("/add")
async def add_to_watchlist(
    data: WatchlistAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add product to user's watchlist with alert preferences"""

    # Verify product exists
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if already in watchlist
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.product_id == data.product_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Product already in watchlist")

    # Create watchlist item
    watchlist_item = Watchlist(
        user_id=current_user.id,
        product_id=data.product_id,
        alert_on_stock=data.alert_on_stock,
        alert_on_price_drop=data.alert_on_price_drop,
        price_drop_threshold=data.price_drop_threshold
    )

    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)

    return {
        "status": "added",
        "watchlist_id": watchlist_item.id,
        "product_id": watchlist_item.product_id
    }


@router.delete("/remove/{product_id}")
async def remove_from_watchlist(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove product from user's watchlist"""

    item = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.product_id == product_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Product not in watchlist")

    db.delete(item)
    db.commit()

    return {"status": "removed", "product_id": product_id}


@router.get("/", response_model=list[WatchlistResponse])
async def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's full watchlist with product details"""

    items = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()

    return [
        WatchlistResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name,
            product_type=item.product.product_type,
            alert_on_stock=item.alert_on_stock,
            alert_on_price_drop=item.alert_on_price_drop,
            price_drop_threshold=item.price_drop_threshold,
            created_at=item.created_at.isoformat() if item.created_at else ""
        )
        for item in items
    ]


@router.get("/check/{product_id}")
async def check_watchlist(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a specific product is in user's watchlist"""

    item = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.product_id == product_id
    ).first()

    return {
        "is_watched": item is not None,
        "watchlist_id": item.id if item else None,
        "alert_settings": {
            "alert_on_stock": item.alert_on_stock if item else None,
            "alert_on_price_drop": item.alert_on_price_drop if item else None,
            "price_drop_threshold": item.price_drop_threshold if item else None
        } if item else None
    }
