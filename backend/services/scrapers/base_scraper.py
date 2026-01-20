"""
Abstract base class for all dispensary scrapers.

All scrapers must implement:
- scrape_products(): Fetch current inventory
- scrape_promotions(): Fetch current promotions

Usage:
    class MyDispensaryScraper(BaseScraper):
        async def scrape_products(self) -> List[ScrapedProduct]:
            ...
        async def scrape_promotions(self) -> List[ScrapedPromotion]:
            ...

    scraper = MyDispensaryScraper("dispensary-uuid")
    result = await scraper.run()
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class ScrapedProduct:
    """Standard product data structure from scraping"""
    name: str
    brand: str
    category: str  # "Flower", "Vape", "Edible", "Concentrate", "Topical"
    price: float
    in_stock: bool = True
    thc_percentage: Optional[float] = None
    cbd_percentage: Optional[float] = None
    batch_number: Optional[str] = None
    cultivation_date: Optional[datetime] = None
    weight: Optional[str] = None  # e.g., "1g", "3.5g", "1oz"
    raw_data: Dict[str, Any] = field(default_factory=dict)  # Original scraped data


@dataclass
class ScrapedPromotion:
    """Standard promotion data structure from scraping"""
    title: str
    start_date: datetime
    description: Optional[str] = None
    discount_percentage: Optional[float] = None  # 0-100
    discount_amount: Optional[float] = None  # Fixed $ amount
    applies_to: Optional[str] = None  # Category name or "all"
    product_id: Optional[str] = None  # Specific product if applicable
    end_date: Optional[datetime] = None
    is_recurring: bool = False
    recurring_day: Optional[str] = None  # "monday", "friday", etc.


class BaseScraper(ABC):
    """
    Base class for all dispensary scrapers.

    Subclasses must implement scrape_products() and scrape_promotions().
    """

    def __init__(
        self,
        dispensary_id: str,
        logger: Optional[logging.Logger] = None
    ):
        self.dispensary_id = dispensary_id
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._last_run: Optional[datetime] = None
        self._last_result: Optional[Dict] = None

    @property
    def name(self) -> str:
        """Human-readable scraper name"""
        return self.__class__.__name__

    @abstractmethod
    async def scrape_products(self) -> List[ScrapedProduct]:
        """
        Scrape current inventory from dispensary.

        Returns:
            List of ScrapedProduct objects representing current inventory
        """
        pass

    @abstractmethod
    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """
        Scrape current promotions from dispensary.

        Returns:
            List of ScrapedPromotion objects representing active promotions
        """
        pass

    async def run(self) -> Dict[str, Any]:
        """
        Execute full scrape and return results.

        Returns:
            Dict containing:
                - dispensary_id: str
                - products: List[ScrapedProduct]
                - promotions: List[ScrapedPromotion]
                - scraped_at: datetime
                - status: "success" | "error"
                - error: Optional error message
        """
        start_time = datetime.utcnow()
        self.logger.info(f"Starting scrape for {self.name}")

        try:
            products = await self.scrape_products()
            promotions = await self.scrape_promotions()

            self._last_run = datetime.utcnow()
            duration = (self._last_run - start_time).total_seconds()

            self.logger.info(
                f"Scraped {len(products)} products, {len(promotions)} promotions "
                f"in {duration:.2f}s"
            )

            self._last_result = {
                "dispensary_id": self.dispensary_id,
                "products": products,
                "promotions": promotions,
                "scraped_at": self._last_run,
                "duration_seconds": duration,
                "status": "success"
            }
            return self._last_result

        except Exception as e:
            self.logger.error(f"Scrape failed: {e}", exc_info=True)
            self._last_result = {
                "dispensary_id": self.dispensary_id,
                "products": [],
                "promotions": [],
                "scraped_at": datetime.utcnow(),
                "status": "error",
                "error": str(e)
            }
            return self._last_result

    async def run_with_retries(
        self,
        max_retries: int = 3,
        initial_delay: float = 5.0
    ) -> Dict[str, Any]:
        """
        Execute scrape with retry logic and exponential backoff.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries (seconds)

        Returns:
            Same as run() but with additional 'attempts' field on error
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                result = await self.run()
                if result["status"] == "success":
                    if attempt > 0:
                        self.logger.info(f"Succeeded on attempt {attempt + 1}")
                    return result
                last_error = result.get("error", "Unknown error")
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")

            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff
                self.logger.info(f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)

        self.logger.error(f"All {max_retries} attempts failed")
        return {
            "dispensary_id": self.dispensary_id,
            "products": [],
            "promotions": [],
            "scraped_at": datetime.utcnow(),
            "status": "error",
            "error": last_error,
            "attempts": max_retries
        }

    def get_last_run(self) -> Optional[datetime]:
        """Get timestamp of last successful run"""
        return self._last_run

    def get_last_result(self) -> Optional[Dict]:
        """Get result of last run"""
        return self._last_result
