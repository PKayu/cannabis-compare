"""
Playwright-based web scraper for dispensaries with dynamic/API-driven menus

Works for:
- JavaScript-rendered pages (WholesomeCo)
- GraphQL-backed sites (Beehive Pharmacy)
- HTML with complex interactions
- Any site that needs a real browser context
"""
import logging
from typing import List, Optional, TYPE_CHECKING
from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available - install with: pip install playwright")

if TYPE_CHECKING:
    from playwright.async_api import Page


class PlaywrightScraper(BaseScraper):
    """
    Scrapes dispensary websites using Playwright browser automation

    Perfect for:
    - JavaScript-heavy pages (WholesomeCo)
    - GraphQL-backed menus (Beehive Pharmacy)
    - Sites with dynamic content loading
    - Complex HTML structures that need CSS selectors
    """

    def __init__(
        self,
        menu_url: str,
        dispensary_name: str = "Unknown Dispensary",
        dispensary_id: str = "unknown",
        headless: bool = True
    ):
        """
        Initialize Playwright scraper

        Args:
            menu_url: Full URL to the menu/products page
            dispensary_name: Human-readable name for logging
            dispensary_id: Unique ID for this dispensary
            headless: Run browser in headless mode (True = no visual)
        """
        super().__init__(dispensary_id=dispensary_id)

        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. Install with:\n"
                "pip install playwright"
            )

        self.menu_url = menu_url
        self.dispensary_name = dispensary_name
        self.headless = headless

        logger.info(
            f"Initialized Playwright scraper for {dispensary_name} ({menu_url})"
        )

    async def scrape_products(self) -> List[ScrapedProduct]:
        """
        Scrape products from a website using Playwright

        Returns:
            List of ScrapedProduct objects

        Raises:
            Exception: On browser or scraping errors
        """
        products = []
        logger.info(
            f"Scraping {self.dispensary_name} using Playwright ({self.menu_url})"
        )

        browser = None
        try:
            async with async_playwright() as p:
                # Launch browser (Chromium recommended for speed)
                browser = await p.chromium.launch(headless=self.headless)

                # Create a new page/context
                page = await browser.new_page()

                # Set timeout for page operations
                page.set_default_timeout(30000)  # 30 seconds

                # Navigate to the menu page
                logger.info(f"Loading {self.menu_url}...")
                await page.goto(self.menu_url, wait_until="networkidle")

                # Wait for products to appear (customize selectors for each site)
                await self._wait_for_products(page)

                # Extract products from the page
                products = await self._extract_products(page)

                logger.info(
                    f"Successfully scraped {len(products)} products "
                    f"from {self.dispensary_name}"
                )

                await page.close()

        except Exception as e:
            logger.error(f"Error scraping {self.dispensary_name}: {e}", exc_info=True)

        finally:
            if browser:
                await browser.close()

        return products

    async def _wait_for_products(self, page: "Page"):
        """
        Wait for products to load on the page

        Customize this method for each site's specific selectors
        """
        # Try multiple common product selectors
        selectors = [
            "[data-test*='product']",  # Data attributes
            ".product-card",
            ".product-item",
            ".menu-item",
            "[class*='product']",
            "li:has([data-price])",  # Li with price data
        ]

        for selector in selectors:
            try:
                # Wait for first product to appear
                await page.wait_for_selector(selector, timeout=5000)
                logger.info(f"Found products with selector: {selector}")
                return
            except Exception:
                continue

        logger.warning(
            f"Could not find product elements on {self.dispensary_name}. "
            "Page may not have loaded correctly."
        )

    async def _extract_products(self, page: "Page") -> List[ScrapedProduct]:
        """
        Extract product data from the page DOM

        Override this method per-site for custom extraction logic
        """
        # Get all product elements and extract data
        product_data = await page.evaluate(
            """
            () => {
                const products = [];
                const selectors = [
                    '[data-test*="product"]',
                    '.product-card',
                    '.product-item',
                    '.menu-item'
                ];

                let elements = [];
                for (const selector of selectors) {
                    elements = document.querySelectorAll(selector);
                    if (elements.length > 0) break;
                }

                elements.forEach(element => {
                    const product = {
                        name: element.querySelector('h2, h3, .name, [data-name]')?.textContent?.trim(),
                        price: element.querySelector('[data-price], .price, [class*="price"]')?.textContent?.match(/\\d+\\.?\\d*/)?.[0],
                        thc: element.querySelector('[data-thc], .thc, [class*="thc"]')?.textContent?.match(/\\d+\\.?\\d*/)?.[0],
                        brand: element.querySelector('.brand, [data-brand], [class*="brand"]')?.textContent?.trim(),
                        category: element.querySelector('.category, [data-category]')?.textContent?.trim(),
                        inStock: !element.querySelector('[data-sold-out], .sold-out, [class*="unavailable"]'),
                        html: element.outerHTML
                    };

                    if (product.name) {
                        products.push(product);
                    }
                });

                return products;
            }
            """
        )

        # Convert extracted data to ScrapedProduct objects
        products = []
        for item in product_data:
            try:
                product = ScrapedProduct(
                    name=item.get("name", ""),
                    brand=item.get("brand"),
                    product_type=self._map_category(item.get("category", "")),
                    thc_percentage=self._parse_float(item.get("thc")),
                    price=self._parse_float(item.get("price")) or 0,
                    in_stock=item.get("inStock", True),
                    raw_data=item  # Preserve original for debugging
                )

                if product.name:
                    products.append(product)

            except Exception as e:
                logger.warning(f"Failed to parse product: {e}")
                continue

        return products

    async def scrape_promotions(self):
        """
        Scrape promotional information from the page

        Currently not implemented for Playwright scraper
        """
        return []

    def _map_category(self, category: str) -> str:
        """Map category strings to product types"""
        if not category:
            return "other"

        category_lower = category.lower()

        category_map = {
            "flower": "flower",
            "bud": "flower",
            "pre-roll": "pre-roll",
            "joint": "pre-roll",
            "vape": "vaporizer",
            "cartridge": "vaporizer",
            "concentrate": "concentrate",
            "extract": "concentrate",
            "edible": "edible",
            "gummy": "edible",
            "topical": "topical",
            "cream": "topical",
            "tincture": "tincture",
            "oil": "tincture",
        }

        return category_map.get(category_lower, "other")

    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Safely parse string to float"""
        if not value:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


# Site-specific scrapers inherit from PlaywrightScraper
class WholesomeCoScraper(PlaywrightScraper):
    """
    Specialized scraper for WholesomeCo (wholesome.co)

    WholesomeCo uses JavaScript-rendered dynamic menu
    """

    def __init__(self):
        super().__init__(
            menu_url="https://www.wholesome.co/shop",
            dispensary_name="WholesomeCo",
            dispensary_id="wholesomeco"
        )

    async def _wait_for_products(self, page: "Page"):
        """Wait for WholesomeCo's specific product elements"""
        logger.info("Waiting for WholesomeCo products to load...")

        # WholesomeCo uses specific classes/data attributes
        try:
            # Wait for the products container
            await page.wait_for_selector(
                "[data-qa*='product'], .product, [class*='ProductCard']",
                timeout=10000
            )
        except Exception:
            logger.warning(
                "Could not find WholesomeCo product selector. "
                "The site structure may have changed."
            )

    async def _extract_products(self, page: "Page") -> List[ScrapedProduct]:
        """Extract products from WholesomeCo's specific structure"""
        logger.info("Extracting WholesomeCo products...")

        # WholesomeCo-specific extraction logic
        product_data = await page.evaluate(
            """
            () => {
                const products = [];

                // WholesomeCo uses data-qa attributes and specific classes
                const productElements = document.querySelectorAll(
                    '[data-qa*="product"], .ProductCard, [class*="ProductCard"]'
                );

                productElements.forEach(el => {
                    try {
                        const name = el.querySelector('h2, h3, [data-qa*="name"]')?.textContent?.trim();
                        const priceText = el.querySelector('[data-qa*="price"], .price')?.textContent;
                        const price = priceText?.match(/\\$?([\\d.]+)/)?.[1];
                        const thcText = el.querySelector('[data-qa*="thc"]')?.textContent;
                        const thc = thcText?.match(/(\\d+\\.?\\d*)/)?.[1];

                        if (name && price) {
                            products.push({
                                name,
                                price,
                                thc,
                                inStock: !el.classList.contains('out-of-stock'),
                                html: el.outerHTML.substring(0, 500)
                            });
                        }
                    } catch (e) {
                        console.error('Error parsing product:', e);
                    }
                });

                return products;
            }
            """
        )

        # Convert to ScrapedProduct objects
        products = []
        for item in product_data:
            try:
                product = ScrapedProduct(
                    name=item["name"],
                    price=float(item["price"]),
                    thc_percentage=float(item["thc"]) if item.get("thc") else None,
                    in_stock=item.get("inStock", True),
                    raw_data=item
                )
                products.append(product)
            except Exception as e:
                logger.warning(f"Failed to parse WholesomeCo product: {e}")

        return products


class BeehiveScraper(PlaywrightScraper):
    """
    Specialized scraper for Beehive Farmacy

    Beehive uses GraphQL-backed menu (no need to reverse-engineer queries,
    Playwright handles the browser context and CSRF protection)
    """

    def __init__(self):
        super().__init__(
            menu_url="https://www.beehivefarmacy.com",  # Adjust if needed
            dispensary_name="Beehive Farmacy",
            dispensary_id="beehive"
        )

    async def _wait_for_products(self, page: "Page"):
        """Wait for Beehive's GraphQL products to load"""
        logger.info("Waiting for Beehive products (GraphQL) to load...")

        try:
            # Beehive loads products via GraphQL - wait for them to appear
            await page.wait_for_selector(
                "[data-product], .product, [class*='Product']",
                timeout=10000
            )
        except Exception:
            logger.warning("Could not find Beehive product selector")

    async def _extract_products(self, page: "Page") -> List[ScrapedProduct]:
        """Extract products from Beehive's GraphQL-rendered page"""
        logger.info("Extracting Beehive products...")

        product_data = await page.evaluate(
            """
            () => {
                const products = [];

                // Beehive-specific selectors (adjust based on actual DOM)
                const productElements = document.querySelectorAll(
                    '[data-product], .product-item, [class*="ProductItem"]'
                );

                productElements.forEach(el => {
                    try {
                        const name = el.querySelector(
                            'h3, h4, [data-testid*="name"]'
                        )?.textContent?.trim();

                        const priceText = el.textContent;
                        const price = priceText?.match(/\\$?([\\d.]+)/)?.[1];

                        const thcText = el.textContent;
                        const thc = thcText?.match(/([\\d.]+)%/)?.[1];

                        if (name) {
                            products.push({
                                name,
                                price,
                                thc,
                                inStock: true,
                                html: el.outerHTML.substring(0, 500)
                            });
                        }
                    } catch (e) {
                        console.error('Error parsing Beehive product:', e);
                    }
                });

                return products;
            }
            """
        )

        # Convert to ScrapedProduct objects
        products = []
        for item in product_data:
            try:
                product = ScrapedProduct(
                    name=item["name"],
                    price=float(item["price"]) if item.get("price") else 0,
                    thc_percentage=float(item["thc"]) if item.get("thc") else None,
                    in_stock=item.get("inStock", True),
                    raw_data=item
                )
                products.append(product)
            except Exception as e:
                logger.warning(f"Failed to parse Beehive product: {e}")

        return products
