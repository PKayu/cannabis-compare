---
description: Implement watch lists, stock alert detection, price drop notifications, email delivery, and user notification preferences.
auto_execution_mode: 1
---

## Context

This workflow implements the final Phase 3 feature set:
- Watch list functionality for favorite strains
- Stock availability alerts
- Price drop notifications
- Email delivery (SendGrid)
- User notification preferences
- Alert badges on product pages

## Steps

### 1. Create Watchlist Table/Model

Add to `backend/models.py`:

```python
class Watchlist(Base):
    """User's watched products for alerts"""
    __tablename__ = "watchlists"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)

    # Alert preferences
    alert_on_stock = Column(Boolean, default=True)  # Notify when back in stock
    alert_on_price_drop = Column(Boolean, default=True)  # Notify on price decrease
    price_drop_threshold = Column(Float, nullable=True)  # % threshold (e.g., 10 = 10% drop)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    product = relationship("Product")

    __table_args__ = (UniqueConstraint('user_id', 'product_id'), )


class PriceAlert(Base):
    """Log of price alerts sent to users"""
    __tablename__ = "price_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    dispensary_id = Column(String, ForeignKey("dispensaries.id"), nullable=False)

    alert_type = Column(String)  # "stock_available" or "price_drop"
    previous_price = Column(Float, nullable=True)
    new_price = Column(Float, nullable=True)
    percent_change = Column(Float, nullable=True)

    sent_at = Column(DateTime, default=datetime.utcnow)
    email_sent = Column(Boolean, default=False)

    # Relationships
    user = relationship("User")
    product = relationship("Product")
    dispensary = relationship("Dispensary")


class NotificationPreference(Base):
    """User notification settings"""
    __tablename__ = "notification_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)

    # Email preferences
    email_stock_alerts = Column(Boolean, default=True)
    email_price_drops = Column(Boolean, default=True)
    email_frequency = Column(String, default="immediately")  # "immediately" or "daily_digest"

    # In-app preferences
    app_notifications = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
```

### 2. Build Watchlist API Endpoints

Create `backend/routers/watchlist.py`:

```python
"""Watchlist endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Watchlist, NotificationPreference
from pydantic import BaseModel

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

class WatchlistAdd(BaseModel):
    product_id: str
    alert_on_stock: bool = True
    alert_on_price_drop: bool = True
    price_drop_threshold: float | None = None

@router.post("/add")
async def add_to_watchlist(
    data: WatchlistAdd,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add product to watchlist"""

    existing = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        Watchlist.product_id == data.product_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")

    watchlist_item = Watchlist(
        user_id=user_id,
        product_id=data.product_id,
        alert_on_stock=data.alert_on_stock,
        alert_on_price_drop=data.alert_on_price_drop,
        price_drop_threshold=data.price_drop_threshold
    )

    db.add(watchlist_item)
    db.commit()

    return {"status": "added"}

@router.delete("/remove/{product_id}")
async def remove_from_watchlist(
    product_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove product from watchlist"""

    item = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        Watchlist.product_id == product_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Not in watchlist")

    db.delete(item)
    db.commit()

    return {"status": "removed"}

@router.get("/")
async def get_watchlist(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's watchlist"""

    items = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()

    return [
        {
            "product_id": item.product_id,
            "product_name": item.product.name,
            "alert_on_stock": item.alert_on_stock,
            "alert_on_price_drop": item.alert_on_price_drop,
            "price_drop_threshold": item.price_drop_threshold
        }
        for item in items
    ]
```

### 3. Create Stock Alert Detection Logic

Create `backend/services/alerts/stock_detector.py`:

```python
"""Detect stock availability changes"""
from sqlalchemy.orm import Session
from backend.models import Watchlist, Price, PriceAlert
from datetime import datetime

class StockDetector:
    """Detects when watched products come back in stock"""

    @staticmethod
    async def check_stock_changes(db: Session) -> list:
        """Check all watched products for stock changes"""

        alerts = []

        # Get all watched products
        watchlist_items = db.query(Watchlist).filter(
            Watchlist.alert_on_stock == True
        ).all()

        for item in watchlist_items:
            # Check if product is in stock at any dispensary
            in_stock = db.query(Price).filter(
                Price.product_id == item.product_id,
                Price.in_stock == True
            ).first()

            if in_stock:
                # Check if we already sent alert for this stock event
                recent_alert = db.query(PriceAlert).filter(
                    PriceAlert.user_id == item.user_id,
                    PriceAlert.product_id == item.product_id,
                    PriceAlert.alert_type == "stock_available",
                    PriceAlert.sent_at > datetime.utcnow() - timedelta(hours=24)
                ).first()

                if not recent_alert:
                    # Create alert
                    alert = PriceAlert(
                        user_id=item.user_id,
                        product_id=item.product_id,
                        dispensary_id=in_stock.dispensary_id,
                        alert_type="stock_available"
                    )
                    db.add(alert)
                    alerts.append(alert)

        db.commit()
        return alerts
```

### 4. Implement Price Drop Detection

Create `backend/services/alerts/price_detector.py`:

```python
"""Detect price drops on watched products"""
from sqlalchemy.orm import Session
from backend.models import Watchlist, Price, PriceAlert
from datetime import datetime, timedelta

class PriceDetector:
    """Detects price drops on watched products"""

    @staticmethod
    async def check_price_drops(db: Session) -> list:
        """Check watched products for price decreases"""

        alerts = []

        # Get all watched products with price drop alerts enabled
        watchlist_items = db.query(Watchlist).filter(
            Watchlist.alert_on_price_drop == True
        ).all()

        for item in watchlist_items:
            # Get current prices
            current_prices = db.query(Price).filter(
                Price.product_id == item.product_id,
                Price.in_stock == True
            ).all()

            for current_price in current_prices:
                if current_price.previous_price is None:
                    continue

                # Calculate percent change
                percent_change = (
                    (current_price.amount - current_price.previous_price) /
                    current_price.previous_price * 100
                )

                # Check if drop meets threshold
                threshold = item.price_drop_threshold or 10  # Default 10%

                if percent_change < -threshold:
                    # Check if we already sent alert
                    recent_alert = db.query(PriceAlert).filter(
                        PriceAlert.user_id == item.user_id,
                        PriceAlert.product_id == item.product_id,
                        PriceAlert.dispensary_id == current_price.dispensary_id,
                        PriceAlert.alert_type == "price_drop",
                        PriceAlert.sent_at > datetime.utcnow() - timedelta(hours=24)
                    ).first()

                    if not recent_alert:
                        alert = PriceAlert(
                            user_id=item.user_id,
                            product_id=item.product_id,
                            dispensary_id=current_price.dispensary_id,
                            alert_type="price_drop",
                            previous_price=current_price.previous_price,
                            new_price=current_price.amount,
                            percent_change=percent_change
                        )
                        db.add(alert)
                        alerts.append(alert)

        db.commit()
        return alerts
```

### 5. Build Notification System (Email via SendGrid)

Create `backend/services/notifications/email_service.py`:

```python
"""Email notification service using SendGrid"""
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To
import os
from backend.models import User, Product, Price, Dispensary

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = "alerts@utahbud.com"

class EmailNotificationService:
    """Send email notifications for alerts"""

    @staticmethod
    async def send_stock_alert(user: User, product: Product, price: Price):
        """Send email when product comes back in stock"""

        subject = f"🎉 {product.name} is back in stock!"

        html_content = f"""
        <h2>{product.name} is now available!</h2>
        <p><strong>{price.dispensary.name}</strong></p>
        <p>Price: ${price.amount:.2f}</p>
        <a href="https://utahbud.com/products/{product.id}">View Product</a>
        """

        await EmailNotificationService._send_email(
            user.email,
            subject,
            html_content
        )

    @staticmethod
    async def send_price_drop_alert(
        user: User,
        product: Product,
        price: Price,
        percent_change: float
    ):
        """Send email when price drops"""

        subject = f"💰 Price drop on {product.name}"

        discount_display = abs(percent_change)
        html_content = f"""
        <h2>Price drop alert!</h2>
        <p><strong>{product.name}</strong></p>
        <p>Now <strong>${price.amount:.2f}</strong> at <strong>{price.dispensary.name}</strong></p>
        <p>Save {discount_display:.1f}%!</p>
        <a href="https://utahbud.com/products/{product.id}">View Product</a>
        """

        await EmailNotificationService._send_email(
            user.email,
            subject,
            html_content
        )

    @staticmethod
    async def _send_email(to_email: str, subject: str, html_content: str):
        """Send email via SendGrid"""

        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )

        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            await sg.send(message)
        except Exception as e:
            print(f"Failed to send email: {e}")
```

### 6. Create Watchlist UI Component

Create `frontend/components/WatchlistButton.tsx`:

```typescript
interface WatchlistButtonProps {
  productId: string
  isWatched: boolean
}

export default function WatchlistButton({ productId, isWatched }: WatchlistButtonProps) {
  const [watched, setWatched] = React.useState(isWatched)
  const [loading, setLoading] = React.useState(false)

  const handleToggle = async () => {
    setLoading(true)

    try {
      if (watched) {
        await api.delete(`/api/watchlist/remove/${productId}`)
      } else {
        await api.post('/api/watchlist/add', { product_id: productId })
      }
      setWatched(!watched)
    } catch (error) {
      console.error('Failed to toggle watchlist:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleToggle}
      disabled={loading}
      className={`flex items-center gap-2 px-4 py-2 rounded ${
        watched
          ? 'bg-cannabis-100 text-cannabis-700 border border-cannabis-300'
          : 'bg-white text-gray-700 border border-gray-300'
      }`}
    >
      {watched ? '★' : '☆'} {watched ? 'Watching' : 'Watch'}
    </button>
  )
}
```

### 7. Build Notification Preferences Page

Create `frontend/app/profile/notifications/page.tsx`:

```typescript
'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'

export default function NotificationPreferencesPage() {
  const [prefs, setPrefs] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    loadPreferences()
  }, [])

  const loadPreferences = async () => {
    try {
      const res = await api.get('/api/notifications/preferences')
      setPrefs(res.data)
    } catch (error) {
      console.error('Failed to load preferences:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      await api.put('/api/notifications/preferences', prefs)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (error) {
      console.error('Failed to save preferences:', error)
    }
  }

  if (loading) return <div>Loading...</div>

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Notification Preferences</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="mb-6">
          <h2 className="font-bold mb-4">Email Alerts</h2>

          <label className="flex items-center mb-4">
            <input
              type="checkbox"
              checked={prefs?.email_stock_alerts}
              onChange={(e) => setPrefs({ ...prefs, email_stock_alerts: e.target.checked })}
              className="mr-3"
            />
            <span>Notify when watched products come back in stock</span>
          </label>

          <label className="flex items-center mb-4">
            <input
              type="checkbox"
              checked={prefs?.email_price_drops}
              onChange={(e) => setPrefs({ ...prefs, email_price_drops: e.target.checked })}
              className="mr-3"
            />
            <span>Notify when prices drop on watched products</span>
          </label>

          <div className="mb-4">
            <label className="block font-semibold mb-2">Email Frequency</label>
            <select
              value={prefs?.email_frequency}
              onChange={(e) => setPrefs({ ...prefs, email_frequency: e.target.value })}
              className="px-3 py-2 border rounded"
            >
              <option value="immediately">Immediately</option>
              <option value="daily_digest">Daily Digest</option>
            </select>
          </div>
        </div>

        <div>
          <h2 className="font-bold mb-4">In-App Notifications</h2>

          <label className="flex items-center">
            <input
              type="checkbox"
              checked={prefs?.app_notifications}
              onChange={(e) => setPrefs({ ...prefs, app_notifications: e.target.checked })}
              className="mr-3"
            />
            <span>Enable push notifications</span>
          </label>
        </div>

        <button
          onClick={handleSave}
          className="mt-8 px-4 py-2 bg-cannabis-600 text-white rounded hover:bg-cannabis-700"
        >
          Save Preferences
        </button>

        {saved && <p className="mt-4 text-green-600">Preferences saved!</p>}
      </div>
    </div>
  )
}
```

### 8. Add Stock Alert Badges on Product Pages

Update `frontend/app/products/[id]/page.tsx` to show watchlist badge and alert status.

### 9. Test Notification Delivery

Test scenarios:
1. Add product to watchlist
2. Trigger stock availability (simulate via database)
3. Trigger price drop (simulate via database)
4. Verify email received
5. Update notification preferences
6. Verify email frequency respected

Create test script `backend/tests/test_alerts.py`:

```python
import pytest
from backend.services.alerts.stock_detector import StockDetector
from backend.services.alerts.price_detector import PriceDetector

@pytest.mark.asyncio
async def test_stock_alert_detection(db):
    """Test stock alert creation"""
    alerts = await StockDetector.check_stock_changes(db)
    assert len(alerts) > 0

@pytest.mark.asyncio
async def test_price_drop_detection(db):
    """Test price drop alert creation"""
    alerts = await PriceDetector.check_price_drops(db)
    assert len(alerts) > 0
```

### 10. Create Scheduled Alert Job

Add to `backend/services/scheduler.py`:

```python
from apscheduler.schedulers.background import BackgroundScheduler
from backend.services.alerts.stock_detector import StockDetector
from backend.services.alerts.price_detector import PriceDetector

async def run_alert_checks(db):
    """Check for new alerts"""
    stock_alerts = await StockDetector.check_stock_changes(db)
    price_alerts = await PriceDetector.check_price_drops(db)
    return len(stock_alerts) + len(price_alerts)

scheduler = BackgroundScheduler()
scheduler.add_job(
    run_alert_checks,
    'interval',
    minutes=15,  # Check every 15 minutes
    id='alert_check',
    name='Alert Detection Job'
)
```

## Success Criteria

- [ ] Watchlist table created with user preferences
- [ ] Add/remove from watchlist endpoints functional
- [ ] Stock detection algorithm working
- [ ] Price drop detection algorithm working
- [ ] SendGrid email integration configured
- [ ] Stock alert emails sending
- [ ] Price drop alert emails sending
- [ ] Watchlist UI component functional
- [ ] Notification preferences page working
- [ ] User can customize alert thresholds
- [ ] Email frequency preferences respected
- [ ] Stock alerts on product pages displayed
- [ ] Scheduled alert job running every 15 minutes
- [ ] Tests passing for alert detection
- [ ] No TypeScript errors

## End-to-End Verification

After completing all 10 workflows:

1. **User Journey**: New user → age gate → search → product → review → watchlist → alert
2. **Admin Journey**: Login → cleanup queue → approve flags → view analytics
3. **Performance**: <200ms search, <2 hour data freshness
4. **Data Quality**: >80% auto-merge rate for scraped products
5. **Compliance**: Age gate + disclaimers on every page
6. **Mobile**: 80%+ responsive design score

All 10 workflows complete! 🎉
