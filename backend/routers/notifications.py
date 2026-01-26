"""Notification preference endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import NotificationPreference
from routers.auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationPreferenceUpdate(BaseModel):
    email_stock_alerts: Optional[bool] = None
    email_price_drops: Optional[bool] = None
    email_frequency: Optional[str] = None  # "immediately", "daily", "weekly"
    app_notifications: Optional[bool] = None


class NotificationPreferenceResponse(BaseModel):
    user_id: str
    email_stock_alerts: bool
    email_price_drops: bool
    email_frequency: str
    app_notifications: bool
    created_at: str
    updated_at: str


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's notification preferences (creates default if not exists)"""

    prefs = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id
    ).first()

    # Create default preferences if they don't exist
    if not prefs:
        prefs = NotificationPreference(
            user_id=user_id,
            email_stock_alerts=True,
            email_price_drops=True,
            email_frequency="immediately",
            app_notifications=True
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    return NotificationPreferenceResponse(
        user_id=prefs.user_id,
        email_stock_alerts=prefs.email_stock_alerts,
        email_price_drops=prefs.email_price_drops,
        email_frequency=prefs.email_frequency,
        app_notifications=prefs.app_notifications,
        created_at=prefs.created_at.isoformat() if prefs.created_at else "",
        updated_at=prefs.updated_at.isoformat() if prefs.updated_at else ""
    )


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    data: NotificationPreferenceUpdate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's notification preferences"""

    # Validate email frequency
    if data.email_frequency and data.email_frequency not in ["immediately", "daily", "weekly"]:
        raise HTTPException(
            status_code=400,
            detail="email_frequency must be 'immediately', 'daily', or 'weekly'"
        )

    prefs = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id
    ).first()

    # Create if doesn't exist
    if not prefs:
        prefs = NotificationPreference(
            user_id=user_id,
            email_stock_alerts=data.email_stock_alerts if data.email_stock_alerts is not None else True,
            email_price_drops=data.email_price_drops if data.email_price_drops is not None else True,
            email_frequency=data.email_frequency or "immediately",
            app_notifications=data.app_notifications if data.app_notifications is not None else True
        )
        db.add(prefs)
    else:
        # Update only provided fields
        if data.email_stock_alerts is not None:
            prefs.email_stock_alerts = data.email_stock_alerts
        if data.email_price_drops is not None:
            prefs.email_price_drops = data.email_price_drops
        if data.email_frequency is not None:
            prefs.email_frequency = data.email_frequency
        if data.app_notifications is not None:
            prefs.app_notifications = data.app_notifications

    db.commit()
    db.refresh(prefs)

    return NotificationPreferenceResponse(
        user_id=prefs.user_id,
        email_stock_alerts=prefs.email_stock_alerts,
        email_price_drops=prefs.email_price_drops,
        email_frequency=prefs.email_frequency,
        app_notifications=prefs.app_notifications,
        created_at=prefs.created_at.isoformat() if prefs.created_at else "",
        updated_at=prefs.updated_at.isoformat() if prefs.updated_at else ""
    )
