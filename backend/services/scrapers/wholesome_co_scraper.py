import json
import logging
import re
from typing import List, Optional, Any

import aiohttp
from bs4 import BeautifulSoup

from services.scrapers.base_scraper import BaseScraper, ScrapedProduct, ScrapedPromotion
from services.scrapers.registry import register_scraper

logger = logging.getLogger(__name__)

@register_scraper(
    id="wholesomeco-legacy",
    name="WholesomeCo (Legacy - Deprecated)",
    dispensary_name="WholesomeCo",
    dispensary_location="Bountiful, UT",
    schedule_minutes=120,
    enabled=False,  # Disabled in favor of Playwright version
    description="DEPRECATED: Direct scraping from WholesomeCo website via embedded JSON. Use wholesomeco (Playwright) instead."
)
class WholesomeCoScraper(BaseScraper):
    """
    Scrapes WholesomeCo website by parsing embedded RudderStack analytics JSON.
    """
    # Main shop URL - this usually loads the initial list of products
    SHOP_URL = "https://www.wholesome.co/shop"

    def __init__(self, dispensary_id: str = "wholesomeco"):
        """
        Initialize WholesomeCo scraper.

        Args:
            dispensary_id: Unique ID for this dispensary (default: "wholesomeco")
        """
        super().__init__(dispensary_id=dispensary_id)

    async def scrape_products(self) -> List[ScrapedProduct]:
        """Fetch and parse products from the HTML"""
        products = []

        try:
            async with aiohttp.ClientSession() as session:
                # Add headers to look like a real browser
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                
                logger.info(f"Fetching {self.SHOP_URL}...")
                async with session.get(self.SHOP_URL, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch: {response.status}")
                        return products

                    html = await response.text()

            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all analytics divs that contain the payload
            elements = soup.find_all('div', attrs={'data-analytics-rudderstack-payload-value': True})
            
            logger.info(f"Found {len(elements)} potential product elements")

            for element in elements:
                try:
                    # Extract JSON string
                    raw_json = element.get('data-analytics-rudderstack-payload-value')
                    if not raw_json:
                        continue
                        
                    data = json.loads(raw_json)
                    
                    # Verify it's a product by checking for required fields
                    if 'product_id' not in data or 'name' not in data:
                        continue

                    # Extract or construct product URL
                    product_url = data.get("url")
                    if not product_url and data.get("product_id"):
                        # Construct URL from product ID if not provided
                        product_url = f"https://www.wholesome.co/product/{data.get('product_id')}"

                    # Map to our schema
                    product = ScrapedProduct(
                        name=data.get("name"),
                        brand=data.get("brand"),
                        category=self._map_category(data.get("category") or data.get("categories")),
                        price=float(data.get("price", 0)),
                        # THC/CBD is not in this JSON, so we try to extract from name
                        thc_percentage=self._extract_percentage(data.get("name")),
                        cbd_percentage=None,
                        weight=data.get("variant") or self._extract_unit_size(data.get("name")),
                        url=product_url,
                        raw_data=data
                    )
                    products.append(product)

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Error parsing product: {e}")
                    continue

            logger.info(f"Successfully scraped {len(products)} products from WholesomeCo")

        except Exception as e:
            logger.error(f"Error scraping WholesomeCo: {e}")

        return products

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """
        Scrape current promotions from dispensary.
        Currently not implemented for WholesomeCo.
        """
        return []

    def _map_category(self, category_data: Any) -> str:
        """Map WholesomeCo categories to our standard types"""
        category_str = ""
        if isinstance(category_data, list):
            category_str = " ".join(category_data).lower()
        elif isinstance(category_data, str):
            category_str = category_data.lower()
            
        if "flower" in category_str: return "flower"
        if "vape" in category_str or "cartridge" in category_str: return "vaporizer"
        if "edible" in category_str or "gummy" in category_str: return "edible"
        if "pre-roll" in category_str or "preroll" in category_str: return "pre-roll"
        if "concentrate" in category_str or "wax" in category_str: return "concentrate"
        if "tincture" in category_str: return "tincture"
        if "topical" in category_str: return "topical"
        return "other"

    def _extract_unit_size(self, name: str) -> Optional[str]:
        """Extract unit size from name if variant is missing"""
        if not name: return None
        match = re.search(r'(\d+\.?\d*)\s*(g|oz|mg|ml)', name, re.IGNORECASE)
        return f"{match.group(1)}{match.group(2)}" if match else None

    def _extract_percentage(self, text: str) -> Optional[float]:
        """Try to extract THC percentage from text if present"""
        if not text: return None
        match = re.search(r'(\d+\.?\d*)\s*%', text)
        try:
            return float(match.group(1)) if match else None
        except ValueError:
            return None