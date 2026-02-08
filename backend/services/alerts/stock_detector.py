"""Detect stock availability changes for watched products"""
from sqlalchemy.orm import Session
from models import Watchlist, Price, PriceAlert, Product
from datetime import datetime, timedelta
from typing import List


class StockDetector:
    """Detects when watched products come back in stock"""

    @staticmethod
    def check_stock_changes(db: Session) -> List[PriceAlert]:
        """
        Check all watched products for stock changes

        Returns:
            List of new PriceAlert records created
        """
        alerts = []

        # Get all watched products with stock alerts enabled
        watchlist_items = db.query(Watchlist).filter(
            Watchlist.alert_on_stock == True
        ).all()

        for item in watchlist_items:
            # Watchlist tracks parent products; prices are on variants
            variant_ids = [
                v.id for v in
                db.query(Product.id).filter(
                    Product.master_product_id == item.product_id
                ).all()
            ]
            price_product_ids = variant_ids if variant_ids else [item.product_id]

            # Check if product is in stock at any dispensary
            in_stock_prices = db.query(Price).filter(
                Price.product_id.in_(price_product_ids),
                Price.in_stock == True
            ).all()

            # For each dispensary that has it in stock
            for price in in_stock_prices:
                # Check if we already sent an alert for this stock event (24-hour deduplication)
                recent_alert = db.query(PriceAlert).filter(
                    PriceAlert.user_id == item.user_id,
                    PriceAlert.product_id == item.product_id,
                    PriceAlert.dispensary_id == price.dispensary_id,
                    PriceAlert.alert_type == "stock_available",
                    PriceAlert.sent_at > datetime.utcnow() - timedelta(hours=24)
                ).first()

                if not recent_alert:
                    # Create new alert
                    alert = PriceAlert(
                        user_id=item.user_id,
                        product_id=item.product_id,
                        dispensary_id=price.dispensary_id,
                        alert_type="stock_available",
                        new_price=price.amount,
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
