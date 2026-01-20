"""
Scraper for WholesomeCo Utah dispensary.

WholesomeCo is one of Utah's licensed medical cannabis pharmacies.
This scraper fetches their current inventory and promotions.

Note: This is a template implementation. Actual scraping logic
will need to be adapted based on the dispensary's actual website/API structure.
"""
import aiohttp
import logging
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import re

from services.scrapers.base_scraper import BaseScraper, ScrapedProduct, ScrapedPromotion

logger = logging.getLogger(__name__)


class WholesomeCoScraper(BaseScraper):
    """
    Scrapes WholesomeCo menu and promotions.

    WholesomeCo may use iHeartJane or a custom menu system.
    This implementation provides the structure for scraping their data.
    """

    BASE_URL = "https://www.wholesomeco.com"
    MENU_ENDPOINT = "/api/menu"  # Placeholder - actual endpoint TBD
    PROMOTIONS_ENDPOINT = "/specials"

    # Request configuration
    TIMEOUT = 30
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; UtahCannabisAggregator/1.0)",
        "Accept": "application/json, text/html",
    }

    async def scrape_products(self) -> List[ScrapedProduct]:
        """
        Scrape WholesomeCo inventory.

        Returns list of products currently available.
        """
        products = []

        try:
            async with aiohttp.ClientSession() as session:
                # First try JSON API endpoint
                products = await self._scrape_json_menu(session)

                # If no products from API, try HTML scraping
                if not products:
                    products = await self._scrape_html_menu(session)

                self.logger.info(
                    f"Scraped {len(products)} products from WholesomeCo"
                )

        except aiohttp.ClientError as e:
            self.logger.error(f"Network error scraping WholesomeCo menu: {e}")
        except Exception as e:
            self.logger.error(f"Failed to scrape WholesomeCo menu: {e}")

        return products

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """
        Scrape WholesomeCo promotions and daily deals.

        Returns list of active promotions including recurring deals.
        """
        promotions = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}{self.PROMOTIONS_ENDPOINT}",
                    headers=self.HEADERS,
                    timeout=aiohttp.ClientTimeout(total=self.TIMEOUT)
                ) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        promotions = self._parse_promotions_html(html)
                        self.logger.info(
                            f"Scraped {len(promotions)} promotions from WholesomeCo"
                        )
                    else:
                        self.logger.warning(
                            f"Promotions page returned status {resp.status}"
                        )

        except aiohttp.ClientError as e:
            self.logger.error(f"Network error scraping WholesomeCo promotions: {e}")
        except Exception as e:
            self.logger.error(f"Failed to scrape WholesomeCo promotions: {e}")

        return promotions

    async def _scrape_json_menu(
        self,
        session: aiohttp.ClientSession
    ) -> List[ScrapedProduct]:
        """Try to scrape menu from JSON API"""
        try:
            async with session.get(
                f"{self.BASE_URL}{self.MENU_ENDPOINT}",
                headers=self.HEADERS,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self._parse_json_menu(data)
        except aiohttp.ContentTypeError:
            # Not JSON, try HTML
            pass
        except Exception as e:
            self.logger.debug(f"JSON menu endpoint not available: {e}")

        return []

    async def _scrape_html_menu(
        self,
        session: aiohttp.ClientSession
    ) -> List[ScrapedProduct]:
        """Fallback to HTML scraping if JSON API not available"""
        try:
            async with session.get(
                f"{self.BASE_URL}/menu",
                headers=self.HEADERS,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT)
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    return self._parse_html_menu(html)
        except Exception as e:
            self.logger.error(f"HTML menu scraping failed: {e}")

        return []

    def _parse_json_menu(self, data: dict) -> List[ScrapedProduct]:
        """
        Parse menu from JSON response.

        Expected structure varies by menu provider (iHeartJane, Dutchie, etc.)
        This is a template that should be adapted to actual API response.
        """
        products = []

        # Try common JSON structures
        items = data.get("items", data.get("products", data.get("menu", [])))

        for item in items:
            try:
                product = ScrapedProduct(
                    name=item.get("name", item.get("product_name", "")),
                    brand=item.get("brand", item.get("brand_name", "Unknown")),
                    category=self._normalize_category(
                        item.get("category", item.get("product_type", "Other"))
                    ),
                    price=float(item.get("price", item.get("retail_price", 0))),
                    in_stock=item.get("in_stock", item.get("available", True)),
                    thc_percentage=self._parse_percentage(
                        item.get("thc", item.get("thc_percentage"))
                    ),
                    cbd_percentage=self._parse_percentage(
                        item.get("cbd", item.get("cbd_percentage"))
                    ),
                    batch_number=item.get("batch_id", item.get("batch_number")),
                    weight=item.get("weight", item.get("size")),
                    raw_data=item
                )

                if product.name and product.price > 0:
                    products.append(product)

            except Exception as e:
                self.logger.warning(f"Failed to parse product: {e}")

        return products

    def _parse_html_menu(self, html: str) -> List[ScrapedProduct]:
        """
        Parse menu from HTML page.

        This is a template - actual selectors depend on page structure.
        """
        products = []
        soup = BeautifulSoup(html, "html.parser")

        # Common product card selectors to try
        product_selectors = [
            ".product-card",
            ".menu-item",
            "[data-product]",
            ".product-tile"
        ]

        for selector in product_selectors:
            product_elements = soup.select(selector)
            if product_elements:
                for elem in product_elements:
                    try:
                        product = self._extract_product_from_element(elem)
                        if product:
                            products.append(product)
                    except Exception as e:
                        self.logger.warning(f"Failed to extract product: {e}")
                break

        return products

    def _extract_product_from_element(
        self,
        elem: BeautifulSoup
    ) -> Optional[ScrapedProduct]:
        """Extract product data from an HTML element"""
        # Name
        name_elem = (
            elem.select_one(".product-name") or
            elem.select_one("h3") or
            elem.select_one(".title")
        )
        name = name_elem.text.strip() if name_elem else None

        if not name:
            return None

        # Brand
        brand_elem = (
            elem.select_one(".brand") or
            elem.select_one(".brand-name")
        )
        brand = brand_elem.text.strip() if brand_elem else "Unknown"

        # Price
        price_elem = (
            elem.select_one(".price") or
            elem.select_one(".product-price")
        )
        price_text = price_elem.text.strip() if price_elem else "0"
        price = self._parse_price(price_text)

        # Category
        category_elem = (
            elem.select_one(".category") or
            elem.select_one(".product-type")
        )
        category = self._normalize_category(
            category_elem.text.strip() if category_elem else "Other"
        )

        # THC/CBD percentages
        thc = self._extract_percentage(elem, ["thc", "THC"])
        cbd = self._extract_percentage(elem, ["cbd", "CBD"])

        return ScrapedProduct(
            name=name,
            brand=brand,
            category=category,
            price=price,
            in_stock=True,  # Assume in-stock if listed
            thc_percentage=thc,
            cbd_percentage=cbd
        )

    def _parse_promotions_html(self, html: str) -> List[ScrapedPromotion]:
        """Parse promotions from HTML page"""
        promotions = []
        soup = BeautifulSoup(html, "html.parser")

        # Try common promotion container selectors
        promo_selectors = [
            ".promotion",
            ".deal",
            ".special",
            ".promo-card"
        ]

        for selector in promo_selectors:
            promo_elements = soup.select(selector)
            if promo_elements:
                for elem in promo_elements:
                    try:
                        promo = self._extract_promotion_from_element(elem)
                        if promo:
                            promotions.append(promo)
                    except Exception as e:
                        self.logger.warning(f"Failed to extract promotion: {e}")
                break

        return promotions

    def _extract_promotion_from_element(
        self,
        elem: BeautifulSoup
    ) -> Optional[ScrapedPromotion]:
        """Extract promotion data from an HTML element"""
        # Title
        title_elem = (
            elem.select_one("h3") or
            elem.select_one(".promo-title") or
            elem.select_one(".title")
        )
        title = title_elem.text.strip() if title_elem else None

        if not title:
            return None

        # Description
        desc_elem = (
            elem.select_one("p") or
            elem.select_one(".description")
        )
        description = desc_elem.text.strip() if desc_elem else None

        # Discount percentage
        discount = self._extract_discount_percentage(elem)

        # Check if recurring
        is_recurring, recurring_day = self._check_recurring(elem)

        return ScrapedPromotion(
            title=title,
            description=description,
            discount_percentage=discount,
            start_date=datetime.utcnow(),
            is_recurring=is_recurring,
            recurring_day=recurring_day
        )

    def _extract_discount_percentage(self, elem: BeautifulSoup) -> Optional[float]:
        """Extract discount percentage from element text"""
        text = elem.get_text()

        # Look for patterns like "15% off", "20% discount"
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
        if match:
            return float(match.group(1))

        return None

    def _check_recurring(self, elem: BeautifulSoup) -> tuple:
        """Check if promotion is recurring and extract day"""
        text = elem.get_text().lower()

        days = {
            "monday": "monday",
            "tuesday": "tuesday",
            "wednesday": "wednesday",
            "thursday": "thursday",
            "friday": "friday",
            "saturday": "saturday",
            "sunday": "sunday"
        }

        is_recurring = "every" in text or "daily" in text
        recurring_day = None

        for day_name, day_value in days.items():
            if day_name in text:
                is_recurring = True
                recurring_day = day_value
                break

        return is_recurring, recurring_day

    @staticmethod
    def _normalize_category(category: str) -> str:
        """Normalize product category to standard values"""
        category_lower = category.lower().strip()

        category_map = {
            "flower": "Flower",
            "flowers": "Flower",
            "bud": "Flower",
            "vape": "Vape",
            "vapes": "Vape",
            "cartridge": "Vape",
            "cartridges": "Vape",
            "edible": "Edible",
            "edibles": "Edible",
            "gummy": "Edible",
            "gummies": "Edible",
            "concentrate": "Concentrate",
            "concentrates": "Concentrate",
            "wax": "Concentrate",
            "shatter": "Concentrate",
            "topical": "Topical",
            "topicals": "Topical",
            "cream": "Topical",
            "tincture": "Tincture",
            "tinctures": "Tincture",
            "oil": "Tincture",
        }

        return category_map.get(category_lower, "Other")

    @staticmethod
    def _parse_price(price_text: str) -> float:
        """Parse price from text like '$45.00' or '45'"""
        try:
            # Remove currency symbols and whitespace
            cleaned = re.sub(r'[^\d.]', '', price_text)
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0

    @staticmethod
    def _parse_percentage(value) -> Optional[float]:
        """Parse THC/CBD percentage from various formats"""
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                # Remove % sign and whitespace
                cleaned = re.sub(r'[^\d.]', '', value)
                return float(cleaned) if cleaned else None
            except ValueError:
                return None

        return None

    def _extract_percentage(
        self,
        elem: BeautifulSoup,
        labels: List[str]
    ) -> Optional[float]:
        """Extract percentage value by label from HTML element"""
        text = elem.get_text()

        for label in labels:
            # Try patterns like "THC: 24.5%" or "24.5% THC"
            patterns = [
                rf'{label}[:\s]*(\d+(?:\.\d+)?)\s*%',
                rf'(\d+(?:\.\d+)?)\s*%\s*{label}'
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return float(match.group(1))

        return None
