"""
Subprocess entry point for running scrapers.

This script is executed in a separate process to run a single scraper.
It uses asyncio.run() which provides a clean event loop that works with Playwright.
"""
import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path so we can import from services
sys.path.insert(0, str(Path(__file__).parent))

from database import SessionLocal
from services.scraper_runner import ScraperRunner

# Import all scrapers to trigger self-registration via decorators
# This must happen before any scraper execution — keep in sync with main.py
from services.scrapers.playwright_scraper import (  # noqa: F401
    WholesomeCoScraper,
)
from services.scrapers.curaleaf_scraper import (  # noqa: F401
    CuraleafScraper,
    CuraleafProvoScraper,
    CuraleafSpringvilleScraper,
    CuraleafPaysonScraper,
)
from services.scrapers.beehive_farmacy_scraper import (  # noqa: F401
    BeehiveFarmacyBrighamScraper,
    BeehiveFarmacySLCScraper,
)
from services.scrapers.zion_medicinal_scraper import ZionMedicinalScraper  # noqa: F401
from services.scrapers.dragonfly_wellness_scraper import DragonFlyWellnessSLCScraper  # noqa: F401
from services.scrapers.bloc_pharmacy_scraper import (  # noqa: F401
    BlocPharmacySouthJordanScraper,
    BlocPharmacyStGeorgeScraper,
)
from services.scrapers.flower_shop_scraper import (  # noqa: F401
    FlowerShopLoganScraper,
    FlowerShopOgdenScraper,
)
from services.scrapers.the_forest_scraper import TheForestMurrayScraper  # noqa: F401
from services.scrapers.dragonfly_price_scraper import DragonFlyWellnessPriceScraper  # noqa: F401
from services.scrapers.curaleaf_park_city_scraper import CuraleafParkCityScraper  # noqa: F401

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_scraper(scraper_id: str):
    """
    Run a scraper with its own database session.

    Args:
        scraper_id: The scraper ID to run

    Returns:
        dict with scraper results
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting scraper: {scraper_id}")

        runner = ScraperRunner(db, triggered_by="subprocess")
        result = await runner.run_by_id(scraper_id)

        logger.info(f"Scraper '{scraper_id}' completed: {result.get('status')}")
        logger.info(f"Products found: {result.get('products_found', 0)}")
        logger.info(f"Products processed: {result.get('products_processed', 0)}")

        return result

    except Exception as e:
        logger.error(f"Scraper '{scraper_id}' failed: {e}", exc_info=True)
        raise

    finally:
        db.close()
        logger.info(f"Database session closed for scraper '{scraper_id}'")


def main():
    """Main entry point for subprocess scraper execution."""
    if len(sys.argv) < 2:
        logger.error("Usage: python run_scraper_subprocess.py <scraper_id>")
        sys.exit(1)

    scraper_id = sys.argv[1]

    try:
        # Run the scraper using asyncio.run() which provides a clean event loop
        result = asyncio.run(run_scraper(scraper_id))

        # Exit with success
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error running scraper '{scraper_id}': {e}", exc_info=True)
        # Exit with error code
        sys.exit(1)


if __name__ == "__main__":
    main()
