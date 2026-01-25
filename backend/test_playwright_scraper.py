"""
Test script for Playwright-based scrapers

Scrapes real product data from WholesomeCo and Beehive Pharmacy websites
using browser automation (Playwright).

Usage:
    python test_playwright_scraper.py [--headless] [--site wholesomeco|beehive]

Options:
    --headless      Run browser without visual (default: True)
    --headed        Show browser window while scraping
    --site          Only scrape specific site (default: both)
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.scrapers.playwright_scraper import (
    WholesomeCoScraper,
    BeehiveScraper
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_wholesomeco(headless=True):
    """Test WholesomeCo scraper"""
    print("\n" + "="*60)
    print("Testing WholesomeCo Scraper")
    print("="*60 + "\n")

    try:
        scraper = WholesomeCoScraper()
        products = await scraper.scrape_products()

        print(f"[SUCCESS] Successfully scraped {len(products)} products\n")

        if products:
            print("Sample Products:\n")
            for i, product in enumerate(products[:5], 1):
                print(f"{i}. {product.name}")
                if product.brand:
                    print(f"   Brand: {product.brand}")
                if product.price:
                    print(f"   Price: ${product.price:.2f}")
                if product.thc_percentage:
                    print(f"   THC: {product.thc_percentage}%")
                print(f"   In Stock: {'Yes' if product.in_stock else 'No'}")
                print()

            # Statistics
            print(f"\n[STATS] Statistics:")
            print(f"   Total products: {len(products)}")

            # By type
            types = {}
            for p in products:
                types[p.product_type] = types.get(p.product_type, 0) + 1
            if types:
                print(f"   By Type: {types}")

            # Price range
            prices = [p.price for p in products if p.price > 0]
            if prices:
                print(f"   Price Range: ${min(prices):.2f} - ${max(prices):.2f}")

        else:
            print("[WARNING] No products found")
            print("   The site structure may have changed or products didn't load")
            print("   Try running with --headed to see what's happening")

        return len(products)

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def test_beehive(headless=True):
    """Test Beehive scraper"""
    print("\n" + "="*60)
    print("Testing Beehive Pharmacy Scraper")
    print("="*60 + "\n")

    try:
        scraper = BeehiveScraper()
        products = await scraper.scrape_products()

        print(f"[SUCCESS] Successfully scraped {len(products)} products\n")

        if products:
            print("Sample Products:\n")
            for i, product in enumerate(products[:5], 1):
                print(f"{i}. {product.name}")
                if product.brand:
                    print(f"   Brand: {product.brand}")
                if product.price:
                    print(f"   Price: ${product.price:.2f}")
                if product.thc_percentage:
                    print(f"   THC: {product.thc_percentage}%")
                print(f"   In Stock: {'Yes' if product.in_stock else 'No'}")
                print()

            # Statistics
            print(f"\n[STATS] Statistics:")
            print(f"   Total products: {len(products)}")

            # By type
            types = {}
            for p in products:
                types[p.product_type] = types.get(p.product_type, 0) + 1
            if types:
                print(f"   By Type: {types}")

            # Price range
            prices = [p.price for p in products if p.price > 0]
            if prices:
                print(f"   Price Range: ${min(prices):.2f} - ${max(prices):.2f}")

        else:
            print("[WARNING] No products found")
            print("   The site structure may have changed or products didn't load")
            print("   Try running with --headed to see what's happening")

        return len(products)

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def main():
    """Main test function"""
    print("\n" + "="*60)
    print("Playwright-Based Dispensary Scraper Test")
    print("="*60)

    # Parse arguments
    headless = "--headed" not in sys.argv
    site = None

    if "--site" in sys.argv:
        idx = sys.argv.index("--site")
        if idx + 1 < len(sys.argv):
            site = sys.argv[idx + 1]

    # Run tests
    total_products = 0

    if site != "beehive":
        try:
            wholesomeco_count = await test_wholesomeco(headless=headless)
            total_products += wholesomeco_count
        except Exception as e:
            logger.error(f"WholesomeCo test failed: {e}")

    if site != "wholesomeco":
        try:
            beehive_count = await test_beehive(headless=headless)
            total_products += beehive_count
        except Exception as e:
            logger.error(f"Beehive test failed: {e}")

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Total products scraped: {total_products}")

    if total_products > 0:
        print("[SUCCESS] Scraping successful! Products can now be saved to database.")
    else:
        print("[ERROR] No products found. Troubleshooting tips:")
        print("   1. Run with --headed to see what's happening in the browser")
        print("   2. Check that websites are accessible")
        print("   3. Site structure may have changed - check selectors")
        print("   4. Network requests may be failing - check connection")

    print("\n" + "="*60)


if __name__ == "__main__":
    # Show usage if needed
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    # Run tests
    asyncio.run(main())
