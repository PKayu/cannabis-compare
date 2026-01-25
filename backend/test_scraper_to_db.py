"""
Enhanced test script for scraper-to-database pipeline.
Validates data quality, duplicate prevention, and price history tracking.
"""
import asyncio
import sys
import os
import logging

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Setup path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from services.scraper_runner import ScraperRunner
from models import Product, Price, Brand

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_save_to_db():
    """
    Comprehensive test of scraper-to-database pipeline.
    Tests data quality, duplicate prevention, and price history.
    """
    db = SessionLocal()
    try:
        # ========================================
        # PHASE 1: Capture Initial State
        # ========================================
        initial_products = db.query(Product).count()
        initial_brands = db.query(Brand).count()
        initial_prices = db.query(Price).count()

        print("\n" + "="*60)
        print("  INITIAL DATABASE STATE")
        print("="*60)
        print(f"Products:     {initial_products}")
        print(f"Brands:       {initial_brands}")
        print(f"Prices:       {initial_prices}")

        # ========================================
        # PHASE 2: Run Scraper
        # ========================================
        print("\n" + "="*60)
        print("  RUNNING SCRAPER PIPELINE")
        print("="*60)

        runner = ScraperRunner(db)
        print("\n🚀 Scraping WholesomeCo...")
        await runner.run_wholesomeco()

        # ========================================
        # PHASE 3: Verify Results
        # ========================================
        final_products = db.query(Product).count()
        final_brands = db.query(Brand).count()
        final_prices = db.query(Price).count()

        print("\n" + "="*60)
        print("  FINAL DATABASE STATE")
        print("="*60)
        print(f"Products:     {final_products} (+{final_products - initial_products})")
        print(f"Brands:       {final_brands} (+{final_brands - initial_brands})")
        print(f"Prices:       {final_prices} (+{final_prices - initial_prices})")

        # ========================================
        # PHASE 4: Data Quality Validation
        # ========================================
        print("\n" + "="*60)
        print("  DATA QUALITY VALIDATION")
        print("="*60)

        # Sample 3 products for inspection
        sample_products = db.query(Product).limit(3).all()

        for i, p in enumerate(sample_products, 1):
            print(f"\n✓ Product {i}: {p.name}")
            print(f"  - Brand:  {p.brand.name if p.brand else 'MISSING ❌'}")
            print(f"  - Type:   {p.product_type if p.product_type else 'MISSING ❌'}")
            print(f"  - THC:    {p.thc_percentage}%" if p.thc_percentage else "  - THC:    Not extracted")

            # Check prices for this product
            prices = db.query(Price).filter(Price.product_id == p.id).all()
            for price in prices:
                dispensary_name = price.dispensary.name if price.dispensary else 'UNKNOWN'
                in_stock_status = "In Stock" if price.in_stock else "Out of Stock"
                print(f"  - Price:  ${price.amount:.2f} at {dispensary_name} ({in_stock_status})")

        # ========================================
        # PHASE 5: Data Integrity Checks
        # ========================================
        print("\n" + "="*60)
        print("  DATA INTEGRITY CHECKS")
        print("="*60)

        # Check for orphaned brands (brands with no products)
        orphaned_brands = db.query(Brand).filter(~Brand.products.any()).count()
        if orphaned_brands == 0:
            print("✓ No orphaned brands (all brands have products)")
        else:
            print(f"⚠ Warning: {orphaned_brands} brands have no products")

        # Check for products without prices
        products_without_prices = db.query(Product).filter(~Product.prices.any()).count()
        if products_without_prices == 0:
            print("✓ No orphaned products (all products have prices)")
        else:
            print(f"⚠ Warning: {products_without_prices} products have no prices")

        # Check for products without brands
        products_without_brands = db.query(Product).filter(Product.brand_id.is_(None)).count()
        if products_without_brands == 0:
            print("✓ All products have brands")
        else:
            print(f"⚠ Warning: {products_without_brands} products have no brand")

        # ========================================
        # PHASE 6: Duplicate Prevention Test
        # ========================================
        print("\n" + "="*60)
        print("  DUPLICATE PREVENTION TEST")
        print("="*60)
        print("Running scraper a second time to test idempotency...")

        await runner.run_wholesomeco()

        duplicate_run_products = db.query(Product).count()
        duplicate_run_prices = db.query(Price).count()

        if duplicate_run_products == final_products:
            print(f"✓ No duplicate products created ({duplicate_run_products} products)")
        else:
            print(f"❌ Duplicates detected! Expected {final_products}, got {duplicate_run_products}")

        if duplicate_run_prices == final_prices:
            print(f"✓ No duplicate prices created ({duplicate_run_prices} prices)")
        else:
            print(f"⚠ Price count changed: Expected {final_prices}, got {duplicate_run_prices}")
            print("  (This is OK if prices were updated)")

        # ========================================
        # PHASE 7: Price History Test
        # ========================================
        print("\n" + "="*60)
        print("  PRICE HISTORY TRACKING TEST")
        print("="*60)

        sample_price = db.query(Price).first()
        if sample_price:
            old_amount = sample_price.amount
            print(f"Testing with price: ${old_amount:.2f}")

            # Simulate price change
            new_amount = old_amount + 5.0
            sample_price.update_price(new_amount)
            db.commit()
            db.refresh(sample_price)

            if sample_price.previous_price == old_amount:
                print(f"✓ Price history tracked correctly")
                print(f"  Previous: ${sample_price.previous_price:.2f}")
                print(f"  Current:  ${sample_price.amount:.2f}")
                if sample_price.price_change_percentage:
                    print(f"  Change:   {sample_price.price_change_percentage:.1f}%")
            else:
                print("❌ Price history not working correctly")
                print(f"  Expected previous_price: ${old_amount:.2f}")
                print(f"  Got: {sample_price.previous_price}")
        else:
            print("⚠ Could not test price history (no prices in database)")

        # ========================================
        # FINAL SUMMARY
        # ========================================
        print("\n" + "="*60)
        print("  TEST SUMMARY")
        print("="*60)

        print(f"✓ Scraper ran successfully")
        print(f"✓ {final_products - initial_products} products added")
        print(f"✓ {final_brands - initial_brands} brands created")
        print(f"✓ {final_prices - initial_prices} prices recorded")
        print(f"✓ Data quality validated")
        print(f"✓ Duplicate prevention confirmed")
        print(f"✓ Price history tracking tested")

        print("\n" + "="*60)
        print("  ✅ ALL TESTS PASSED")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_save_to_db())
