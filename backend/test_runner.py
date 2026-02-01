import asyncio
import logging
import main  # Import main to trigger scraper registration
from database import SessionLocal
from services.scraper_runner import ScraperRunner

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test():
    db = SessionLocal()
    runner = ScraperRunner(db, triggered_by='test')

    print("Running WholesomeCo scraper through ScraperRunner...")
    print("=" * 60)

    result = await runner.run_by_id('wholesomeco')

    print("\nResult:")
    print("=" * 60)
    for key, value in result.items():
        print(f"{key}: {value}")

    db.close()

asyncio.run(test())
