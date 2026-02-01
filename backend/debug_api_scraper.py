"""
Debug script to test scraper in the same way the API does.

This simulates the exact call path that the admin API uses.
"""
import asyncio
import logging
from database import SessionLocal
from services.scraper_runner import ScraperRunner
from services.scrapers.registry import ScraperRegistry

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_api_context():
    """Test scraper exactly as the API endpoint does"""

    # Show all registered scrapers
    all_scrapers = ScraperRegistry.get_all()
    logger.info(f"Registered scrapers: {list(all_scrapers.keys())}")

    # Show details for wholesomeco
    config = ScraperRegistry.get("wholesomeco")
    if config:
        logger.info(f"wholesomeco config:")
        logger.info(f"  - name: {config.name}")
        logger.info(f"  - enabled: {config.enabled}")
        logger.info(f"  - class: {config.scraper_class}")
        logger.info(f"  - module: {config.scraper_class.__module__}")

        # Try to instantiate directly
        logger.info("\n=== Direct instantiation test ===")
        try:
            scraper = config.scraper_class(dispensary_id="wholesomeco")
            logger.info(f"Scraper instantiated: {scraper}")
            logger.info(f"Scraper type: {type(scraper)}")
            logger.info(f"Headless mode: {getattr(scraper, 'headless', 'N/A')}")

            # Test the scrape_products method directly
            logger.info("\n=== Direct scrape_products call ===")
            products = await scraper.scrape_products()
            logger.info(f"Direct call returned: {len(products)} products")

        except Exception as e:
            logger.error(f"Direct instantiation failed: {e}", exc_info=True)

    # Now test via ScraperRunner (same as API)
    logger.info("\n=== ScraperRunner test (same as API) ===")
    db = SessionLocal()
    try:
        runner = ScraperRunner(db, triggered_by="debug-test")
        logger.info(f"ScraperRunner created: {runner}")

        result = await runner.run_by_id("wholesomeco")
        logger.info(f"ScraperRunner result: {result}")

    except Exception as e:
        logger.error(f"ScraperRunner failed: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_api_context())
