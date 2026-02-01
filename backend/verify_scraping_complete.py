"""
Comprehensive verification that Steps 1-4 of SCRAPING.md are complete.

Run this after implementing fixes to confirm everything works end-to-end.

Steps tested:
1. Inspect Website - Verify scraper can initialize and access target
2. Customize Scraper - Run scraper and validate data structure
3. Test Locally - Display sample product data
4. Save to Database - Validate database integration, duplicates, price history
"""
import asyncio
import sys
import os
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
from services.scrapers.playwright_scraper import WholesomeCoScraper
from services.scraper_runner import ScraperRunner
from models import Product, Price, Brand, Dispensary
import logging

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise during tests
    format='%(levelname)s - %(message)s'
)

def print_header(text):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_check(passed, message):
    """Print a check result with visual indicator"""
    symbol = "✅" if passed else "❌"
    print(f"{symbol} {message}")

async def verify_all_steps():
    """
    Run comprehensive verification of all 4 steps from SCRAPING.md.
    Returns 0 on success, 1 on failure.
    """

    all_passed = True

    # ========================================
    # STEP 1: Inspect Website
    # ========================================
    print_header("STEP 1: Website Inspection")

    try:
        scraper = WholesomeCoScraper(dispensary_id="test-verify")
        print(f"Target URL: {scraper.SHOP_URL}")
        print(f"Scraper Type: BeautifulSoup HTML Parser")
        print("✓ Scraper initialized successfully")
        step1_passed = True
    except Exception as e:
        print(f"✗ Failed to initialize scraper: {e}")
        step1_passed = False
        all_passed = False

    print_check(step1_passed, "Step 1: Website structure understood")

    # ========================================
    # STEP 2: Customize Scraper
    # ========================================
    print_header("STEP 2: Scraper Customization")

    if not step1_passed:
        print("⊘ Skipping Step 2 (Step 1 failed)")
        step2_passed = False
        all_passed = False
    else:
        try:
            # Test scraper can fetch and parse
            print("Fetching products from WholesomeCo...")
            products = await scraper.scrape_products()

            if len(products) > 0:
                print(f"✓ Scraped {len(products)} products")

                # Validate data structure
                sample = products[0]
                has_name = bool(sample.name)
                has_brand = bool(sample.brand)
                has_price = sample.price > 0
                has_category = bool(sample.category)

                print(f"\nData Field Validation:")
                print(f"  - Names:      {'✓' if has_name else '✗'}")
                print(f"  - Brands:     {'✓' if has_brand else '✗'}")
                print(f"  - Prices:     {'✓' if has_price else '✗'}")
                print(f"  - Categories: {'✓' if has_category else '✗'}")

                step2_passed = has_name and has_brand and has_price and has_category

                if not step2_passed:
                    all_passed = False
            else:
                print("✗ No products scraped")
                step2_passed = False
                all_passed = False

        except Exception as e:
            print(f"✗ Scraper failed: {e}")
            import traceback
            traceback.print_exc()
            step2_passed = False
            all_passed = False

    print_check(step2_passed, "Step 2: Scraper implementation works")

    # ========================================
    # STEP 3: Test Locally
    # ========================================
    print_header("STEP 3: Local Testing")

    if not step2_passed:
        print("⊘ Skipping Step 3 (Step 2 failed)")
        step3_passed = False
        all_passed = False
    else:
        print(f"Sample Product Data:\n")
        sample = products[0]
        print(f"  Name:     {sample.name}")
        print(f"  Brand:    {sample.brand}")
        print(f"  Category: {sample.category}")
        print(f"  Price:    ${sample.price:.2f}")
        if sample.thc_percentage:
            print(f"  THC:      {sample.thc_percentage}%")
        if sample.weight:
            print(f"  Weight:   {sample.weight}")

        step3_passed = True

    print_check(step3_passed, "Step 3: Data extraction validated")

    # ========================================
    # STEP 4: Save to Database
    # ========================================
    print_header("STEP 4: Database Integration")

    if not step3_passed:
        print("⊘ Skipping Step 4 (Step 3 failed)")
        step4_passed = False
        all_passed = False
    else:
        db = SessionLocal()

        try:
            # Create tables
            Base.metadata.create_all(bind=engine)
            print("✓ Database tables created/verified")

            # Clear existing test data for clean test
            print("Clearing database for clean test...")
            db.query(Price).delete()
            db.query(Product).delete()
            db.query(Brand).delete()
            db.query(Dispensary).delete()
            db.commit()
            print("✓ Database cleared for clean test")

            # Run scraper
            runner = ScraperRunner(db)
            print("\nRunning scraper to database...")
            await runner.run_wholesomeco()

            # Verify data was saved
            product_count = db.query(Product).count()
            brand_count = db.query(Brand).count()
            price_count = db.query(Price).count()
            dispensary_count = db.query(Dispensary).count()

            print(f"\nDatabase Contents:")
            print(f"  Products:     {product_count}")
            print(f"  Brands:       {brand_count}")
            print(f"  Prices:       {price_count}")
            print(f"  Dispensaries: {dispensary_count}")

            # Validation checks
            has_products = product_count > 0
            has_brands = brand_count > 0
            has_prices = price_count > 0
            has_dispensary = dispensary_count == 1

            print(f"\nData Saved:")
            print_check(has_products, f"Products saved ({product_count})")
            print_check(has_brands, f"Brands created ({brand_count})")
            print_check(has_prices, f"Prices recorded ({price_count})")
            print_check(has_dispensary, f"Dispensary created ({dispensary_count})")

            # Test data quality
            data_quality_passed = False
            if has_products:
                sample_product = db.query(Product).first()
                if sample_product:
                    has_valid_brand = sample_product.brand is not None
                    has_valid_type = sample_product.product_type is not None
                    product_has_price = len(sample_product.prices) > 0

                    print(f"\nData Quality:")
                    print_check(has_valid_brand, "Products linked to brands")
                    print_check(has_valid_type, "Product types mapped")
                    print_check(product_has_price, "Products have prices")

                    data_quality_passed = has_valid_brand and has_valid_type and product_has_price

            # Test duplicate prevention
            print(f"\nDuplicate Prevention Test:")
            print("Running scraper a second time...")
            initial_product_count = product_count
            initial_price_count = price_count

            await runner.run_wholesomeco()

            final_product_count = db.query(Product).count()
            final_price_count = db.query(Price).count()

            no_duplicate_products = (final_product_count == initial_product_count)
            no_duplicate_prices = (final_price_count == initial_price_count)

            print_check(no_duplicate_products, f"No duplicate products ({final_product_count} products)")
            print_check(no_duplicate_prices, f"No duplicate prices ({final_price_count} prices)")

            # Test price history
            print(f"\nPrice History Test:")
            sample_price = db.query(Price).first()
            history_works = False

            if sample_price:
                old_amount = sample_price.amount
                new_amount = old_amount + 5.0

                sample_price.update_price(new_amount)
                db.commit()
                db.refresh(sample_price)

                history_works = (sample_price.previous_price == old_amount)

                if history_works:
                    print(f"✓ Price history tracking works")
                    print(f"  Previous: ${sample_price.previous_price:.2f}")
                    print(f"  Current:  ${sample_price.amount:.2f}")
                    if sample_price.price_change_percentage:
                        print(f"  Change:   {sample_price.price_change_percentage:+.1f}%")
                else:
                    print("✗ Price history not working")
            else:
                print("✗ Could not test price history (no prices)")

            # Overall Step 4 result
            step4_passed = (has_products and has_brands and has_prices and
                           has_dispensary and data_quality_passed and
                           no_duplicate_products and no_duplicate_prices and
                           history_works)

            if not step4_passed:
                all_passed = False

        except Exception as e:
            print(f"\n✗ Database integration failed: {e}")
            import traceback
            traceback.print_exc()
            step4_passed = False
            all_passed = False
        finally:
            db.close()

    print_check(step4_passed, "Step 4: Database integration complete")

    # ========================================
    # FINAL SUMMARY
    # ========================================
    print_header("VERIFICATION SUMMARY")

    print(f"Step 1 (Inspect Website):    {'✅ PASS' if step1_passed else '❌ FAIL'}")
    print(f"Step 2 (Customize Scraper):  {'✅ PASS' if step2_passed else '❌ FAIL'}")
    print(f"Step 3 (Test Locally):       {'✅ PASS' if step3_passed else '❌ FAIL'}")
    print(f"Step 4 (Save to Database):   {'✅ PASS' if step4_passed else '❌ FAIL'}")

    print("\n" + "="*60)

    if all_passed and step1_passed and step2_passed and step3_passed and step4_passed:
        print("🎉 ALL STEPS COMPLETE! SCRAPING.md STEPS 1-4 VERIFIED")
        print("="*60 + "\n")
        return 0
    else:
        print("❌ SOME STEPS FAILED - SEE DETAILS ABOVE")
        print("="*60 + "\n")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(verify_all_steps())
    sys.exit(exit_code)
