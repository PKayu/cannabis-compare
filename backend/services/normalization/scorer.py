"""
Confidence scoring and product normalization service.

Handles the decision logic for scraped products:
- >90% confidence: Auto-merge to existing product
- 60-90% confidence: Create ScraperFlag for admin review
- <60% confidence: Create new product entry
"""
from sqlalchemy.orm import Session
from typing import Optional, Tuple
import logging

from services.normalization.matcher import ProductMatcher
from services.scrapers.base_scraper import ScrapedProduct

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Manages confidence-based product matching and normalization"""

    @staticmethod
    def process_scraped_product(
        db: Session,
        scraped_product: ScrapedProduct,
        dispensary_id: str
    ) -> Tuple[Optional[str], str]:
        """
        Process a scraped product and determine how to handle it.

        Args:
            db: Database session
            scraped_product: Product data from scraper
            dispensary_id: ID of the dispensary being scraped

        Returns:
            Tuple of (product_id, action_taken)
            - product_id: ID of matched/created product, None if flagged
            - action_taken: "auto_merge" | "flagged_review" | "new_product"
        """
        # Import models here to avoid circular imports
        from models import Product, Brand, ScraperFlag

        # Find all master products to compare against
        master_products = (
            db.query(Product)
            .filter(Product.is_master == True)
            .all()
        )

        # Build candidate list for matching
        candidates = []
        for master in master_products:
            candidates.append({
                "id": master.id,
                "name": master.name,
                "brand": master.brand.name if master.brand else "",
                "thc_percentage": master.thc_percentage
            })

        # Find best match
        best_match, confidence, match_type = ProductMatcher.find_best_match(
            scraped_name=scraped_product.name,
            scraped_brand=scraped_product.brand,
            candidates=candidates,
            scraped_thc=scraped_product.thc_percentage
        )

        if match_type == "auto_merge" and best_match:
            # AUTO-MERGE: Link directly to existing product
            logger.info(
                f"Auto-merging '{scraped_product.name}' to '{best_match['name']}' "
                f"(confidence: {confidence:.0%})"
            )
            return best_match["id"], "auto_merge"

        elif match_type == "flagged_review":
            # FLAGGED FOR REVIEW: Create ScraperFlag for admin approval
            logger.info(
                f"Flagging '{scraped_product.name}' for review "
                f"(confidence: {confidence:.0%})"
            )

            flag = ScraperFlag(
                original_name=scraped_product.name,
                original_thc=scraped_product.thc_percentage,
                original_cbd=scraped_product.cbd_percentage,
                brand_name=scraped_product.brand,
                dispensary_id=dispensary_id,
                matched_product_id=best_match["id"] if best_match else None,
                confidence_score=confidence,
                status="pending",
                merge_reason=f"Confidence {confidence:.0%} requires manual review"
            )
            db.add(flag)
            db.commit()
            return None, "flagged_review"

        else:
            # NEW PRODUCT: Create master product entry
            logger.info(
                f"Creating new product for '{scraped_product.name}' "
                f"(confidence: {confidence:.0%})"
            )

            # Get or create brand
            brand_id = ConfidenceScorer._get_or_create_brand(
                db, scraped_product.brand
            )

            new_product = Product(
                name=scraped_product.name,
                product_type=scraped_product.category,
                brand_id=brand_id,
                thc_percentage=scraped_product.thc_percentage,
                cbd_percentage=scraped_product.cbd_percentage,
                is_master=True,
                normalization_confidence=1.0
            )
            db.add(new_product)
            db.commit()
            db.refresh(new_product)

            return new_product.id, "new_product"

    @staticmethod
    def _get_or_create_brand(db: Session, brand_name: str) -> str:
        """
        Get existing brand or create new one.

        Args:
            db: Database session
            brand_name: Name of the brand

        Returns:
            Brand ID
        """
        from models import Brand

        # Try to find existing brand (case-insensitive)
        brand = (
            db.query(Brand)
            .filter(Brand.name.ilike(brand_name))
            .first()
        )

        if not brand:
            # Create new brand
            brand = Brand(name=brand_name)
            db.add(brand)
            db.commit()
            db.refresh(brand)
            logger.info(f"Created new brand: {brand_name}")

        return brand.id

    @staticmethod
    def update_or_create_price(
        db: Session,
        product_id: str,
        dispensary_id: str,
        price: float,
        in_stock: bool = True
    ) -> str:
        """
        Update existing price or create new price entry.

        Args:
            db: Database session
            product_id: Product ID
            dispensary_id: Dispensary ID
            price: New price amount
            in_stock: Stock status

        Returns:
            Price ID
        """
        from models import Price

        # Check for existing price entry
        existing_price = (
            db.query(Price)
            .filter(
                Price.product_id == product_id,
                Price.dispensary_id == dispensary_id
            )
            .first()
        )

        if existing_price:
            # Update existing price with history tracking
            existing_price.update_price(price)
            existing_price.in_stock = in_stock
            db.commit()
            return existing_price.id
        else:
            # Create new price entry
            new_price = Price(
                product_id=product_id,
                dispensary_id=dispensary_id,
                amount=price,
                in_stock=in_stock
            )
            db.add(new_price)
            db.commit()
            db.refresh(new_price)
            return new_price.id

    @staticmethod
    def get_normalization_stats(db: Session) -> dict:
        """
        Get statistics about product normalization.

        Returns:
            Dict with counts for auto-merged, flagged, and new products
        """
        from models import ScraperFlag, Product
        from sqlalchemy import func

        total_flags = db.query(ScraperFlag).count()
        pending_flags = (
            db.query(ScraperFlag)
            .filter(ScraperFlag.status == "pending")
            .count()
        )
        approved_flags = (
            db.query(ScraperFlag)
            .filter(ScraperFlag.status == "approved")
            .count()
        )
        rejected_flags = (
            db.query(ScraperFlag)
            .filter(ScraperFlag.status == "rejected")
            .count()
        )

        master_products = (
            db.query(Product)
            .filter(Product.is_master == True)
            .count()
        )

        # Calculate auto-merge rate (if we have data)
        # This is simplified - in production would track this separately
        total_processed = total_flags + master_products
        auto_merge_rate = (
            (master_products - rejected_flags) / total_processed * 100
            if total_processed > 0 else 0
        )

        return {
            "total_flags": total_flags,
            "pending_review": pending_flags,
            "approved": approved_flags,
            "rejected": rejected_flags,
            "master_products": master_products,
            "estimated_auto_merge_rate": f"{auto_merge_rate:.1f}%"
        }
