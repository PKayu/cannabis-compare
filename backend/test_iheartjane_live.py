"""
Live test script for iHeartJane scraper

Run this after finding store IDs to verify the scraper works.

Usage:
    python test_iheartjane_live.py
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.scrapers.iheartjane_scraper import (
    IHeartJaneScraper,
    create_wholesomeco_scraper,
    create_beehive_scraper
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_generic_store(store_id: str, dispensary_name: str):
    """Test scraping a specific iHeartJane store"""
    print(f"\n{'='*60}")
    print(f"Testing: {dispensary_name}")
    print(f"Store ID: {store_id}")
    print(f"{'='*60}\n")

    scraper = IHeartJaneScraper(store_id=store_id, dispensary_name=dispensary_name)

    try:
        products = await scraper.scrape_products()

        print(f"\n✅ Successfully scraped {len(products)} products\n")

        if products:
            # Show first 5 products
            print("Sample Products:\n")
            for i, product in enumerate(products[:5], 1):
                print(f"{i}. {product.name}")
                print(f"   Brand: {product.brand or 'N/A'}")
                print(f"   Type: {product.product_type}")
                print(f"   THC: {product.thc_percentage}%" if product.thc_percentage else "   THC: N/A")
                print(f"   Price: ${product.price:.2f}")
                print(f"   In Stock: {'Yes' if product.in_stock else 'No'}")
                print()

            # Statistics
            print("\n📊 Statistics:")
            print(f"   Total products: {len(products)}")

            # Product type breakdown
            types = {}
            for p in products:
                types[p.product_type] = types.get(p.product_type, 0) + 1

            print("\n   By Type:")
            for ptype, count in sorted(types.items(), key=lambda x: -x[1]):
                print(f"   - {ptype}: {count}")

            # Brand breakdown (top 5)
            brands = {}
            for p in products:
                if p.brand:
                    brands[p.brand] = brands.get(p.brand, 0) + 1

            if brands:
                print("\n   Top Brands:")
                for brand, count in sorted(brands.items(), key=lambda x: -x[1])[:5]:
                    print(f"   - {brand}: {count}")

            # Price range
            prices = [p.price for p in products if p.price > 0]
            if prices:
                print(f"\n   Price Range: ${min(prices):.2f} - ${max(prices):.2f}")
                print(f"   Average Price: ${sum(prices)/len(prices):.2f}")

        else:
            print("⚠️  No products found. This might mean:")
            print("   - Incorrect store ID")
            print("   - Store has no products")
            print("   - API structure changed")
            print("\n   Check the store ID and try again.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Troubleshooting:")
        print("   1. Verify the store ID is correct")
        print("   2. Check internet connection")
        print("   3. Verify iHeartJane API is accessible")


async def test_wholesomeco():
    """Test WholesomeCo scraper"""
    scraper = create_wholesomeco_scraper()

    if scraper.store_id == "WHOLESOMECO_STORE_ID":
        print("\n⚠️  WholesomeCo store ID not configured yet!")
        print("   Edit backend/services/scrapers/iheartjane_scraper.py")
        print("   Replace 'WHOLESOMECO_STORE_ID' with actual ID")
        print("\n   See FIND_IHEARTJANE_API.md for instructions")
        return

    products = await scraper.scrape_products()
    print(f"\nWholesomeCo: {len(products)} products")

    return products


async def test_beehive():
    """Test Beehive Farmacy scraper"""
    scraper = create_beehive_scraper()

    if scraper.store_id == "BEEHIVE_STORE_ID":
        print("\n⚠️  Beehive Farmacy store ID not configured yet!")
        print("   Edit backend/services/scrapers/iheartjane_scraper.py")
        print("   Replace 'BEEHIVE_STORE_ID' with actual ID")
        print("\n   See FIND_IHEARTJANE_API.md for instructions")
        return

    products = await scraper.scrape_products()
    print(f"\nBeehive Farmacy: {len(products)} products")

    return products


async def main():
    """Main test function"""
    print("\n" + "="*60)
    print("iHeartJane Scraper Test")
    print("="*60)

    # Test with custom store ID if provided
    if len(sys.argv) > 1:
        store_id = sys.argv[1]
        dispensary_name = sys.argv[2] if len(sys.argv) > 2 else "Custom Store"
        await test_generic_store(store_id, dispensary_name)

    # Test configured scrapers
    else:
        print("\n📝 Testing configured dispensaries...")
        print("   (Update store IDs in iheartjane_scraper.py first)")

        await test_wholesomeco()
        await test_beehive()

        print("\n" + "="*60)
        print("\n💡 To test a specific store ID:")
        print("   python test_iheartjane_live.py <STORE_ID> <DISPENSARY_NAME>")
        print("\nExample:")
        print("   python test_iheartjane_live.py 12345 \"Test Dispensary\"")


if __name__ == "__main__":
    asyncio.run(main())
