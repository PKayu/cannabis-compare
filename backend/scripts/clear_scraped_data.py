"""
Clear all scraped data from the database while preserving user-generated content.

This script removes:
- Products (master and variants)
- Prices
- Brands
- Promotions
- ScraperRuns
- ScraperFlags

Preserves:
- Users
- Reviews (orphaned after products deleted, but kept for reference)
- Watchlists (orphaned)
- PriceAlerts (orphaned)
- NotificationPreferences
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from models import Product, Price, Brand, Promotion, ScraperRun, ScraperFlag

def clear_scraped_data():
    """Clear all scraped data from database."""
    db = SessionLocal()

    try:
        print("Clearing scraped data from database...")
        print()

        # Count records before deletion
        product_count = db.query(Product).count()
        price_count = db.query(Price).count()
        brand_count = db.query(Brand).count()
        promo_count = db.query(Promotion).count()
        run_count = db.query(ScraperRun).count()
        flag_count = db.query(ScraperFlag).count()

        print(f"Current database state:")
        print(f"   Products: {product_count}")
        print(f"   Prices: {price_count}")
        print(f"   Brands: {brand_count}")
        print(f"   Promotions: {promo_count}")
        print(f"   ScraperRuns: {run_count}")
        print(f"   ScraperFlags: {flag_count}")
        print()

        if product_count == 0 and price_count == 0:
            print("[OK] Database already empty of scraped data")
            return

        print("Deleting records...")

        # Delete in order to respect foreign key constraints
        # 1. Delete Prices (references Product and Dispensary)
        deleted = db.query(Price).delete()
        print(f"   [OK] Deleted {deleted} Price records")

        # 2. Delete ScraperFlags (references Product)
        deleted = db.query(ScraperFlag).delete()
        print(f"   [OK] Deleted {deleted} ScraperFlag records")

        # 3. Delete Products (master and variants)
        deleted = db.query(Product).delete()
        print(f"   [OK] Deleted {deleted} Product records")

        # 4. Delete Brands (no longer referenced)
        deleted = db.query(Brand).delete()
        print(f"   [OK] Deleted {deleted} Brand records")

        # 5. Delete Promotions
        deleted = db.query(Promotion).delete()
        print(f"   [OK] Deleted {deleted} Promotion records")

        # 6. Delete ScraperRuns (execution history)
        deleted = db.query(ScraperRun).delete()
        print(f"   [OK] Deleted {deleted} ScraperRun records")

        # Commit all deletions
        db.commit()

        print()
        print("[SUCCESS] Database cleared successfully!")
        print()
        print("Note: User-generated content preserved:")
        print("   - Users")
        print("   - Reviews (orphaned - no product references)")
        print("   - Watchlists (orphaned)")
        print("   - PriceAlerts (orphaned)")
        print("   - NotificationPreferences")
        print()

    except Exception as e:
        print(f"[ERROR] Error clearing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clear_scraped_data()
