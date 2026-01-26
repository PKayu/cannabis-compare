"""Detect price drops on watched products"""
from sqlalchemy.orm import Session
from models import Watchlist, Price, PriceAlert
from datetime import datetime, timedelta
from typing import List


class PriceDetector:
    """Detects price drops on watched products"""

    @staticmethod
    def check_price_drops(db: Session) -> List[PriceAlert]:
        """
        Check watched products for price decreases

        Returns:
            List of new PriceAlert records created
        """
        alerts = []

        # Get all watched products with price drop alerts enabled
        watchlist_items = db.query(Watchlist).filter(
            Watchlist.alert_on_price_drop == True
        ).all()

        for item in watchlist_items:
            # Get current prices for this product
            current_prices = db.query(Price).filter(
                Price.product_id == item.product_id,
                Price.in_stock == True
            ).all()

            for current_price in current_prices:
                # Skip if no previous price to compare
                if current_price.previous_price is None:
                    continue

                # Calculate percent change
                percent_change = (
                    (current_price.amount - current_price.previous_price) /
                    current_price.previous_price * 100
                )

                # Get user's threshold (or default 10%)
                threshold = item.price_drop_threshold if item.price_drop_threshold else 10.0

                # Check if drop meets threshold (negative percentage = price drop)
                if percent_change < -threshold:
                    # Check if we already sent alert (24-hour deduplication)
                    recent_alert = db.query(PriceAlert).filter(
                        PriceAlert.user_id == item.user_id,
                        PriceAlert.product_id == item.product_id,
                        PriceAlert.dispensary_id == current_price.dispensary_id,
                        PriceAlert.alert_type == "price_drop",
                        PriceAlert.sent_at > datetime.utcnow() - timedelta(hours=24)
                    ).first()

                    if not recent_alert:
                        # Create new alert
                        alert = PriceAlert(
                            user_id=item.user_id,
                            product_id=item.product_id,
                            dispensary_id=current_price.dispensary_id,
                            alert_type="price_drop",
                            previous_price=current_price.previous_price,
                            new_price=current_price.amount,
                            percent_change=percent_change,
                            email_sent=False
                        )
                        db.add(alert)
                        alerts.append(alert)

        # Commit all new alerts
        if alerts:
            db.commit()
            # Refresh to get IDs
            for alert in alerts:
                db.refresh(alert)

        return alerts
