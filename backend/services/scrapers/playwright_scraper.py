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
from .registry import register_scraper

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
                    category=self._map_category(item.get("category", "")),
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

@register_scraper(
    id="wholesomeco",
    name="WholesomeCo",
    dispensary_name="WholesomeCo",
    dispensary_location="Bountiful, UT",
    schedule_minutes=120,
    description="Playwright-based scraper for WholesomeCo with Load More handling"
)
class WholesomeCoScraper(PlaywrightScraper):
    """
    Specialized scraper for WholesomeCo (wholesome.co)

    WholesomeCo uses JavaScript-rendered dynamic menu with:
    - Age gate verification (21+)
    - Products in .productListItem elements
    - "Load More" button for pagination
    - THC/CBD data in .productListItem-attrs
    """

    def __init__(self, dispensary_id: str = "wholesomeco"):
        super().__init__(
            menu_url="https://www.wholesome.co/shop",
            dispensary_name="WholesomeCo",
            dispensary_id=dispensary_id
        )

    async def scrape_products(self) -> List[ScrapedProduct]:
        """
        Scrape products from WholesomeCo with age gate and Load More handling
        """
        products = []
        logger.info(f"Scraping WholesomeCo using Playwright ({self.menu_url})")

        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()
                page.set_default_timeout(30000)

                # Navigate to the shop page
                logger.info(f"Loading {self.menu_url}...")
                await page.goto(self.menu_url, wait_until="domcontentloaded")

                # Handle age gate
                await self._dismiss_age_gate(page)

                # Wait for initial products to load
                await self._wait_for_products(page)

                # Click "Load More" until all products are visible
                await self._load_all_products(page)

                # Extract all products from the page
                products = await self._extract_products(page)

                logger.info(f"Successfully scraped {len(products)} products from WholesomeCo")

                await page.close()

        except Exception as e:
            logger.error(f"Error scraping WholesomeCo: {e}", exc_info=True)
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

        finally:
            if browser:
                await browser.close()

        logger.info(f"Returning {len(products)} products from WholesomeCo scraper")
        return products

    async def _dismiss_age_gate(self, page: "Page"):
        """Dismiss the 21+ age verification modal"""
        logger.info("Checking for age gate...")

        age_gate_selectors = [
            'button:has-text("I\'m 21 or older")',
            'button:has-text("I am 21")',
            'button:has-text("Enter")',
        ]

        for selector in age_gate_selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=3000)
                if button:
                    logger.info(f"Dismissing age gate with selector: {selector}")
                    await button.click()
                    await page.wait_for_timeout(2000)
                    return
            except:
                continue

        logger.info("No age gate found or already dismissed")

    async def _wait_for_products(self, page: "Page"):
        """Wait for WholesomeCo's product elements to appear"""
        logger.info("Waiting for WholesomeCo products to load...")

        try:
            # Wait for product list items to appear
            await page.wait_for_selector(".productListItem", timeout=15000)
            logger.info("Products loaded")
        except Exception:
            logger.warning("Could not find product elements - site structure may have changed")

    async def _load_all_products(self, page: "Page"):
        """
        Scroll to bottom of page to trigger infinite scroll loading

        WholesomeCo uses infinite scroll - products load as you scroll down
        """
        logger.info("Loading all products via infinite scroll...")

        last_product_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 50  # Safety limit

        while scroll_attempts < max_scroll_attempts:
            # Get current product count
            current_count = await page.locator(".productListItem").count()

            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            # Wait for new products to load
            await page.wait_for_timeout(1500)

            # Check if product count increased
            new_count = await page.locator(".productListItem").count()

            scroll_attempts += 1
            logger.info(f"Scroll {scroll_attempts}: {current_count} -> {new_count} products")

            if new_count == last_product_count:
                # Product count hasn't changed, try a few more times
                await page.wait_for_timeout(2000)
                new_count = await page.locator(".productListItem").count()
                if new_count == last_product_count:
                    logger.info(f"Product count stabilized at {new_count} - all products loaded")
                    break

            last_product_count = new_count

        logger.info(f"Finished loading products. Total: {last_product_count}")

    async def _extract_products(self, page: "Page") -> List[ScrapedProduct]:
        """
        Extract products from WholesomeCo's .productListItem elements

        Product structure:
        - .productListItem (container)
          - .productListItem-thumbnail (image)
          - .productListItem-content
            - Brand name
            - Product name with weight
          - .productListItem-attrs (THC/CBD info like "I\n19% THC\n0.42% CBG")
          - Price info
        """
        logger.info("Extracting WholesomeCo products...")

        # Extract product data using JavaScript
        product_data = await page.evaluate(
            """
            () => {
                const products = [];

                // WholesomeCo uses .productListItem for products
                const productElements = document.querySelectorAll('.productListItem');

                productElements.forEach(el => {
                    try {
                        // Get all text for parsing
                        const fullText = el.textContent || '';

                        // Extract name - usually the main heading
                        const nameEl = el.querySelector('h2, h3, h4, .product-name, [class*="name"]');
                        let name = nameEl?.textContent?.trim() || '';

                        // Extract brand - often appears before the name
                        // Look for brand links or badges
                        const brandEl = el.querySelector('a[href*="/brands/"], .brand, [class*="brand"]');
                        let brand = brandEl?.textContent?.trim() || null;

                        // If no brand found, try to extract from the beginning of the name
                        if (!brand && name) {
                            const parts = name.split('–');
                            if (parts.length > 1) {
                                brand = parts[0].trim();
                                name = parts.slice(1).join('–').trim();
                            }
                        }

                        // Extract price - look for price elements
                        let price = null;
                        const priceEl = el.querySelector('[class*="price"], [data-qa*="price"]');
                        if (priceEl) {
                            // Get numeric price, handle comma separators
                            const priceMatch = priceEl.textContent.replace(/,/g, '').match(/\\$?(\\d+\\.?\\d*)/);
                            if (priceMatch) {
                                price = priceMatch[1];
                            }
                        }

                        // If no price in price element, try to find it in full text
                        if (!price) {
                            const priceMatch = fullText.replace(/,/g, '').match(/\\$(\\d+\\.?\\d*)/);
                            if (priceMatch) {
                                price = priceMatch[1];
                            }
                        }

                        // Extract strain type (I/S/H) from attrs or text
                        const attrsEl = el.querySelector('.productListItem-attrs, [class*="attrs"]');
                        const attrsText = attrsEl?.textContent || fullText;

                        let strainType = null;
                        const strainMatch = attrsText.match(/\\b([HSI])\\b/);
                        if (strainMatch) {
                            strainType = strainMatch[1];
                        }

                        // Extract cannabinoids - patterns like "19% THC" and "0.42% CBG"
                        // The format is: number% CANNABINOID (e.g., "19% THC")
                        let thc = null, cbd = null, cbg = null, cbn = null;

                        // Check percentage format first (number% followed by cannabinoid name)
                        // This is the correct format: "19% THC" not "THC19%"
                        const thcMatch = attrsText.match(/(\\d+\\.?\\d*)%\\s*THC/i);
                        if (thcMatch) thc = thcMatch[1];

                        const cbdMatch = attrsText.match(/(\\d+\\.?\\d*)%\\s*CBD/i);
                        if (cbdMatch) cbd = cbdMatch[1];

                        const cbgMatch = attrsText.match(/(\\d+\\.?\\d*)%\\s*CBG/i);
                        if (cbgMatch) cbg = cbgMatch[1];

                        const cbnMatch = attrsText.match(/(\\d+\\.?\\d*)%\\s*CBN/i);
                        if (cbnMatch) cbn = cbnMatch[1];

                        // Extract weight/size
                        let weight = null;
                        const weightMatch = fullText.match(/(\\d+\\.?\\d*)\\s*(gr?|g|oz|ml|mg|each)/i);
                        if (weightMatch) {
                            weight = weightMatch[1] + weightMatch[2];
                        }

                        // Extract category from text
                        let category = 'other';
                        const lowerText = fullText.toLowerCase();
                        if (lowerText.includes('flower') || lowerText.includes('indoor') || lowerText.includes('outdoor') || lowerText.includes('greenhouse')) {
                            category = 'flower';
                        } else if (lowerText.includes('vape') || lowerText.includes('cartridge') || lowerText.includes('cart')) {
                            category = 'vaporizer';
                        } else if (lowerText.includes('edible') || lowerText.includes('gummy') || lowerText.includes('chocolate') || lowerText.includes('caramel')) {
                            category = 'edible';
                        } else if (lowerText.includes('concentrate') || lowerText.includes('rosin') || lowerText.includes('badder') || lowerText.includes('shatter') || lowerText.includes('diamond')) {
                            category = 'concentrate';
                        } else if (lowerText.includes('tincture')) {
                            category = 'tincture';
                        } else if (lowerText.includes('topical') || lowerText.includes('lotion') || lowerText.includes('balm')) {
                            category = 'topical';
                        } else if (lowerText.includes('pre-roll') || lowerText.includes('preroll')) {
                            category = 'pre-roll';
                        }

                        // Check stock status
                        const outOfStock = el.classList.contains('out-of-stock') ||
                                          el.classList.contains('sold-out') ||
                                          fullText.toLowerCase().includes('out of stock') ||
                                          fullText.toLowerCase().includes('sold out');

                        if (name && price) {
                            products.push({
                                name: name.trim(),
                                brand: brand,
                                category: category,
                                price: price,
                                thc: thc,
                                cbd: cbd,
                                cbg: cbg,
                                cbn: cbn,
                                strainType: strainType,
                                weight: weight,
                                inStock: !outOfStock,
                                html: el.outerHTML.substring(0, 1000)
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
                    brand=item.get("brand"),
                    category=item.get("category") or "other",
                    price=float(item["price"]),
                    thc_percentage=float(item["thc"]) if item.get("thc") else None,
                    cbd_percentage=float(item["cbd"]) if item.get("cbd") else None,
                    weight=item.get("weight"),
                    in_stock=item.get("inStock", True),
                    raw_data=item
                )
                products.append(product)
            except Exception as e:
                logger.warning(f"Failed to parse WholesomeCo product: {e}")

        logger.info(f"Extracted {len(products)} valid products from page")
        return products


@register_scraper(
    id="beehive-playwright",
    name="Beehive Farmacy (Playwright)",
    dispensary_name="Beehive Farmacy",
    dispensary_location="Salt Lake City, UT",
    schedule_minutes=120,
    description="Playwright-based scraper for Beehive Farmacy GraphQL menu"
)
class BeehiveScraper(PlaywrightScraper):
    """
    Specialized scraper for Beehive Farmacy

    Beehive uses GraphQL-backed menu (no need to reverse-engineer queries,
    Playwright handles the browser context and CSRF protection)
    """

    def __init__(self, dispensary_id: str = "beehive-playwright"):
        super().__init__(
            menu_url="https://www.beehivefarmacy.com",  # Adjust if needed
            dispensary_name="Beehive Farmacy",
            dispensary_id=dispensary_id
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
