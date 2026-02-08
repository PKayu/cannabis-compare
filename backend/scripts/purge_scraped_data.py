"""
Purge scraped data from the database while preserving seed data.

This script deletes all products created by scrapers, along with their
associated prices and flags. Manually created seed data is preserved.

Usage:
    python scripts/purge_scraped_data.py [--dry-run] [--yes]

Options:
    --dry-run    Show what would be deleted without actually deleting
    --yes        Skip confirmation prompt and proceed with deletion
"""
import sys
import re
import argparse
sys.path.insert(0, '.')

from database import SessionLocal
from models import Product, Price, ScraperFlag, Brand
from sqlalchemy import and_


def is_seed_data(product: Product) -> bool:
    """Determine if a product is from seed data (manually created)."""
    # Seed data uses predictable IDs like "prod-001", "prod-002"
    return product.id.startswith('prod-') and re.match(r'prod-\d{3}', product.id)


def purge_scraped_data(dry_run: bool = False, skip_confirmation: bool = False):
    """
    Purge scraped data from the database.

    Args:
        dry_run: If True, show what would be deleted without deleting
        skip_confirmation: If True, skip the confirmation prompt
    """
    db = SessionLocal()

    try:
        print("=" * 70)
        print("Scraped Data Purge")
        print("=" * 70)
        print()

        # Identify scraped products
        all_products = db.query(Product).all()
        scraped_parents = []
        scraped_variants = []
        seed_parents = []
        seed_variants = []

        for product in all_products:
            if is_seed_data(product):
                if product.is_master:
                    seed_parents.append(product)
                else:
                    seed_variants.append(product)
            else:
                if product.is_master:
                    scraped_parents.append(product)
                else:
                    scraped_variants.append(product)

        # Count associated data
        scraped_variant_ids = [v.id for v in scraped_variants]
        scraped_parent_ids = [p.id for p in scraped_parents]
        all_scraped_ids = scraped_variant_ids + scraped_parent_ids

        if scraped_variant_ids:
            scraped_prices = db.query(Price).filter(
                Price.product_id.in_(scraped_variant_ids)
            ).all()
        else:
            scraped_prices = []

        all_flags = db.query(ScraperFlag).all()

        print("Analysis:")
        print("-" * 70)
        print(f"Seed Data (WILL BE PRESERVED):")
        print(f"  - Parent products: {len(seed_parents)}")
        print(f"  - Variant products: {len(seed_variants)}")
        print()
        print(f"Scraped Data (WILL BE DELETED):")
        print(f"  - Parent products: {len(scraped_parents)}")
        print(f"  - Variant products: {len(scraped_variants)}")
        print(f"  - Prices on scraped variants: {len(scraped_prices)}")
        print(f"  - ScraperFlags: {len(all_flags)}")
        print()

        if len(scraped_parents) == 0 and len(scraped_variants) == 0:
            print("✓ No scraped data found. Nothing to delete.")
            print()
            return

        # Show examples
        if scraped_parents:
            print("Examples of scraped parent products to be deleted:")
            for product in scraped_parents[:5]:
                print(f"  - {product.id}: '{product.name}'")
            if len(scraped_parents) > 5:
                print(f"  ... and {len(scraped_parents) - 5} more")
            print()

        # Confirmation
        if not skip_confirmation and not dry_run:
            print("=" * 70)
            response = input("Are you sure you want to delete all scraped data? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Cancelled.")
                return

        if dry_run:
            print()
            print("=" * 70)
            print("DRY RUN MODE - No data will be deleted")
            print("=" * 70)
            print()
            print("The following would be deleted:")
            print(f"  - {len(scraped_parents)} scraped parent products")
            print(f"  - {len(scraped_variants)} scraped variant products")
            print(f"  - {len(scraped_prices)} prices")
            print(f"  - {len(all_flags)} scraper flags")
            print()
            print("Run without --dry-run to actually delete this data.")
            return

        # Perform deletion
        print()
        print("=" * 70)
        print("Deleting scraped data...")
        print("=" * 70)
        print()

        # Delete prices first (foreign key constraint)
        if scraped_prices:
            print(f"Deleting {len(scraped_prices)} prices...")
            for price in scraped_prices:
                db.delete(price)
            db.commit()
            print(f"  ✓ Deleted {len(scraped_prices)} prices")

        # Delete scraper flags
        if all_flags:
            print(f"Deleting {len(all_flags)} scraper flags...")
            for flag in all_flags:
                db.delete(flag)
            db.commit()
            print(f"  ✓ Deleted {len(all_flags)} scraper flags")

        # Delete variant products
        if scraped_variants:
            print(f"Deleting {len(scraped_variants)} scraped variant products...")
            for variant in scraped_variants:
                db.delete(variant)
            db.commit()
            print(f"  ✓ Deleted {len(scraped_variants)} variant products")

        # Delete parent products
        if scraped_parents:
            print(f"Deleting {len(scraped_parents)} scraped parent products...")
            for parent in scraped_parents:
                db.delete(parent)
            db.commit()
            print(f"  ✓ Deleted {len(scraped_parents)} parent products")

        print()
        print("=" * 70)
        print("Purge Complete!")
        print("=" * 70)
        print()

        # Verify what's left
        remaining_products = db.query(Product).count()
        remaining_parents = db.query(Product).filter(Product.is_master == True).count()
        remaining_variants = db.query(Product).filter(Product.is_master == False).count()
        remaining_prices = db.query(Price).count()

        print("Remaining data:")
        print(f"  - Total products: {remaining_products}")
        print(f"  - Parent products: {remaining_parents}")
        print(f"  - Variant products: {remaining_variants}")
        print(f"  - Prices: {remaining_prices}")
        print()

        print("✓ Seed data has been preserved")
        print("✓ Ready for scraper runs with fixed pipeline")
        print()

    except Exception as e:
        db.rollback()
        print(f"❌ Error during purge: {e}")
        raise
    finally:
        db.close()


def main():
    """Parse arguments and run the purge."""
    parser = argparse.ArgumentParser(
        description="Purge scraped data while preserving seed data"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help="Skip confirmation prompt and proceed with deletion"
    )

    args = parser.parse_args()

    purge_scraped_data(dry_run=args.dry_run, skip_confirmation=args.yes)


if __name__ == "__main__":
    main()
