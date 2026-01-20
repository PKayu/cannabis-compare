"""Detect price outliers for data quality"""
import statistics
from typing import List, Dict
from models import Price

class OutlierDetector:
    """Detects price anomalies"""

    STDDEV_THRESHOLD = 2.0  # 2 standard deviations = outlier

    @staticmethod
    def detect_price_outliers(prices: List[Price]) -> List[Dict]:
        """Find prices significantly different from state average"""
        if len(prices) < 3:
            return []  # Need at least 3 data points

        price_amounts = [p.amount for p in prices]
        mean = statistics.mean(price_amounts)
        stdev = statistics.stdev(price_amounts)

        outliers = []
        for price in prices:
            z_score = abs((price.amount - mean) / stdev) if stdev > 0 else 0

            if z_score > OutlierDetector.STDDEV_THRESHOLD:
                outliers.append({
                    "price_id": price.id,
                    "dispensary_id": price.dispensary_id,
                    "amount": price.amount,
                    "state_average": mean,
                    "deviation_percent": ((price.amount - mean) / mean) * 100,
                    "z_score": z_score,
                    "severity": "high" if z_score > 3 else "medium"
                })

        return sorted(outliers, key=lambda x: x["z_score"], reverse=True)

    @staticmethod
    def get_product_price_range(db, product_id: str) -> Dict:
        """Get min/max/avg prices for a product across dispensaries"""
        prices = db.query(Price).filter(Price.product_id == product_id).all()

        if not prices:
            return {}

        amounts = [p.amount for p in prices]
        return {
            "min": min(amounts),
            "max": max(amounts),
            "avg": statistics.mean(amounts),
            "count": len(amounts),
            "range": max(amounts) - min(amounts)
        }

    @staticmethod
    def get_all_outliers(db, limit: int = 50) -> List[Dict]:
        """Get all price outliers across all products."""
        from models import Product
        from sqlalchemy import func

        # Get products with multiple prices (needed for outlier detection)
        product_counts = (
            db.query(Price.product_id, func.count(Price.id).label('count'))
            .filter(Price.in_stock == True)
            .group_by(Price.product_id)
            .having(func.count(Price.id) >= 3)
            .all()
        )

        all_outliers = []

        for product_id, _ in product_counts:
            prices = (
                db.query(Price)
                .filter(Price.product_id == product_id)
                .filter(Price.in_stock == True)
                .all()
            )

            outliers = OutlierDetector.detect_price_outliers(prices)

            for outlier in outliers:
                # Add product name for display
                product = db.query(Product).filter(Product.id == product_id).first()
                if product:
                    outlier["product_name"] = product.name

            all_outliers.extend(outliers)

        # Sort all outliers by z-score and limit
        all_outliers.sort(key=lambda x: x["z_score"], reverse=True)
        return all_outliers[:limit]