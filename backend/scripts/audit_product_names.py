"""
Audit script to check for products with weights embedded in names.

This script identifies products that have weight information stored
redundantly in both the product name and the weight fields.

Usage:
    python scripts/audit_product_names.py
"""
import sys
import re
sys.path.insert(0, '.')

from database import SessionLocal
from models import Product, Price, ScraperFlag, ScraperRun
from sqlalchemy import func


def has_weight_in_name(name: str) -> bool:
    """Check if a product name contains weight information."""
    if not name:
        return False

    # Pattern to match weights: "3.5g", "1oz", "1/8 oz", "100mg", etc.
    weight_pattern = re.compile(
        r'\s+\d+(?:\.\d+)?\s*(?:g|gram|grams|oz|ounce|mg|milligram|ml)\b|'
        r'\s+\d+\s*/\s*\d+\s*(?:oz|ounce)\b',
        re.IGNORECASE
    )

    return bool(weight_pattern.search(name))


def is_seed_data(product: Product) -> bool:
    """Determine if a product is from seed data (manually created)."""
    # Seed data uses predictable IDs like "prod-001", "prod-002"
    return product.id.startswith('prod-') and re.match(r'prod-\d{3}', product.id)


def audit_products():
    """Run the audit and display results."""
    db = SessionLocal()

    try:
        print("=" * 70)
        print("Product Name Audit Report")
        print("=" * 70)
        print()

        # Overall statistics
        total_products = db.query(Product).count()
        total_parents = db.query(Product).filter(Product.is_master == True).count()
        total_variants = db.query(Product).filter(Product.is_master == False).count()

        print(f"Total Products: {total_products}")
        print(f"  - Parent products: {total_parents}")
        print(f"  - Variant products: {total_variants}")
        print()

        # Check for weights in names
        parents_with_weights = []
        variants_with_weights = []

        all_products = db.query(Product).all()
        for product in all_products:
            if has_weight_in_name(product.name):
                if product.is_master:
                    parents_with_weights.append(product)
                else:
                    variants_with_weights.append(product)

        # Parent products with weights in names (PROBLEMATIC)
        print("=" * 70)
        print("PARENT Products with Weights in Names (PROBLEMATIC):")
        print("=" * 70)
        print(f"Count: {len(parents_with_weights)}")
        print()

        if parents_with_weights:
            seed_count = sum(1 for p in parents_with_weights if is_seed_data(p))
            scraped_count = len(parents_with_weights) - seed_count

            print(f"  - From seed data: {seed_count}")
            print(f"  - From scrapers: {scraped_count}")
            print()
            print("Examples:")
            for product in parents_with_weights[:10]:
                origin = "SEED" if is_seed_data(product) else "SCRAPED"
                print(f"  [{origin}] {product.id}: '{product.name}'")
        else:
            print("  ✓ No parent products with weights in names (GOOD!)")
        print()

        # Variant products with weights in names (EXPECTED for legacy, but should match parent)
        print("=" * 70)
        print("VARIANT Products with Weights in Names:")
        print("=" * 70)
        print(f"Count: {len(variants_with_weights)}")
        print()

        if variants_with_weights:
            seed_count = sum(1 for v in variants_with_weights if is_seed_data(v))
            scraped_count = len(variants_with_weights) - seed_count

            print(f"  - From seed data: {seed_count}")
            print(f"  - From scrapers: {scraped_count}")
            print()
            print("Note: Variants inherit names from parents. If parent has weight in name,")
            print("      variants will too. Check parent products first.")
            print()
            print("Examples:")
            for variant in variants_with_weights[:10]:
                parent = db.query(Product).filter(Product.id == variant.master_product_id).first()
                parent_name = parent.name if parent else "UNKNOWN"
                origin = "SEED" if is_seed_data(variant) else "SCRAPED"
                print(f"  [{origin}] {variant.id}: '{variant.name}' (parent: '{parent_name}')")
        else:
            print("  ✓ No variant products with weights in names")
        print()

        # Scraped data statistics
        print("=" * 70)
        print("Scraped Data Overview:")
        print("=" * 70)

        # Count scraped products
        scraped_parents = [p for p in all_products if p.is_master and not is_seed_data(p)]
        scraped_variants = [p for p in all_products if not p.is_master and not is_seed_data(p)]

        print(f"Total Scraped Products: {len(scraped_parents) + len(scraped_variants)}")
        print(f"  - Parents: {len(scraped_parents)}")
        print(f"  - Variants: {len(scraped_variants)}")
        print()

        # Prices associated with scraped products
        scraped_variant_ids = [v.id for v in scraped_variants]
        if scraped_variant_ids:
            scraped_prices = db.query(Price).filter(
                Price.product_id.in_(scraped_variant_ids)
            ).count()
            print(f"Prices on scraped variants: {scraped_prices}")
        else:
            print(f"Prices on scraped variants: 0")

        # ScraperFlags
        total_flags = db.query(ScraperFlag).count()
        pending_flags = db.query(ScraperFlag).filter(ScraperFlag.status == 'pending').count()
        print(f"Total ScraperFlags: {total_flags} (pending: {pending_flags})")
        print()

        # Scraper runs
        total_runs = db.query(ScraperRun).count()
        print(f"Total ScraperRuns: {total_runs}")
        print()

        # Recommendations
        print("=" * 70)
        print("Recommendations:")
        print("=" * 70)

        if len(parents_with_weights) > 0:
            print("⚠️  Parent products with weights in names detected!")
            print("   → Run purge_scraped_data.py to clean the database")
            print("   → Then re-run scrapers with the fixed pipeline")
        else:
            print("✓ No parent products with weights in names")
            print("  → Database is clean!")

        if len(scraped_parents) > 0 or len(scraped_variants) > 0:
            print()
            print(f"ℹ️  Found {len(scraped_parents) + len(scraped_variants)} scraped products")
            print("   → These will be deleted when running purge_scraped_data.py")
            print("   → Seed data will be preserved")

        print()
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    audit_products()
