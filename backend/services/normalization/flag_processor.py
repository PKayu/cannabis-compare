"""
Process and resolve ScraperFlags created by the scraper.

Provides admin functionality to:
- Approve merges (link flagged product to matched master)
- Reject merges (create new master product from flagged data)
- View and filter pending flags
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class ScraperFlagProcessor:
    """Handles admin approval/rejection of flagged products"""

    @staticmethod
    def approve_flag(
        db: Session,
        flag_id: str,
        admin_id: str,
        notes: str = ""
    ) -> str:
        """
        Approve merge of flagged product to matched product.

        Args:
            db: Database session
            flag_id: ID of the ScraperFlag
            admin_id: ID of the admin user approving
            notes: Optional admin notes

        Returns:
            ID of the matched product

        Raises:
            ValueError: If flag not found or no matched product
        """
        from models import ScraperFlag

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

        # Update flag status
        flag.status = "approved"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes

        db.commit()

        logger.info(
            f"Approved merge for '{flag.original_name}' to product "
            f"{flag.matched_product_id} by admin {admin_id}"
        )

        return flag.matched_product_id

    @staticmethod
    def reject_flag(
        db: Session,
        flag_id: str,
        admin_id: str,
        product_type: str = "Unknown",
        notes: str = ""
    ) -> str:
        """
        Reject merge and create new product from flagged entry.

        Args:
            db: Database session
            flag_id: ID of the ScraperFlag
            admin_id: ID of the admin user rejecting
            product_type: Product type for the new product
            notes: Optional admin notes

        Returns:
            ID of the newly created product

        Raises:
            ValueError: If flag not found
        """
        from models import ScraperFlag, Product, Brand

        flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()

        if not flag:
            raise ValueError(f"ScraperFlag not found: {flag_id}")

        if flag.status != "pending":
            raise ValueError(
                f"Flag already resolved with status: {flag.status}"
            )

        # Get or create brand
        brand = (
            db.query(Brand)
            .filter(Brand.name.ilike(flag.brand_name))
            .first()
        )

        if not brand:
            brand = Brand(name=flag.brand_name)
            db.add(brand)
            db.commit()
            db.refresh(brand)

        # Create new master product from flag data
        new_product = Product(
            name=flag.original_name,
            product_type=product_type,
            brand_id=brand.id,
            thc_percentage=flag.original_thc,
            cbd_percentage=flag.original_cbd,
            is_master=True,
            normalization_confidence=1.0  # Admin-verified
        )
        db.add(new_product)

        # Update flag status
        flag.status = "rejected"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes

        db.commit()
        db.refresh(new_product)

        logger.info(
            f"Rejected merge for '{flag.original_name}', created new product "
            f"{new_product.id} by admin {admin_id}"
        )

        return new_product.id

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
                        "thc_percentage": product.thc_percentage,
                        "cbd_percentage": product.cbd_percentage
                    }

            results.append({
                "id": flag.id,
                "original_name": flag.original_name,
                "original_thc": flag.original_thc,
                "original_cbd": flag.original_cbd,
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
            .filter(ScraperFlag.status.in_(["approved", "rejected"]))
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
