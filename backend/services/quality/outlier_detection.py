"""
Price outlier detection for data quality assurance.

Identifies prices that are significantly different from state averages
using statistical analysis (z-score based detection).
"""
import statistics
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class OutlierDetector:
    """
    Detects price anomalies using statistical methods.

    Uses z-score analysis to identify prices that deviate significantly
    from the mean price for a product across all dispensaries.
    """

    # Z-score thresholds for severity classification
    MEDIUM_THRESHOLD = 2.0  # 2 standard deviations = medium severity
    HIGH_THRESHOLD = 3.0    # 3 standard deviations = high severity

    @classmethod
    def detect_price_outliers(
        cls,
        prices: List,  # List of Price model instances
        min_data_points: int = 3
    ) -> List[Dict]:
        """
        Find prices significantly different from average.

        Args:
            prices: List of Price model instances
            min_data_points: Minimum data points needed for analysis

        Returns:
            List of outlier dictionaries with details
        """
        if len(prices) < min_data_points:
            return []  # Need sufficient data for statistical analysis

        price_amounts = [p.amount for p in prices]

        try:
            mean = statistics.mean(price_amounts)
            stdev = statistics.stdev(price_amounts)
        except statistics.StatisticsError:
            return []

        if stdev == 0:
            return []  # All prices are identical

        outliers = []
        for price in prices:
            z_score = abs((price.amount - mean) / stdev)

            if z_score >= cls.MEDIUM_THRESHOLD:
                severity = "high" if z_score >= cls.HIGH_THRESHOLD else "medium"
                deviation_percent = ((price.amount - mean) / mean) * 100

                outliers.append({
                    "price_id": price.id,
                    "product_id": price.product_id,
                    "dispensary_id": price.dispensary_id,
                    "amount": price.amount,
                    "state_average": round(mean, 2),
                    "deviation_percent": round(deviation_percent, 1),
                    "z_score": round(z_score, 2),
                    "severity": severity,
                    "direction": "above" if price.amount > mean else "below"
                })

        # Sort by severity (z-score) descending
        return sorted(outliers, key=lambda x: x["z_score"], reverse=True)

    @classmethod
    def get_product_price_range(cls, db: Session, product_id: str) -> Dict:
        """
        Get price statistics for a product across dispensaries.

        Args:
            db: Database session
            product_id: Product ID to analyze

        Returns:
            Dict with min, max, avg, and other statistics
        """
        from models import Price

        prices = (
            db.query(Price)
            .filter(Price.product_id == product_id)
            .filter(Price.in_stock == True)
            .all()
        )

        if not prices:
            return {
                "product_id": product_id,
                "count": 0,
                "error": "No prices found"
            }

        amounts = [p.amount for p in prices]

        try:
            result = {
                "product_id": product_id,
                "min": min(amounts),
                "max": max(amounts),
                "avg": round(statistics.mean(amounts), 2),
                "count": len(amounts),
                "range": round(max(amounts) - min(amounts), 2)
            }

            if len(amounts) >= 2:
                result["stdev"] = round(statistics.stdev(amounts), 2)

            return result
        except statistics.StatisticsError:
            return {
                "product_id": product_id,
                "count": len(amounts),
                "error": "Insufficient data for statistics"
            }

    @classmethod
    def get_all_outliers(
        cls,
        db: Session,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get all price outliers across all products.

        Args:
            db: Database session
            limit: Maximum number of outliers to return

        Returns:
            List of outliers sorted by severity
        """
        from models import Price, Product
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

            outliers = cls.detect_price_outliers(prices)

            for outlier in outliers:
                # Add product name for display
                product = db.query(Product).filter(Product.id == product_id).first()
                if product:
                    outlier["product_name"] = product.name

            all_outliers.extend(outliers)

        # Sort all outliers by z-score and limit
        all_outliers.sort(key=lambda x: x["z_score"], reverse=True)
        return all_outliers[:limit]

    @classmethod
    def check_price_is_outlier(
        cls,
        db: Session,
        product_id: str,
        new_price: float
    ) -> Optional[Dict]:
        """
        Check if a new price would be an outlier.

        Useful for warning during scraping or manual entry.

        Args:
            db: Database session
            product_id: Product ID
            new_price: Price to check

        Returns:
            Outlier info if price is an outlier, None otherwise
        """
        from models import Price

        prices = (
            db.query(Price)
            .filter(Price.product_id == product_id)
            .filter(Price.in_stock == True)
            .all()
        )

        if len(prices) < 3:
            return None  # Not enough data

        existing_amounts = [p.amount for p in prices]

        try:
            mean = statistics.mean(existing_amounts)
            stdev = statistics.stdev(existing_amounts)
        except statistics.StatisticsError:
            return None

        if stdev == 0:
            # If all prices are same, any different price is notable
            if new_price != mean:
                return {
                    "is_outlier": True,
                    "severity": "medium",
                    "message": f"Price ${new_price} differs from uniform price ${mean}"
                }
            return None

        z_score = abs((new_price - mean) / stdev)

        if z_score >= cls.MEDIUM_THRESHOLD:
            deviation_percent = ((new_price - mean) / mean) * 100
            severity = "high" if z_score >= cls.HIGH_THRESHOLD else "medium"

            return {
                "is_outlier": True,
                "severity": severity,
                "z_score": round(z_score, 2),
                "deviation_percent": round(deviation_percent, 1),
                "state_average": round(mean, 2),
                "message": f"Price ${new_price} is {abs(deviation_percent):.1f}% {'above' if new_price > mean else 'below'} average"
            }

        return None
