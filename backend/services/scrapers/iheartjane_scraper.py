"""
iHeartJane API scraper for dispensaries using their menu platform

Used by: WholesomeCo, Beehive Farmacy, and other iHeartJane-powered dispensaries
"""
import aiohttp
import logging
import re
from typing import List, Optional
from .base_scraper import BaseScraper, ScrapedProduct
from .registry import register_scraper

logger = logging.getLogger(__name__)


@register_scraper(
    id="iheartjane",
    name="iHeartJane API (Generic)",
    dispensary_name="iHeartJane Store",
    dispensary_location="Utah",
    schedule_minutes=120,
    description="Generic iHeartJane API scraper - requires store_id configuration"
)
class IHeartJaneScraper(BaseScraper):
    """
    Scrapes iHeartJane-powered dispensaries via their public API

    iHeartJane provides menu management for many dispensaries with a consistent API.
    This scraper works for any dispensary using the iHeartJane platform.
    """

    BASE_URL = "https://api.iheartjane.com/v1"
    HEADERS = {
        "User-Agent": "UtahCannabisAggregator/1.0 (+https://utahcannabis.example.com/about)",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    def __init__(
        self,
        dispensary_id: str = "iheartjane",
        store_id: Optional[str] = None,
        dispensary_name: str = "iHeartJane Store"
    ):
        """
        Initialize scraper for specific iHeartJane store

        Args:
            dispensary_id: Unique ID for this scraper instance
            store_id: The iHeartJane store identifier (found via API inspection)
            dispensary_name: Human-readable name for logging (e.g., "WholesomeCo")
        """
        super().__init__(dispensary_id=dispensary_id)
        self.store_id = store_id
        self.dispensary_name = dispensary_name
        logger.info(f"Initialized iHeartJane scraper for {dispensary_name} (store_id: {store_id})")

    async def scrape_products(self) -> List[ScrapedProduct]:
        """
        Fetch products from iHeartJane API

        Returns:
            List of ScrapedProduct objects

        Raises:
            aiohttp.ClientError: On network errors
        """
        products = []
        url = f"{self.BASE_URL}/stores/{self.store_id}/products"

        logger.info(f"Scraping {self.dispensary_name} from {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.HEADERS,
                    timeout=aiohttp.ClientTimeout(total=self.TIMEOUT.total_seconds())
                ) as response:
                    # Check HTTP status
                    if response.status != 200:
                        logger.error(
                            f"Failed to fetch {self.dispensary_name}: "
                            f"HTTP {response.status}"
                        )
                        return products

                    # Parse JSON response
                    data = await response.json()

                    # iHeartJane API may use different keys for product list
                    product_list = (
                        data.get("products") or
                        data.get("items") or
                        data.get("menu") or
                        []
                    )

                    # Parse each product
                    for item in product_list:
                        try:
                            product = self._parse_product(item)
                            if product and product.name:  # Skip invalid products
                                products.append(product)
                        except Exception as e:
                            logger.warning(
                                f"Failed to parse product in {self.dispensary_name}: {e}",
                                exc_info=True
                            )
                            continue

                    logger.info(
                        f"Successfully scraped {len(products)} products "
                        f"from {self.dispensary_name}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Network error scraping {self.dispensary_name}: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error scraping {self.dispensary_name}: {e}",
                exc_info=True
            )

        return products

    def _parse_product(self, item: dict) -> Optional[ScrapedProduct]:
        """
        Parse iHeartJane product JSON into ScrapedProduct

        Args:
            item: Raw product dict from iHeartJane API

        Returns:
            ScrapedProduct or None if parsing fails
        """
        # Extract brand (may be nested object or simple string)
        brand = self._extract_brand(item)

        # Extract THC/CBD percentages
        thc = self._extract_percentage(item.get("potency_thc"))
        cbd = self._extract_percentage(item.get("potency_cbd"))

        # Map category to our product types
        category = item.get("category") or item.get("kind") or item.get("type") or ""
        product_type = self._map_category(category)

        # Extract price (try multiple possible fields)
        price = (
            item.get("price") or
            item.get("price_each") or
            item.get("unit_price") or
            0
        )

        # Get product name
        name = item.get("name") or item.get("title") or ""

        # Stock status
        in_stock = item.get("in_stock", True)
        if "inventory" in item:
            in_stock = item["inventory"] > 0

        return ScrapedProduct(
            name=name,
            brand=brand,
            category=product_type,
            thc_percentage=thc,
            cbd_percentage=cbd,
            price=float(price),
            in_stock=in_stock,
            weight=self._extract_unit_size(name),
            raw_data=item  # Preserve original for debugging
        )

    def _extract_brand(self, item: dict) -> Optional[str]:
        """Extract brand name from various iHeartJane formats"""
        # Format 1: Nested object
        if "brand" in item and isinstance(item["brand"], dict):
            return item["brand"].get("name")

        # Format 2: Simple string
        if "brand" in item and isinstance(item["brand"], str):
            return item["brand"]

        # Format 3: Separate field
        if "brand_name" in item:
            return item["brand_name"]

        # Format 4: Manufacturer field
        if "manufacturer" in item:
            if isinstance(item["manufacturer"], dict):
                return item["manufacturer"].get("name")
            return item["manufacturer"]

        return None

    def _extract_percentage(self, potency_data) -> Optional[float]:
        """
        Extract percentage from various iHeartJane potency formats

        Handles:
        - Dict: {"value": 22.5, "unit": "%"}
        - String: "22.5%"
        - Number: 22.5
        - None/missing data

        Args:
            potency_data: Potency data in various formats

        Returns:
            Float percentage or None
        """
        if potency_data is None:
            return None

        # Handle dict format (most common)
        if isinstance(potency_data, dict):
            value = potency_data.get("value") or potency_data.get("percentage")
            if value is not None:
                return float(value)

        # Handle string format
        if isinstance(potency_data, str):
            # Remove % and any whitespace, convert to float
            cleaned = potency_data.replace("%", "").strip()
            if cleaned:
                try:
                    return float(cleaned)
                except ValueError:
                    pass

        # Handle direct number
        try:
            return float(potency_data)
        except (ValueError, TypeError):
            return None

    def _map_category(self, category: str) -> str:
        """
        Map iHeartJane categories to our standardized product types

        Args:
            category: Category from iHeartJane API

        Returns:
            Standardized product type string
        """
        if not category:
            return "other"

        category_lower = category.lower()

        category_map = {
            "flower": "flower",
            "flowers": "flower",
            "bud": "flower",
            "buds": "flower",

            "pre-roll": "pre-roll",
            "pre-rolls": "pre-roll",
            "preroll": "pre-roll",
            "prerolls": "pre-roll",
            "joint": "pre-roll",
            "joints": "pre-roll",

            "vape": "vaporizer",
            "vapes": "vaporizer",
            "vaporizer": "vaporizer",
            "vaporizers": "vaporizer",
            "cartridge": "vaporizer",
            "cartridges": "vaporizer",
            "cart": "vaporizer",
            "carts": "vaporizer",

            "concentrate": "concentrate",
            "concentrates": "concentrate",
            "extract": "concentrate",
            "extracts": "concentrate",
            "wax": "concentrate",
            "shatter": "concentrate",
            "live resin": "concentrate",

            "edible": "edible",
            "edibles": "edible",
            "gummy": "edible",
            "gummies": "edible",
            "chocolate": "edible",

            "topical": "topical",
            "topicals": "topical",
            "lotion": "topical",
            "cream": "topical",
            "balm": "topical",

            "tincture": "tincture",
            "tinctures": "tincture",
            "oil": "tincture",
            "oils": "tincture",
        }

        return category_map.get(category_lower, "other")

    def _extract_unit_size(self, name: str) -> Optional[str]:
        """
        Extract unit size from product name

        Examples:
        - "Blue Dream 3.5g" → "3.5g"
        - "Gummies 100mg" → "100mg"
        - "Cartridge 1.0ml" → "1.0ml"

        Args:
            name: Product name

        Returns:
            Unit size string or None
        """
        if not name:
            return None

        # Pattern: number (decimal optional) + unit (g, oz, mg, ml)
        match = re.search(r'(\d+\.?\d*)\s*(g|oz|mg|ml|gram|ounce)\b', name, re.IGNORECASE)

        if match:
            value = match.group(1)
            unit = match.group(2).lower()

            # Normalize units
            if unit == "gram":
                unit = "g"
            elif unit == "ounce":
                unit = "oz"

            return f"{value}{unit}"

        return None


# Factory functions for easy instantiation

def create_wholesomeco_scraper() -> IHeartJaneScraper:
    """
    Create scraper for WholesomeCo

    TODO: Replace WHOLESOMECO_STORE_ID with actual ID from API inspection
          See FIND_IHEARTJANE_API.md for instructions
    """
    return IHeartJaneScraper(
        store_id="WHOLESOMECO_STORE_ID",  # TODO: Fill this in!
        dispensary_name="WholesomeCo"
    )


def create_beehive_scraper() -> IHeartJaneScraper:
    """
    Create scraper for Beehive Farmacy

    TODO: Replace BEEHIVE_STORE_ID with actual ID from API inspection
          See FIND_IHEARTJANE_API.md for instructions
    """
    return IHeartJaneScraper(
        store_id="BEEHIVE_STORE_ID",  # TODO: Fill this in!
        dispensary_name="Beehive Farmacy"
    )
