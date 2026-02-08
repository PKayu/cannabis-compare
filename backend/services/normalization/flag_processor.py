"""
Process and resolve ScraperFlags created by the scraper.

Provides admin functionality to:
- Approve merges (link flagged product to matched master)
- Reject merges (create new master product from flagged data)
- Dismiss bad imports (no product created)
- View and filter pending flags
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def _build_corrections(flag, overrides: Dict) -> Optional[Dict]:
    """Compare override values to flag's original data, return diff or None."""
    field_map = {
        "name": "original_name",
        "brand_name": "brand_name",
        "product_type": "original_category",
        "thc_percentage": "original_thc",
        "cbd_percentage": "original_cbd",
        "weight": "original_weight",
        "price": "original_price",
    }
    corrections = {}
    for override_key, flag_attr in field_map.items():
        override_val = overrides.get(override_key)
        if override_val is not None:
            original_val = getattr(flag, flag_attr, None)
            # Normalize for comparison (both to str)
            if str(override_val) != str(original_val):
                corrections[override_key] = {
                    "from": original_val,
                    "to": override_val
                }
    return corrections if corrections else None


class ScraperFlagProcessor:
    """Handles admin approval/rejection/dismissal of flagged products"""

    @staticmethod
    def approve_flag(
        db: Session,
        flag_id: str,
        admin_id: str,
        notes: str = "",
        # Editable field overrides
        name: Optional[str] = None,
        brand_name: Optional[str] = None,
        product_type: Optional[str] = None,
        thc_percentage: Optional[float] = None,
        cbd_percentage: Optional[float] = None,
        weight: Optional[str] = None,
        price: Optional[float] = None,
    ) -> str:
        """
        Approve merge of flagged product to matched product.

        Creates a variant under the matched parent product with the
        original weight/price data stored on the flag. Optional override
        params allow the admin to correct fields before saving.

        Parent-level overrides (name, brand_name, product_type) update the
        matched parent product in-place. Variant-level overrides
        (thc_percentage, cbd_percentage, weight, price) apply to the new variant.

        Returns:
            ID of the created/found variant product
        """
        from models import ScraperFlag, Product, Brand
        from services.normalization.scorer import find_or_create_variant, ConfidenceScorer
        from services.scrapers.base_scraper import ScrapedProduct

        flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()

        if not flag:
            raise ValueError(f"ScraperFlag not found: {flag_id}")

        if not flag.matched_product_id:
            raise ValueError(
                f"Cannot approve flag without matched product: {flag_id}"
            )

        if flag.status != "pending":
            raise ValueError(
                f"Flag already resolved with status: {flag.status}"
            )

        # Track corrections for analytics
        overrides = {
            "name": name, "brand_name": brand_name, "product_type": product_type,
            "thc_percentage": thc_percentage, "cbd_percentage": cbd_percentage,
            "weight": weight, "price": price,
        }
        corrections = _build_corrections(flag, overrides)
        if corrections:
            flag.corrections = corrections

        # Load matched parent and apply parent-level overrides
        parent = db.query(Product).filter(
            Product.id == flag.matched_product_id
        ).first()

        if parent:
            if name is not None and name != parent.name:
                parent.name = name
            if product_type is not None and product_type != parent.product_type:
                parent.product_type = product_type
            if brand_name is not None:
                existing_brand = parent.brand
                if not existing_brand or existing_brand.name.lower() != brand_name.lower():
                    brand = (
                        db.query(Brand)
                        .filter(Brand.name.ilike(brand_name))
                        .first()
                    )
                    if not brand:
                        brand = Brand(name=brand_name)
                        db.add(brand)
                        db.flush()
                    parent.brand_id = brand.id

        # Resolve final values (override or flag original)
        final_thc = thc_percentage if thc_percentage is not None else flag.original_thc
        final_cbd = cbd_percentage if cbd_percentage is not None else flag.original_cbd
        final_weight = weight if weight is not None else flag.original_weight
        final_price = price if price is not None else flag.original_price

        # Build ScrapedProduct from resolved values
        scraped = ScrapedProduct(
            name=flag.original_name,
            brand=flag.brand_name,
            category=flag.original_category or "Unknown",
            price=final_price or 0.0,
            thc_percentage=final_thc,
            cbd_percentage=final_cbd,
            weight=final_weight
        )

        # Create/find variant under the matched parent
        variant = find_or_create_variant(
            db, flag.matched_product_id, final_weight, scraped
        )

        # Create price record if we have price data
        if final_price and final_price > 0:
            ConfidenceScorer.update_or_create_price(
                db, variant.id, flag.dispensary_id, final_price
            )

        # Update flag status
        flag.status = "approved"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes

        db.commit()

        logger.info(
            f"Approved merge for '{flag.original_name}' to product "
            f"{flag.matched_product_id} (variant {variant.id}) by admin {admin_id}"
            f"{' with corrections' if corrections else ''}"
        )

        return variant.id

    @staticmethod
    def reject_flag(
        db: Session,
        flag_id: str,
        admin_id: str,
        notes: str = "",
        # Editable field overrides
        name: Optional[str] = None,
        brand_name: Optional[str] = None,
        product_type: Optional[str] = None,
        thc_percentage: Optional[float] = None,
        cbd_percentage: Optional[float] = None,
        weight: Optional[str] = None,
        price: Optional[float] = None,
    ) -> str:
        """
        Reject merge and create new parent + variant from flagged entry.

        Optional override params allow the admin to correct fields before
        the new product is created.

        Returns:
            ID of the newly created parent product
        """
        from models import ScraperFlag, Product, Brand
        from services.normalization.scorer import find_or_create_variant, ConfidenceScorer
        from services.scrapers.base_scraper import ScrapedProduct

        flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()

        if not flag:
            raise ValueError(f"ScraperFlag not found: {flag_id}")

        if flag.status != "pending":
            raise ValueError(
                f"Flag already resolved with status: {flag.status}"
            )

        # Track corrections for analytics
        overrides = {
            "name": name, "brand_name": brand_name, "product_type": product_type,
            "thc_percentage": thc_percentage, "cbd_percentage": cbd_percentage,
            "weight": weight, "price": price,
        }
        corrections = _build_corrections(flag, overrides)
        if corrections:
            flag.corrections = corrections

        # Resolve final values (override or flag original)
        final_name = name if name is not None else flag.original_name
        final_brand_name = brand_name if brand_name is not None else flag.brand_name
        final_thc = thc_percentage if thc_percentage is not None else flag.original_thc
        final_cbd = cbd_percentage if cbd_percentage is not None else flag.original_cbd
        final_weight = weight if weight is not None else flag.original_weight
        final_price = price if price is not None else flag.original_price

        # Get or create brand
        brand = (
            db.query(Brand)
            .filter(Brand.name.ilike(final_brand_name))
            .first()
        )

        if not brand:
            brand = Brand(name=final_brand_name)
            db.add(brand)
            db.flush()

        # Resolve product type
        resolved_type = "Unknown"
        if product_type is not None and product_type != "Unknown":
            resolved_type = product_type
        elif flag.original_category:
            resolved_type = flag.original_category

        # Create new parent product (is_master=True, no weight)
        parent = Product(
            name=final_name,
            product_type=resolved_type,
            brand_id=brand.id,
            thc_percentage=final_thc,
            cbd_percentage=final_cbd,
            is_master=True,
            normalization_confidence=1.0  # Admin-verified
        )
        db.add(parent)
        db.flush()

        # Create variant with weight
        scraped = ScrapedProduct(
            name=final_name,
            brand=final_brand_name,
            category=resolved_type,
            price=final_price or 0.0,
            thc_percentage=final_thc,
            cbd_percentage=final_cbd,
            weight=final_weight
        )
        variant = find_or_create_variant(
            db, parent.id, final_weight, scraped
        )

        # Create price record if we have price data
        if final_price and final_price > 0:
            ConfidenceScorer.update_or_create_price(
                db, variant.id, flag.dispensary_id, final_price
            )

        # Update flag status
        flag.status = "rejected"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes

        db.commit()

        logger.info(
            f"Rejected merge for '{flag.original_name}', created new product "
            f"{parent.id} (variant {variant.id}) by admin {admin_id}"
            f"{' with corrections' if corrections else ''}"
        )

        return parent.id

    @staticmethod
    def dismiss_flag(
        db: Session,
        flag_id: str,
        admin_id: str,
        notes: str = ""
    ) -> None:
        """
        Dismiss a flagged product without creating any product.

        The flag is kept with status='dismissed' for audit/analytics
        (helps identify scraper patterns that produce bad data).
        """
        from models import ScraperFlag

        flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()

        if not flag:
            raise ValueError(f"ScraperFlag not found: {flag_id}")

        if flag.status != "pending":
            raise ValueError(
                f"Flag already resolved with status: {flag.status}"
            )

        flag.status = "dismissed"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes

        db.commit()

        logger.info(
            f"Dismissed flag '{flag.original_name}' by admin {admin_id}"
        )

    @staticmethod
    def get_pending_flags(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        dispensary_id: Optional[str] = None
    ) -> List[dict]:
        """
        Get flags pending admin review.

        Args:
            db: Database session
            limit: Maximum number of flags to return
            offset: Number of flags to skip
            dispensary_id: Optional filter by dispensary

        Returns:
            List of flag dictionaries with related data
        """
        from models import ScraperFlag, Product, Dispensary

        query = (
            db.query(ScraperFlag)
            .filter(ScraperFlag.status == "pending")
        )

        if dispensary_id:
            query = query.filter(ScraperFlag.dispensary_id == dispensary_id)

        flags = (
            query
            .order_by(ScraperFlag.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        results = []
        for flag in flags:
            # Get dispensary name
            dispensary = (
                db.query(Dispensary)
                .filter(Dispensary.id == flag.dispensary_id)
                .first()
            )

            # Get matched product if exists
            matched_product = None
            if flag.matched_product_id:
                product = (
                    db.query(Product)
                    .filter(Product.id == flag.matched_product_id)
                    .first()
                )
                if product:
                    matched_product = {
                        "id": product.id,
                        "name": product.name,
                        "product_type": product.product_type,
                        "brand": product.brand.name if product.brand else None,
                        "brand_id": product.brand_id,
                        "thc_percentage": product.thc_percentage,
                        "cbd_percentage": product.cbd_percentage,
                    }

            results.append({
                "id": flag.id,
                "original_name": flag.original_name,
                "original_thc": flag.original_thc,
                "original_cbd": flag.original_cbd,
                "original_weight": flag.original_weight,
                "original_price": flag.original_price,
                "original_category": flag.original_category,
                "brand_name": flag.brand_name,
                "dispensary_id": flag.dispensary_id,
                "dispensary_name": dispensary.name if dispensary else None,
                "confidence_score": flag.confidence_score,
                "confidence_percent": f"{flag.confidence_score:.0%}",
                "matched_product": matched_product,
                "merge_reason": flag.merge_reason,
                "created_at": flag.created_at.isoformat()
            })

        return results

    @staticmethod
    def get_flag_count(
        db: Session,
        status: str = "pending"
    ) -> int:
        """Get count of flags by status"""
        from models import ScraperFlag

        return (
            db.query(ScraperFlag)
            .filter(ScraperFlag.status == status)
            .count()
        )

    @staticmethod
    def bulk_approve(
        db: Session,
        flag_ids: List[str],
        admin_id: str,
        notes: str = "Bulk approved"
    ) -> dict:
        """
        Approve multiple flags at once.

        Args:
            db: Database session
            flag_ids: List of flag IDs to approve
            admin_id: ID of the admin user
            notes: Notes to apply to all flags

        Returns:
            Dict with success count and errors
        """
        results = {"approved": 0, "errors": []}

        for flag_id in flag_ids:
            try:
                ScraperFlagProcessor.approve_flag(db, flag_id, admin_id, notes)
                results["approved"] += 1
            except ValueError as e:
                results["errors"].append({"flag_id": flag_id, "error": str(e)})

        return results

    @staticmethod
    def get_recent_resolutions(
        db: Session,
        limit: int = 20
    ) -> List[dict]:
        """Get recently resolved flags for audit trail"""
        from models import ScraperFlag

        flags = (
            db.query(ScraperFlag)
            .filter(ScraperFlag.status.in_(["approved", "rejected", "dismissed"]))
            .order_by(ScraperFlag.resolved_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": f.id,
                "original_name": f.original_name,
                "status": f.status,
                "resolved_by": f.resolved_by,
                "resolved_at": f.resolved_at.isoformat() if f.resolved_at else None,
                "admin_notes": f.admin_notes
            }
            for f in flags
        ]
