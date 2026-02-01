"""
Quick test to verify Curaleaf scraper product count.

Run with: python test_scraper_count.py
"""
import asyncio
import logging
from services.scrapers.curaleaf_scraper import CuraleafScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_scraper():
    """Test the Curaleaf scraper and count products"""

    # Test Lehi location
    scraper = CuraleafScraper(dispensary_id="curaleaf-lehi", location="lehi")
    scraper.headless = True  # Run headless for speed

    logger.info("Starting Curaleaf Lehi scraper test...")
    products = await scraper.scrape_products()

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"TOTAL PRODUCTS SCRAPED: {len(products)}")
    logger.info("=" * 60)

    # Count by category
    categories = {}
    for p in products:
        cat = p.category or "unknown"
        categories[cat] = categories.get(cat, 0) + 1

    logger.info("Products by category:")
    for cat, count in sorted(categories.items()):
        logger.info(f"  {cat}: {count}")

    # Show sample products
    logger.info("")
    logger.info("Sample products (first 5):")
    for i, p in enumerate(products[:5]):
        logger.info(f"  {i+1}. {p.name} - ${p.price} ({p.category})")

    return len(products)


if __name__ == "__main__":
    count = asyncio.run(test_scraper())

    if count >= 150:
        logger.info("")
        logger.info("SUCCESS: Product count looks good!")
    elif count >= 50:
        logger.info("")
        logger.warning(f"IMPROVED: {count} products is better than before, but still low.")
    else:
        logger.error("")
        logger.error(f"FAILED: Only {count} products found. Issue may persist.")
