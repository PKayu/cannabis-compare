"""
Confidence scoring and product normalization service.

Handles the decision logic for scraped products:
- >90% confidence: Auto-merge to existing product (create variant)
- <90% confidence: Create new product entry (parent + variant)
  - Clean data: product is active immediately
  - Dirty data: product is inactive, flagged for admin cleanup

Products use a parent/variant hierarchy:
- Parent (is_master=True): canonical product, holds reviews
- Variant (is_master=False): quantity-specific, holds prices
"""
from sqlalchemy.orm import Session
from typing import Optional, Tuple, List
import logging

from services.normalization.matcher import ProductMatcher
from services.normalization.weight_parser import parse_weight, extract_weight_from_name
from services.normalization.name_cleaner import clean_product_name
from services.scrapers.base_scraper import ScrapedProduct

logger = logging.getLogger(__name__)


def find_or_create_variant(
    db: Session,
    parent_id: str,
    raw_weight: Optional[str],
    scraped: ScrapedProduct
) -> "Product":
    """
    Find existing variant by parent_id + weight_grams, or create a new one.

    Args:
        db: Database session
        parent_id: ID of the parent product
        raw_weight: Raw weight string from scraper (e.g., "3.5g")
        scraped: Original scraped product data

    Returns:
        The variant Product record
    """
    from models import Product

    weight_label, weight_g = parse_weight(raw_weight)

    # Look for existing variant with same weight under this parent
    if weight_g is not None:
        existing = (
            db.query(Product)
            .filter(
                Product.master_product_id == parent_id,
                Product.is_master.is_(False),
                Product.weight_grams == weight_g
            )
            .first()
        )
        if existing:
            return existing
    else:
        # Look for a weightless variant
        existing = (
            db.query(Product)
            .filter(
                Product.master_product_id == parent_id,
                Product.is_master.is_(False),
                Product.weight_grams.is_(None)
            )
            .first()
        )
        if existing:
            return existing

    # Create new variant
    parent = db.query(Product).filter(Product.id == parent_id).first()
    if not parent:
        raise ValueError(f"Parent product not found: {parent_id}")

    variant = Product(
        name=parent.name,
        product_type=parent.product_type,
        brand_id=parent.brand_id,
        thc_percentage=scraped.thc_percentage or parent.thc_percentage,
        cbd_percentage=scraped.cbd_percentage or parent.cbd_percentage,
        cbg_percentage=scraped.cbg_percentage or parent.cbg_percentage,
        thc_content=scraped.thc_content or parent.thc_content,
        cbd_content=scraped.cbd_content or parent.cbd_content,
        is_master=False,
        master_product_id=parent_id,
        weight=weight_label,
        weight_grams=weight_g,
        normalization_confidence=1.0
    )
    db.add(variant)
    db.flush()

    logger.info(
        f"Created variant for '{parent.name}' "
        f"(weight={weight_label}, parent={parent_id})"
    )
    return variant


class ConfidenceScorer:
    """Manages confidence-based product matching and normalization"""

    @staticmethod
    def process_scraped_product(
        db: Session,
        scraped_product: ScrapedProduct,
        dispensary_id: str,
        candidates: Optional[List[dict]] = None
    ) -> Tuple[Optional[str], str]:
        """
        Process a scraped product and determine how to handle it.

        Args:
            db: Database session
            scraped_product: Product data from scraper
            dispensary_id: ID of the dispensary being scraped
            candidates: Pre-computed list of master products for matching
                        (avoids re-querying on every call). Each dict has:
                        id, name, brand, thc_percentage.
                        List is mutated (new products appended) for cache freshness.

        Returns:
            Tuple of (product_id, action_taken)
            - product_id: ID of the variant product (always set now)
            - action_taken: "auto_merge" | "new_product" | "new_product_flagged"
        """
        from models import Product, ScraperFlag, Price

        # Build candidate list if not provided
        if candidates is None:
            master_products = (
                db.query(Product)
                .filter(Product.is_master.is_(True))
                .all()
            )
            candidates = []
            for master in master_products:
                candidates.append({
                    "id": master.id,
                    "name": master.name,
                    "brand": master.brand.name if master.brand else "",
                    "thc_percentage": master.thc_percentage
                })

        # Clean name first (remove cart text, junk), then extract weight
        junk_cleaned = clean_product_name(scraped_product.name)
        clean_name, extracted_weight_label, extracted_weight_g = extract_weight_from_name(
            junk_cleaned
        )
        name_for_matching = clean_name or junk_cleaned

        # Find best match using clean name
        best_match, confidence, match_type = ProductMatcher.find_best_match(
            scraped_name=name_for_matching,
            scraped_brand=scraped_product.brand,
            candidates=candidates,
            scraped_thc=scraped_product.thc_percentage
        )

        if match_type == "auto_merge" and best_match:
            # AUTO-MERGE: Create/find variant under the matched parent
            logger.info(
                f"Auto-merging '{name_for_matching}' to '{best_match['name']}' "
                f"(confidence: {confidence:.0%})"
            )
            # Use extracted weight if scraper didn't provide one
            weight_to_use = scraped_product.weight or extracted_weight_label
            variant = find_or_create_variant(
                db, best_match["id"], weight_to_use, scraped_product
            )

            # Only create an audit flag for TRUE cross-dispensary merges.
            # If the matched product already has a price at this dispensary,
            # this is a routine price refresh — no admin review needed.
            existing_price_at_dispensary = (
                db.query(Price)
                .join(Product, Price.product_id == Product.id)
                .filter(
                    Product.master_product_id == best_match["id"],
                    Price.dispensary_id == dispensary_id
                )
                .first()
            )
            if not existing_price_at_dispensary:
                audit_flag = ScraperFlag(
                    original_name=name_for_matching,
                    original_thc=scraped_product.thc_percentage,
                    original_cbd=scraped_product.cbd_percentage,
                    original_thc_content=scraped_product.thc_content,
                    original_cbd_content=scraped_product.cbd_content,
                    brand_name=scraped_product.brand or "Unknown",
                    dispensary_id=dispensary_id,
                    matched_product_id=best_match["id"],
                    confidence_score=confidence,
                    status="auto_merged",
                    merge_reason=f"Auto-merged at {confidence:.0%} confidence (cross-dispensary)",
                    original_weight=scraped_product.weight,
                    original_price=scraped_product.price,
                    original_category=scraped_product.category,
                    original_url=scraped_product.url,
                )
                db.add(audit_flag)
                db.flush()

            return variant.id, "auto_merge"

        else:
            # NEW PRODUCT: Always create parent + variant (replaces both
            # the old "flagged_review" and "new_product" branches)
            logger.info(
                f"Creating new product for '{name_for_matching}' "
                f"(confidence: {confidence:.0%})"
            )

            # Get or create brand
            brand_id = ConfidenceScorer._get_or_create_brand(
                db, scraped_product.brand
            )

            # Check data quality to decide if product needs admin cleanup.
            # Pass junk_cleaned (after junk removal, before weight extraction)
            # so the reduction-ratio check doesn't false-positive on weights.
            from services.normalization.data_quality import check_data_quality
            is_dirty, issue_tags = check_data_quality(
                scraped_product, junk_cleaned
            )

            # Create parent product (is_master=True, no weight in name)
            # Dirty products are inactive until admin cleans them up
            parent = Product(
                name=name_for_matching,  # Use clean name without weight
                product_type=scraped_product.category,
                brand_id=brand_id,
                thc_percentage=scraped_product.thc_percentage,
                cbd_percentage=scraped_product.cbd_percentage,
                cbg_percentage=scraped_product.cbg_percentage,
                thc_content=scraped_product.thc_content,
                cbd_content=scraped_product.cbd_content,
                is_master=True,
                is_active=not is_dirty,
                normalization_confidence=1.0
            )
            db.add(parent)
            db.flush()

            # Create variant product (is_master=False, with weight)
            # Use extracted weight if scraper didn't provide one
            weight_to_use = scraped_product.weight or extracted_weight_label
            variant = find_or_create_variant(
                db, parent.id, weight_to_use, scraped_product
            )

            # Add parent to candidates cache so subsequent products can match
            candidates.append({
                "id": parent.id,
                "name": parent.name,  # Clean name for future matching
                "brand": scraped_product.brand,
                "thc_percentage": scraped_product.thc_percentage
            })

            # If dirty data, create a data_cleanup flag for admin
            if is_dirty:
                flag = ScraperFlag(
                    original_name=name_for_matching,
                    original_thc=scraped_product.thc_percentage,
                    original_cbd=scraped_product.cbd_percentage,
                    original_thc_content=scraped_product.thc_content,
                    original_cbd_content=scraped_product.cbd_content,
                    brand_name=scraped_product.brand or "Unknown",
                    dispensary_id=dispensary_id,
                    matched_product_id=parent.id,  # Points to CREATED product
                    confidence_score=confidence,
                    status="pending",
                    flag_type="data_cleanup",
                    merge_reason=f"Data quality issues: {', '.join(issue_tags)}",
                    original_weight=scraped_product.weight,
                    original_price=scraped_product.price,
                    original_category=scraped_product.category,
                    original_url=scraped_product.url,
                    issue_tags=issue_tags,
                )
                db.add(flag)
                db.flush()
                return variant.id, "new_product_flagged"

            return variant.id, "new_product"

    @staticmethod
    def _get_or_create_brand(db: Session, brand_name: str) -> str:
        """Get existing brand or create new one."""
        from models import Brand

        # Handle None or empty brand name
        if not brand_name:
            brand_name = "Unknown"

        brand = (
            db.query(Brand)
            .filter(Brand.name.ilike(brand_name))
            .first()
        )

        if not brand:
            brand = Brand(name=brand_name)
            db.add(brand)
            db.flush()
            logger.info(f"Created new brand: {brand_name}")

        return brand.id

    @staticmethod
    def update_or_create_price(
        db: Session,
        product_id: str,
        dispensary_id: str,
        price: float,
        in_stock: bool = True,
        product_url: Optional[str] = None
    ) -> str:
        """Update existing price or create new price entry."""
        from models import Price

        existing_price = (
            db.query(Price)
            .filter(
                Price.product_id == product_id,
                Price.dispensary_id == dispensary_id
            )
            .first()
        )

        if existing_price:
            existing_price.update_price(price)
            existing_price.in_stock = in_stock
            if product_url is not None:
                existing_price.product_url = product_url
            db.flush()
            return existing_price.id
        else:
            new_price = Price(
                product_id=product_id,
                dispensary_id=dispensary_id,
                amount=price,
                in_stock=in_stock,
                product_url=product_url
            )
            db.add(new_price)
            db.flush()
            return new_price.id

    @staticmethod
    def get_normalization_stats(db: Session) -> dict:
        """Get statistics about product normalization."""
        from models import ScraperFlag, Product

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
            .filter(Product.is_master.is_(True))
            .count()
        )

        variant_products = (
            db.query(Product)
            .filter(Product.is_master.is_(False))
            .count()
        )

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
            "variant_products": variant_products,
            "estimated_auto_merge_rate": f"{auto_merge_rate:.1f}%"
        }
