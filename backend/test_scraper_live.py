import asyncio
import logging
import sys
import os

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend directory to path so we can import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.scrapers.wholesome_co_scraper import WholesomeCoScraper

# Configure logging to see scraper output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_scraper():
    # Initialize scraper with a dummy ID for testing
    scraper = WholesomeCoScraper(dispensary_id="test-wholesome-co")

    print(f"\n🧪 Starting Live Scrape Test for WholesomeCo...")
    print(f"Target URL: {scraper.SHOP_URL}\n")
    
    try:
        products = await scraper.scrape_products()
        
        print(f"\n✅ Scrape Complete!")
        print(f"Found {len(products)} products.")
        
        if products:
            print("\n--- Sample Data (First 3) ---")
            for i, p in enumerate(products[:3]):
                print(f"\nProduct #{i+1}:")
                print(f"  Name:     {p.name}")
                print(f"  Brand:    {p.brand}")
                print(f"  Category: {p.category}")
                print(f"  Price:    ${p.price}")
                if p.thc_percentage:
                    print(f"  THC:      {p.thc_percentage}%")
                print(f"  Weight:   {p.weight}")
                
    except Exception as e:
        print(f"\n❌ Error during scrape: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_scraper())