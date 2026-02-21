"""
Process and resolve ScraperFlags created by the scraper.

Provides admin functionality to:
- Approve merges (link flagged product to matched master) [legacy match_review]
- Reject merges (create new master product from flagged data) [legacy match_review]
- Dismiss bad imports (no product created)
- Clean and activate dirty products [data_cleanup]
- Delete garbage products [data_cleanup]
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
        # Editable field overrides for the incoming (flagged) product
        name: Optional[str] = None,
        brand_name: Optional[str] = None,
        product_type: Optional[str] = None,
        thc_percentage: Optional[float] = None,
        cbd_percentage: Optional[float] = None,
        weight: Optional[str] = None,
        price: Optional[float] = None,
        issue_tags: Optional[List[str]] = None,
        # Overrides for the matched (existing) product
        matched_product_name: Optional[str] = None,
        matched_product_brand: Optional[str] = None,
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
            # Apply incoming-product overrides to the matched parent
            final_parent_name = matched_product_name if matched_product_name is not None else name
            final_parent_brand = matched_product_brand if matched_product_brand is not None else brand_name
            if final_parent_name is not None and final_parent_name != parent.name:
                parent.name = final_parent_name
            if product_type is not None and product_type != parent.product_type:
                parent.product_type = product_type
            if final_parent_brand is not None:
                existing_brand = parent.brand
                if not existing_brand or existing_brand.name.lower() != final_parent_brand.lower():
                    brand = (
                        db.query(Brand)
                        .filter(Brand.name.ilike(final_parent_brand))
                        .first()
                    )
                    if not brand:
                        brand = Brand(name=final_parent_brand)
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
            weight=final_weight,
            url=flag.original_url
        )

        # Create/find variant under the matched parent
        variant = find_or_create_variant(
            db, flag.matched_product_id, final_weight, scraped
        )

        # Create price record if we have price data
        if final_price and final_price > 0:
            ConfidenceScorer.update_or_create_price(
                db, variant.id, flag.dispensary_id, final_price,
                product_url=flag.original_url
            )

        # Update flag status
        flag.status = "approved"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes
        if issue_tags:
            flag.issue_tags = issue_tags

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
        issue_tags: Optional[List[str]] = None,
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
            weight=final_weight,
            url=flag.original_url
        )
        variant = find_or_create_variant(
            db, parent.id, final_weight, scraped
        )

        # Create price record if we have price data
        if final_price and final_price > 0:
            ConfidenceScorer.update_or_create_price(
                db, variant.id, flag.dispensary_id, final_price,
                product_url=flag.original_url
            )

        # Update flag status
        flag.status = "rejected"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes
        if issue_tags:
            flag.issue_tags = issue_tags

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
        notes: str = "",
        issue_tags: Optional[List[str]] = None,
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

        if flag.status not in ("pending", "auto_merged"):
            raise ValueError(
                f"Flag already resolved with status: {flag.status}"
            )

        flag.status = "dismissed"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes
        if issue_tags:
            flag.issue_tags = issue_tags

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
                "original_url": flag.original_url,
                "brand_name": flag.brand_name,
                "dispensary_id": flag.dispensary_id,
                "dispensary_name": dispensary.name if dispensary else None,
                "confidence_score": flag.confidence_score,
                "confidence_percent": f"{flag.confidence_score:.0%}",
                "matched_product": matched_product,
                "merge_reason": flag.merge_reason,
                "issue_tags": flag.issue_tags,
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
    def merge_duplicate_flag(
        db: Session,
        flag_id: str,
        kept_product_id: str,
        admin_id: str,
        notes: str = "",
    ) -> dict:
        """
        Resolve a same-dispensary duplicate by merging the loser into the winner.

        Moves all Price, Review, and Watchlist records from the loser product
        to the winner (kept_product_id), then soft-deletes the loser.

        Args:
            db: Database session
            flag_id: ScraperFlag ID referencing the two products
            kept_product_id: ID of the product to keep (winner)
            admin_id: Resolving admin's ID
            notes: Optional admin notes

        Returns:
            dict with winner_id, loser_id, prices_moved, reviews_moved, watchlist_moved
        """
        from models import ScraperFlag, Product, Price, Review

        flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()
        if not flag:
            raise ValueError(f"ScraperFlag not found: {flag_id}")
        if flag.status != "pending":
            raise ValueError(f"Flag already resolved with status: {flag.status}")
        if not flag.matched_product_id:
            raise ValueError(f"Flag has no matched product to merge: {flag_id}")

        # Determine the loser — whichever product is NOT the kept one
        candidate_ids = {flag.matched_product_id}
        # The "incoming" product may have already been created as a variant;
        # if not, we just work with the matched product pair
        if kept_product_id not in candidate_ids:
            raise ValueError(
                f"kept_product_id {kept_product_id} must be one of the flagged products: "
                f"{candidate_ids}"
            )

        loser_id = next(id for id in candidate_ids if id != kept_product_id)

        # Ensure both products exist
        winner = db.query(Product).filter(Product.id == kept_product_id).first()
        loser = db.query(Product).filter(Product.id == loser_id).first()
        if not winner:
            raise ValueError(f"Winner product not found: {kept_product_id}")
        if not loser:
            raise ValueError(f"Loser product not found: {loser_id}")

        # Move Price records
        prices_moved = (
            db.query(Price)
            .filter(Price.product_id == loser_id)
            .update({Price.product_id: kept_product_id}, synchronize_session=False)
        )

        # Move Review records (reviews attach to master products)
        reviews_moved = (
            db.query(Review)
            .filter(Review.product_id == loser_id)
            .update({Review.product_id: kept_product_id}, synchronize_session=False)
        )

        # Move Watchlist records if model exists
        watchlist_moved = 0
        try:
            from models import Watchlist
            watchlist_moved = (
                db.query(Watchlist)
                .filter(Watchlist.product_id == loser_id)
                .update({Watchlist.product_id: kept_product_id}, synchronize_session=False)
            )
        except Exception:
            pass  # Watchlist model may not exist in all deployments

        # Soft-delete the loser
        loser.is_active = False
        loser.master_product_id = kept_product_id  # Point to winner for traceability

        # Resolve flag
        flag.status = "dismissed"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes or f"Duplicate merged: kept {kept_product_id}"
        flag.issue_tags = flag.issue_tags or []
        if "duplicate" not in (flag.issue_tags or []):
            flag.issue_tags = list(flag.issue_tags or []) + ["duplicate_merged"]

        db.commit()

        logger.info(
            f"Merged duplicate: loser={loser_id} -> winner={kept_product_id} "
            f"(prices={prices_moved}, reviews={reviews_moved}) by admin {admin_id}"
        )

        return {
            "winner_id": kept_product_id,
            "loser_id": loser_id,
            "prices_moved": prices_moved,
            "reviews_moved": reviews_moved,
            "watchlist_moved": watchlist_moved,
        }

    @staticmethod
    def clean_and_activate(
        db: Session,
        flag_id: str,
        admin_id: str,
        notes: str = "",
        name: Optional[str] = None,
        brand_name: Optional[str] = None,
        product_type: Optional[str] = None,
        thc_percentage: Optional[float] = None,
        cbd_percentage: Optional[float] = None,
        weight: Optional[str] = None,
        price: Optional[float] = None,
        issue_tags: Optional[List[str]] = None,
    ) -> str:
        """
        Clean up a data_cleanup flag by applying edits to the linked product
        and setting is_active=True.

        Unlike approve_flag (which merges into a matched product), this edits
        the product that was ALREADY CREATED and stored on matched_product_id.

        Returns:
            ID of the activated parent product
        """
        from models import ScraperFlag, Product, Brand, Price
        from services.normalization.weight_parser import parse_weight

        flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()
        if not flag:
            raise ValueError(f"ScraperFlag not found: {flag_id}")
        if flag.status != "pending":
            raise ValueError(f"Flag already resolved with status: {flag.status}")
        if flag.flag_type != "data_cleanup":
            raise ValueError(
                f"clean_and_activate is only for data_cleanup flags, got: {flag.flag_type}"
            )
        if not flag.matched_product_id:
            raise ValueError(f"Flag has no linked product: {flag_id}")

        # Load the product that was created during scraping
        product = db.query(Product).filter(
            Product.id == flag.matched_product_id
        ).first()
        if not product:
            raise ValueError(f"Linked product not found: {flag.matched_product_id}")

        # Track corrections
        overrides = {
            "name": name, "brand_name": brand_name, "product_type": product_type,
            "thc_percentage": thc_percentage, "cbd_percentage": cbd_percentage,
            "weight": weight, "price": price,
        }
        corrections = _build_corrections(flag, overrides)
        if corrections:
            flag.corrections = corrections

        # Apply edits to the parent product
        if name is not None and name != product.name:
            product.name = name
            # Also update variant names to stay consistent
            for variant in product.variants:
                variant.name = name
        if product_type is not None:
            product.product_type = product_type
        if thc_percentage is not None:
            product.thc_percentage = thc_percentage
        if cbd_percentage is not None:
            product.cbd_percentage = cbd_percentage

        # Handle brand change
        if brand_name is not None:
            existing_brand = product.brand
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
                product.brand_id = brand.id

        # Handle weight change on variants
        if weight is not None:
            weight_label, weight_g = parse_weight(weight)
            for variant in product.variants:
                variant.weight = weight_label
                variant.weight_grams = weight_g

        # Handle price update on existing price records
        if price is not None and price > 0:
            for variant in product.variants:
                existing_prices = (
                    db.query(Price)
                    .filter(Price.product_id == variant.id)
                    .all()
                )
                for p in existing_prices:
                    p.update_price(price)

        # Activate the product
        product.is_active = True

        # Resolve the flag
        flag.status = "cleaned"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes
        if issue_tags:
            flag.issue_tags = issue_tags

        db.commit()

        logger.info(
            f"Cleaned and activated product '{product.name}' (id={product.id}) "
            f"by admin {admin_id}"
            f"{' with corrections' if corrections else ''}"
        )

        return product.id

    @staticmethod
    def delete_flagged_product(
        db: Session,
        flag_id: str,
        admin_id: str,
        notes: str = "",
    ) -> None:
        """
        Delete the product linked to a data_cleanup flag (garbage data).

        The product and its variants are deleted. The flag is kept with
        status='dismissed' for analytics.
        """
        from models import ScraperFlag, Product

        flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()
        if not flag:
            raise ValueError(f"ScraperFlag not found: {flag_id}")
        if flag.status != "pending":
            raise ValueError(f"Flag already resolved with status: {flag.status}")
        if flag.flag_type != "data_cleanup":
            raise ValueError(
                f"delete_flagged_product is only for data_cleanup flags, got: {flag.flag_type}"
            )

        # Delete the product if it exists
        if flag.matched_product_id:
            product = db.query(Product).filter(
                Product.id == flag.matched_product_id
            ).first()
            if product:
                # Delete variants first
                for variant in product.variants:
                    db.delete(variant)
                db.delete(product)

        # Resolve the flag
        flag.status = "dismissed"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes or "Product deleted (garbage data)"
        flag.matched_product_id = None  # Clear reference since product is gone

        db.commit()

        logger.info(
            f"Deleted flagged product for flag '{flag.original_name}' by admin {admin_id}"
        )

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
