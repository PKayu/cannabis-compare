"""
Data migration script: Convert flat products to parent/variant hierarchy.

Run AFTER the Alembic migration that adds weight/weight_grams columns.

Usage:
    cd backend
    python scripts/migrate_to_variants.py

What it does:
    1. For every is_master=True product with prices, creates a variant child
       and moves Price records from parent to variant.
    2. Deduplicates products with same brand + similar names (>90% fuzzy match).
    3. Parses weights from product names where possible.

Safe to run multiple times (idempotent).
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import Product, Price, Review, Watchlist, Brand
from services.normalization.weight_parser import parse_weight, extract_weight_from_name
from services.normalization.matcher import ProductMatcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def phase1_create_variants(db):
    """
    For every is_master=True product that has prices,
    create a variant child and move prices to it.
    """
    logger.info("=== Phase 1: Create variants from existing master products ===")

    parents = (
        db.query(Product)
        .filter(Product.is_master == True)
        .all()
    )

    created = 0
    skipped = 0

    for parent in parents:
        # Check if this parent already has variants
        existing_variants = (
            db.query(Product)
            .filter(
                Product.master_product_id == parent.id,
                Product.is_master == False
            )
            .count()
        )
        if existing_variants > 0:
            skipped += 1
            continue

        # Check if this parent has any prices
        prices = (
            db.query(Price)
            .filter(Price.product_id == parent.id)
            .all()
        )
        if not prices:
            skipped += 1
            continue

        # Try to extract weight from product name
        clean_name, weight_label, weight_grams = extract_weight_from_name(parent.name)

        # Create variant
        variant = Product(
            name=parent.name,
            product_type=parent.product_type,
            brand_id=parent.brand_id,
            thc_percentage=parent.thc_percentage,
            cbd_percentage=parent.cbd_percentage,
            is_master=False,
            master_product_id=parent.id,
            weight=weight_label,
            weight_grams=weight_grams,
            normalization_confidence=1.0
        )
        db.add(variant)
        db.flush()

        # Move all prices from parent to variant
        for price in prices:
            price.product_id = variant.id

        # If we extracted a weight from the name, clean up the parent name
        if weight_label and clean_name != parent.name:
            parent.name = clean_name

        created += 1
        logger.info(
            f"  Created variant for '{parent.name}' "
            f"(weight={weight_label}, moved {len(prices)} prices)"
        )

    db.flush()
    logger.info(f"Phase 1 complete: {created} variants created, {skipped} skipped")
    return created


def phase2_deduplicate(db):
    """
    Find is_master=True products with same brand + similar names (>90% fuzzy match).
    Merge duplicates into one parent.
    """
    logger.info("=== Phase 2: Deduplicate products ===")

    parents = (
        db.query(Product)
        .filter(Product.is_master == True)
        .order_by(Product.created_at.asc())
        .all()
    )

    merged = 0
    processed_ids = set()

    for i, product_a in enumerate(parents):
        if product_a.id in processed_ids:
            continue

        for product_b in parents[i + 1:]:
            if product_b.id in processed_ids:
                continue
            if product_b.brand_id != product_a.brand_id:
                continue

            # Score similarity
            score, match_type = ProductMatcher.score_match(
                scraped_name=product_b.name,
                master_name=product_a.name,
                scraped_brand="",  # Same brand, skip brand scoring
                master_brand="",
                scraped_thc=product_b.thc_percentage,
                master_thc=product_a.thc_percentage
            )

            if match_type == "auto_merge":
                logger.info(
                    f"  Merging '{product_b.name}' into '{product_a.name}' "
                    f"(score={score:.0%})"
                )

                # Move product_b's variants under product_a
                b_variants = (
                    db.query(Product)
                    .filter(
                        Product.master_product_id == product_b.id,
                        Product.is_master == False
                    )
                    .all()
                )
                for variant in b_variants:
                    variant.master_product_id = product_a.id

                # Move any direct prices from product_b to product_a's variants
                b_prices = (
                    db.query(Price)
                    .filter(Price.product_id == product_b.id)
                    .all()
                )
                if b_prices:
                    # Find or create a default variant for product_a
                    default_variant = (
                        db.query(Product)
                        .filter(
                            Product.master_product_id == product_a.id,
                            Product.is_master == False
                        )
                        .first()
                    )
                    if default_variant:
                        for price in b_prices:
                            # Check for conflict
                            existing = (
                                db.query(Price)
                                .filter(
                                    Price.product_id == default_variant.id,
                                    Price.dispensary_id == price.dispensary_id
                                )
                                .first()
                            )
                            if not existing:
                                price.product_id = default_variant.id
                            else:
                                db.delete(price)

                # Move reviews (handle unique constraint conflicts)
                b_reviews = (
                    db.query(Review)
                    .filter(Review.product_id == product_b.id)
                    .all()
                )
                for review in b_reviews:
                    existing = (
                        db.query(Review)
                        .filter(
                            Review.user_id == review.user_id,
                            Review.product_id == product_a.id
                        )
                        .first()
                    )
                    if not existing:
                        review.product_id = product_a.id
                    else:
                        # Keep the review with higher rating
                        if review.rating > existing.rating:
                            db.delete(existing)
                            review.product_id = product_a.id
                        else:
                            db.delete(review)

                # Move watchlist entries (skip conflicts)
                b_watchlists = (
                    db.query(Watchlist)
                    .filter(Watchlist.product_id == product_b.id)
                    .all()
                )
                for wl in b_watchlists:
                    existing = (
                        db.query(Watchlist)
                        .filter(
                            Watchlist.user_id == wl.user_id,
                            Watchlist.product_id == product_a.id
                        )
                        .first()
                    )
                    if not existing:
                        wl.product_id = product_a.id
                    else:
                        db.delete(wl)

                # Mark product_b as merged (convert to variant or delete)
                # Delete it since its data has been moved
                db.delete(product_b)
                processed_ids.add(product_b.id)
                merged += 1

    db.flush()
    logger.info(f"Phase 2 complete: {merged} products merged")
    return merged


def phase3_parse_weights(db):
    """
    For variants with weight=None, try to extract weight from name.
    """
    logger.info("=== Phase 3: Parse weights from product names ===")

    variants = (
        db.query(Product)
        .filter(
            Product.is_master == False,
            Product.weight == None
        )
        .all()
    )

    updated = 0
    for variant in variants:
        clean_name, weight_label, weight_grams = extract_weight_from_name(variant.name)
        if weight_label:
            variant.weight = weight_label
            variant.weight_grams = weight_grams
            updated += 1
            logger.info(f"  Parsed weight '{weight_label}' from '{variant.name}'")

    db.flush()
    logger.info(f"Phase 3 complete: {updated} weights parsed")
    return updated


def print_stats(db):
    """Print current database statistics."""
    parents = db.query(Product).filter(Product.is_master == True).count()
    variants = db.query(Product).filter(Product.is_master == False).count()
    prices_on_parents = (
        db.query(Price)
        .join(Product)
        .filter(Product.is_master == True)
        .count()
    )
    prices_on_variants = (
        db.query(Price)
        .join(Product)
        .filter(Product.is_master == False)
        .count()
    )
    total_reviews = db.query(Review).count()

    logger.info("=== Database Statistics ===")
    logger.info(f"  Parent products: {parents}")
    logger.info(f"  Variant products: {variants}")
    logger.info(f"  Prices on parents (should be 0): {prices_on_parents}")
    logger.info(f"  Prices on variants: {prices_on_variants}")
    logger.info(f"  Total reviews: {total_reviews}")


def main():
    db = SessionLocal()
    try:
        logger.info("Starting product variant migration...")
        print_stats(db)

        phase1_create_variants(db)
        phase2_deduplicate(db)
        phase3_parse_weights(db)

        db.commit()
        logger.info("Migration committed successfully!")

        print_stats(db)

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
