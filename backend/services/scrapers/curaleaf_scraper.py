"""
Curaleaf Utah Scraper

Scrapes Curaleaf dispensary locations in Utah using Playwright browser automation.
Handles age gate verification, infinite scroll, and product extraction.
"""
import logging
from typing import List, TYPE_CHECKING

from .playwright_scraper import PlaywrightScraper
from .base_scraper import ScrapedProduct, ScrapedPromotion
from .registry import register_scraper

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from playwright.async_api import Page


@register_scraper(
    id="curaleaf-lehi",
    name="Curaleaf Utah - Lehi",
    dispensary_name="Curaleaf",
    dispensary_location="Lehi, UT",
    schedule_minutes=120,
    description="Playwright-based scraper for Curaleaf Utah Lehi location"
)
class CuraleafScraper(PlaywrightScraper):
    """
    Scraper for Curaleaf Utah (Lehi location)

    Curaleaf uses a Next.js-based menu with:
    - Age gate verification (21+)
    - JavaScript-rendered product cards
    - Potential infinite scroll or load more
    - Product data includes: name, brand, price, THC/CBD, weight, category, stock
    """

    # Curaleaf Utah locations
    LOCATIONS = {
        "lehi": "https://ut.curaleaf.com/stores/curaleaf-ut-lehi",
        "provo": "https://ut.curaleaf.com/stores/curaleaf-ut-provo",
        "springville": "https://ut.curaleaf.com/stores/curaleaf-ut-springville",
        "park-city": "https://ut.curaleaf.com/stores/curaleaf-ut-park-city",
    }

    def __init__(self, dispensary_id: str = "curaleaf-lehi", location: str = "lehi"):
        """
        Initialize Curaleaf scraper

        Args:
            dispensary_id: Unique ID for this dispensary
            location: Which location to scrape (lehi, provo, springville, park-city)
        """
        url = self.LOCATIONS.get(location, self.LOCATIONS["lehi"])
        location_name = location.replace("-", " ").title()

        super().__init__(
            menu_url=url,
            dispensary_name=f"Curaleaf Utah - {location_name}",
            dispensary_id=dispensary_id
        )
        self.location = location

    # Curaleaf product categories (slugs from their menu)
    CATEGORIES = [
        "flower",
        "vaporizers",
        "edibles",
        "concentrates",
        "tinctures",
        "topicals",
        "accessories",  # Hardware/devices — mapped to "hardware" category after extraction
    ]

    async def scrape_products(self) -> List[ScrapedProduct]:
        """
        Scrape products from Curaleaf by visiting each category page

        Curaleaf organizes products by category on separate pages.
        We need to visit each category page to get all products.
        """
        all_products = []
        logger.info(f"Scraping Curaleaf {self.location} using Playwright ({self.menu_url})")

        browser = None
        try:
            async with await self._get_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()
                page.set_default_timeout(60000)  # 60 second timeout for all operations

                # Dismiss age gate first — it now navigates directly to /age-gate and handles the redirect
                await self._dismiss_age_gate(page)

                # Verify we're on the store page, not still stuck on the age gate
                await page.goto(self.menu_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(1000)
                if "age-gate" in page.url:
                    logger.error("Still on age gate after dismissal attempt — aborting scrape")
                    return all_products

                logger.info(f"On store page: {page.url}")

                # Now visit each category page
                total_categories = len(self.CATEGORIES)
                for idx, category in enumerate(self.CATEGORIES, 1):
                    logger.info(f"Scraping category {idx}/{total_categories}: {category}")
                    category_url = f"{self.menu_url}/products/{category}"

                    try:
                        logger.info(f"  Loading {category_url}...")
                        await page.goto(category_url, wait_until="networkidle", timeout=30000)
                        await page.wait_for_timeout(2000)

                        # Age gate sometimes re-appears on category pages — re-dismiss if needed
                        if "age-gate" in page.url:
                            logger.warning(f"  Age gate re-appeared for category {category}, re-dismissing...")
                            await self._dismiss_age_gate(page)
                            await page.goto(category_url, wait_until="networkidle", timeout=30000)
                            await page.wait_for_timeout(2000)

                        # Wait for products to load on this category page
                        logger.info(f"  Waiting for products to load...")
                        await self._wait_for_products(page)

                        # CRITICAL: Load all products via infinite scroll/load more
                        # This was missing - causing only initial products to be scraped
                        logger.info(f"  Loading all products (clicking View More buttons)...")
                        await self._load_all_products(page)

                        # Extract products from this category
                        logger.info(f"  Extracting products...")
                        category_products = await self._extract_products(page)
                        logger.info(f"  Found {len(category_products)} products in {category}")

                        # The JS extraction infers category from product text keywords, not the page URL.
                        # Override to "hardware" for the accessories page so these products don't
                        # compete with cannabis products in confidence matching.
                        if category == "accessories":
                            for p in category_products:
                                p.category = "hardware"

                        all_products.extend(category_products)

                    except Exception as e:
                        logger.warning(f"Error scraping category {category}: {e}")
                        continue

                logger.info(f"Successfully scraped {len(all_products)} products from Curaleaf {self.location}")
                await page.close()

        except Exception as e:
            logger.error(f"Error scraping Curaleaf {self.location}: {e}", exc_info=True)
            logger.error(f"Exception type: {type(e).__name__}")
            # Re-raise so the caller sees the error
            raise

        finally:
            if browser:
                await browser.close()

        logger.info(f"Returning {len(all_products)} products from Curaleaf scraper")
        return all_products

    async def _get_playwright(self):
        """Get async_playwright context"""
        from playwright.async_api import async_playwright
        return async_playwright()

    async def _dismiss_age_gate(self, page: "Page"):
        """
        Dismiss Curaleaf's age verification page.

        As of Mar 2026, Curaleaf changed from a modal overlay to a full-page redirect:
        every URL (including category pages) redirects to /age-gate?returnurl=...
        The confirm button is rendered by AgeVerificationClient (client-side React),
        so we must wait for networkidle + extra hydration time before looking for it.
        """
        from urllib.parse import quote
        logger.info("Handling Curaleaf age gate (full-page redirect pattern)...")

        # Navigate directly to the age gate page with networkidle so React fully hydrates
        age_gate_url = f"https://ut.curaleaf.com/age-gate?returnurl={quote(self.menu_url, safe='')}"
        await page.goto(age_gate_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)  # Extra wait for client-side hydration

        age_gate_selectors = [
            'button:has-text("I\'m over 18")',
            'button:has-text("I am over 18")',
            'button:has-text("Yes, I\'m 18")',
            'button:has-text("I\'m 21")',
            'button:has-text("I am 21")',
            'button:has-text("I\'m 21 or older")',
            'button:has-text("Yes")',
            'button:has-text("Enter")',
            'button:has-text("I\'m of legal age")',
            # Fallback: any button that is not the "Exit" button
            # The age gate has exactly two buttons: confirm and Exit (links to google.com)
            'button:not(:has-text("Exit"))',
        ]

        for selector in age_gate_selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=5000)
                if button and await button.is_visible():
                    logger.info(f"Clicking age gate button with selector: {selector}")
                    await button.click()
                    await page.wait_for_timeout(3000)
                    if "age-gate" not in page.url:
                        logger.info("Age gate dismissed successfully")
                        await self._dismiss_cookies(page)
                        return
            except Exception:
                continue

        logger.warning("Could not dismiss Curaleaf age gate — scraping will likely return 0 products")

    async def _dismiss_cookies(self, page: "Page"):
        """Dismiss cookie consent dialog if present"""
        logger.info("Checking for cookie consent...")

        cookie_selectors = [
            'button:has-text("Accept Cookies")',
            '#onetrust-accept-btn-handler',
            'button[ id="onetrust-accept-btn-handler"]',
        ]

        for selector in cookie_selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=2000)
                if button:
                    logger.info(f"Dismissing cookies with selector: {selector}")
                    await button.click()
                    await page.wait_for_timeout(1000)
                    return
            except Exception:
                continue

        logger.info("No cookie consent found")

    async def _wait_for_products(self, page: "Page"):
        """
        Wait for Curaleaf product elements to appear

        Curaleaf uses different class patterns:
        - Main page: product-carousel
        - Category pages: product-item-list
        """
        logger.info("Waiting for Curaleaf products to load...")

        selectors = [
            '[class*="product-item-list"]',  # Category pages
            '[class*="product-carousel"]',   # Main page
            '[data-testid*="product"]',
            '[data-test*="product"]',
            '.product-card',
            '.product-item',
            '[class*="ProductCard"]',
            '[class*="ProductItem"]',
        ]

        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                logger.info(f"Found products with selector: {selector}")
                return
            except Exception:
                continue

        logger.warning("Could not find Curaleaf product elements - site structure may have changed")

    async def _load_all_products(self, page: "Page"):
        """
        Load all products via infinite scroll or load more button

        Curaleaf may use either infinite scroll or a "Load More" button.
        This method handles both patterns.
        """
        logger.info("Loading all Curaleaf products...")

        last_count = 0
        attempts = 0
        max_attempts = 15  # Further reduced from 30 to match WholesomeCo and prevent timeouts

        # Try to determine which product selector to use for this page
        product_selectors = [
            '[class*="ProductCard"]',        # Current Curaleaf site (Mar 2026+)
            '[class*="product-item-list"]',  # Legacy: category pages
            '[class*="product-carousel"]',   # Legacy: main page
            '.product-card',
            '.product-item',
        ]

        product_selector = None
        for selector in product_selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    product_selector = selector
                    logger.info(f"Using product selector: {selector} (initial count: {count})")
                    break
            except:
                continue

        if not product_selector:
            logger.warning("Could not find product elements for loading")
            return

        while attempts < max_attempts:
            # First, try to find and click a "Load More" button
            try:
                load_more_selectors = [
                    'button:has-text("Load More")',
                    'button:has-text("Show More")',
                    'button:has-text("View More")',
                    '[data-testid*="load"]',
                    '[data-testid*="more"]',
                ]
                for selector in load_more_selectors:
                    try:
                        button = page.locator(selector).first
                        if await button.is_visible(timeout=1000):
                            logger.info(f"Clicking load more button: {selector}")
                            await button.click()
                            await page.wait_for_timeout(2000)
                            break
                    except:
                        continue
            except:
                pass

            # Scroll to bottom to trigger infinite scroll
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(4000)  # WholesomeCo learning: increased from 2000ms for better lazy loading

            # Check if product count has changed
            try:
                current_count = await page.locator(product_selector).count()
            except:
                current_count = 0

            logger.info(f"Scroll attempt {attempts + 1}/{max_attempts}: {current_count} products")

            if current_count == last_count and current_count > 0:
                # WholesomeCo pattern: Double-check with 4-second wait to ensure all products loaded
                await page.wait_for_timeout(4000)
                try:
                    new_count = await page.locator(product_selector).count()
                    if new_count == last_count:
                        logger.info(f"Product count stabilized at {current_count} - all products loaded")
                        break
                except:
                    break

            last_count = current_count
            attempts += 1

        logger.info(f"Finished loading products. Total: {last_count}")

    async def _extract_products(self, page: "Page") -> List[ScrapedProduct]:
        """
        Extract products from Curaleaf's DOM structure.

        As of Mar 2026, each product is a <div class="*ProductCard*"> containing:
          <a aria-label="Cap Junky Whole Flower, Flower. 7g | 251215H - $55.00" href="/shop/...">

        The aria-label is the authoritative source for name / type / weight / price.
        Text content is used for THC/CBD and brand (brands appear as "by Find." in the text).
        """
        logger.info("Extracting Curaleaf products...")

        # Extract product data using JavaScript
        product_data = await page.evaluate("""
            () => {
                const products = [];

                // Curaleaf class patterns (current first, then legacy fallbacks)
                let elements = document.querySelectorAll('[class*="ProductCard"]');
                if (elements.length === 0) {
                    elements = document.querySelectorAll('[class*="product-item-list"]');
                }
                if (elements.length === 0) {
                    elements = document.querySelectorAll('[class*="product-carousel"]');
                }
                console.log(`Found ${elements.length} product elements`);

                // Known Curaleaf brands for text-based brand detection
                const knownBrands = [
                    'Curaleaf', 'Grassroots', 'Select', 'DGT', 'Find.', 'Jams',
                    'Chief', 'Incredibles', 'Mindseye', 'BCD', 'AbsoluteXtracts',
                    'Care By Design', 'Guild', 'Lowell', 'Floyds of Leadville',
                    'CBD Clinic', 'CBD For Life', 'Platinum', 'Dixie',
                    'Canna Pros', 'Green Therapies', 'Utah Cannabis',
                    'WholesomeCo', 'Tryke', 'Standard', 'Dragonfly',
                    'Boojum', 'Hoodoo', 'Riverside Farm', 'Hi Variety',
                    'Surplus', 'Element', 'Cresco', 'Bazelet',
                    'Floweer', 'Plus', 'Loud', 'Connected',
                    'Stiiizy', 'RYTHM', 'Justice', 'Moxie', 'Origins',
                    'Hilight', 'HiLight', 'Buzz', 'Hygge', 'Gummiez',
                    // Utah-specific craft brands
                    'San Juan Squish Co.', 'San Juan Squish', 'HighWire',
                    // Hardware / accessory brands
                    'Rokin', 'Puffco', 'PAX', 'DynaVap', 'Storz & Bickel',
                    'Volcano', 'Yocan', 'Boundless', 'Arizer',
                ];

                elements.forEach(el => {
                    try {
                        const fullText = el.textContent || '';
                        if (!fullText.includes('$') || fullText.length < 20) return;

                        // PRIMARY: aria-label on the product <a> tag
                        // Format: "Product Name, Category. Weight | LotNum - $Price"
                        // Example: "Cap Junky Whole Flower, Flower. 7g | 251215H - $55.00"
                        const linkEl = el.querySelector('a[aria-label]');
                        if (!linkEl) return;

                        const ariaLabel = linkEl.getAttribute('aria-label') || '';
                        const url = linkEl.href
                            ? (linkEl.href.startsWith('http') ? linkEl.href : new URL(linkEl.href, window.location.origin).href)
                            : null;

                        // Parse: "Name, Type. Weight | Lot - $Price"
                        const ariaMatch = ariaLabel.match(/^(.+?),\\s*(.+?)\\.\\s*(\\S+)\\s*\\|[^-]*-\\s*\\$(\\d+\\.?\\d*)/);
                        if (!ariaMatch) return;

                        const name = ariaMatch[1].trim();
                        const categoryRaw = ariaMatch[2].toLowerCase();
                        const weight = ariaMatch[3].trim();
                        const price = ariaMatch[4];

                        if (!name || !price || name.length < 3) return;

                        // Map category from the type field in the aria-label
                        let category = 'other';
                        if (categoryRaw.includes('flower')) category = 'flower';
                        else if (categoryRaw.includes('vaporizer') || categoryRaw.includes('cartridge') || categoryRaw.includes('vape')) category = 'vaporizer';
                        else if (categoryRaw.includes('edible') || categoryRaw.includes('gummy') || categoryRaw.includes('infusion') || categoryRaw.includes('capsule') || categoryRaw.includes('tablet')) category = 'edible';
                        else if (categoryRaw.includes('concentrate') || categoryRaw.includes('rosin') || categoryRaw.includes('resin') || categoryRaw.includes('wax') || categoryRaw.includes('badder') || categoryRaw.includes('sugar') || categoryRaw.includes('shatter')) category = 'concentrate';
                        else if (categoryRaw.includes('tincture') || categoryRaw.includes('drop') || categoryRaw.includes('sublingual')) category = 'tincture';
                        else if (categoryRaw.includes('topical') || categoryRaw.includes('lotion') || categoryRaw.includes('balm') || categoryRaw.includes('cream') || categoryRaw.includes('patch')) category = 'topical';
                        else if (categoryRaw.includes('pre-roll') || categoryRaw.includes('preroll')) category = 'pre-roll';

                        // Strain type from text content
                        let strainType = null;
                        if (fullText.includes('Indica')) strainType = 'Indica';
                        else if (fullText.includes('Sativa')) strainType = 'Sativa';
                        else if (fullText.includes('Hybrid')) strainType = 'Hybrid';

                        // THC / CBD from text (may or may not be present in the new layout)
                        let thc = null, thcUnit = null, cbd = null, cbdUnit = null;
                        const thcPctM = fullText.match(/THC:\\s*(\\d+\\.?\\d*)%/i);
                        if (thcPctM) { thc = thcPctM[1]; thcUnit = '%'; }
                        else { const thcMgM = fullText.match(/THC:\\s*(\\d+\\.?\\d*)\\s*mg/i); if (thcMgM) { thc = thcMgM[1]; thcUnit = 'mg'; } }

                        const cbdPctM = fullText.match(/CBD:\\s*(\\d+\\.?\\d*)%/i);
                        if (cbdPctM) { cbd = cbdPctM[1]; cbdUnit = '%'; }
                        else { const cbdMgM = fullText.match(/CBD:\\s*(\\d+\\.?\\d*)\\s*mg/i); if (cbdMgM) { cbd = cbdMgM[1]; cbdUnit = 'mg'; } }

                        const cbgM = fullText.match(/CBG:\\s*(\\d+\\.?\\d*)(%|\\s*mg)?/i);
                        const cbg = cbgM ? cbgM[1] : null;

                        const cbnM = fullText.match(/CBN:\\s*(\\d+\\.?\\d*)(%|\\s*mg)?/i);
                        const cbn = cbnM ? cbnM[1] : null;

                        // Brand: check known brands list, then try "by BrandName" pattern
                        let brand = null;
                        const lowerText = fullText.toLowerCase();
                        for (const b of knownBrands) {
                            if (fullText.includes(b) || lowerText.includes(b.toLowerCase())) {
                                brand = b;
                                break;
                            }
                        }
                        if (!brand) {
                            // "by Origins", "by Find.", etc. appear in the new text layout
                            const byMatch = fullText.match(/\\bby\\s+([A-Z][A-Za-z.&\\s]{1,25}?)(?=[A-Z][a-z]|\\d|\\s*$)/);
                            if (byMatch) brand = byMatch[1].trim();
                        }

                        // Stock status
                        const outOfStock = lowerText.includes('out of stock') || lowerText.includes('sold out')
                            || el.classList.contains('out-of-stock') || el.classList.contains('sold-out');
                        const lowStockM = fullText.match(/Only (\\d+) left/i);
                        const stockStatus = outOfStock ? 'out_of_stock' : (lowStockM ? 'low_stock' : 'in_stock');

                        products.push({
                            name,
                            brand,
                            category,
                            price,
                            weight,
                            strainType,
                            thc, thcUnit,
                            cbd, cbdUnit,
                            cbg, cbn,
                            inStock: !outOfStock,
                            stockStatus,
                            stockQuantity: lowStockM ? parseInt(lowStockM[1]) : null,
                            url,
                            html: el.outerHTML.substring(0, 500),
                        });
                    } catch (e) {
                        console.error('Error parsing Curaleaf product:', e);
                    }
                });

                console.log(`Extracted ${products.length} valid products`);
                return products;
            }
        """)

        # Convert extracted data to ScrapedProduct objects
        products = []
        for item in product_data:
            try:
                thc_val = item.get("thc")
                thc_unit = item.get("thcUnit")
                cbd_val = item.get("cbd")
                cbd_unit = item.get("cbdUnit")

                # Build plain-text display strings (e.g. "15.4%" or "396mg")
                thc_content = f"{thc_val}{thc_unit}" if thc_val and thc_unit else None
                cbd_content = f"{cbd_val}{cbd_unit}" if cbd_val and cbd_unit else None

                # Only store float percentage when unit is actually %; mg values go in content only
                thc_pct = self._parse_float(thc_val) if thc_unit == '%' else None
                cbd_pct = self._parse_float(cbd_val) if cbd_unit == '%' else None

                product = ScrapedProduct(
                    name=item["name"],
                    brand=item.get("brand"),
                    category=item.get("category", "other"),
                    price=float(item["price"]),
                    thc_percentage=thc_pct,
                    cbd_percentage=cbd_pct,
                    cbg_percentage=self._parse_float(item.get("cbg")),  # WholesomeCo learning: CBG extraction
                    thc_content=thc_content,
                    cbd_content=cbd_content,
                    weight=item.get("weight"),
                    in_stock=item.get("inStock", True),
                    url=item.get("url"),  # WholesomeCo learning: product URL for direct links
                    raw_data=item  # CBN, stockStatus, stockQuantity preserved here
                )
                products.append(product)
            except Exception as e:
                logger.warning(f"Failed to parse Curaleaf product: {e}")

        logger.info(f"Extracted {len(products)} valid products from Curaleaf {self.location}")
        return products

    def _parse_float(self, value: str | None) -> float | None:
        """
        Safely parse string to float

        Args:
            value: String value to parse

        Returns:
            Float value or None if parsing fails
        """
        if not value:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """
        Scrape promotional information from Curaleaf

        Currently not implemented - promotions can be added later if needed.
        """
        logger.info("Promotions scraping not implemented for Curaleaf")
        return []


# Additional location-specific scrapers
# Each location is registered separately for independent scheduling and management


@register_scraper(
    id="curaleaf-provo",
    name="Curaleaf Utah - Provo",
    dispensary_name="Curaleaf",
    dispensary_location="Provo, UT",
    schedule_minutes=120,
    description="Playwright-based scraper for Curaleaf Utah Provo location"
)
class CuraleafProvoScraper(CuraleafScraper):
    """Scraper for Curaleaf Provo location"""

    def __init__(self, dispensary_id: str = "curaleaf-provo"):
        super().__init__(dispensary_id=dispensary_id, location="provo")


@register_scraper(
    id="curaleaf-springville",
    name="Curaleaf Utah - Springville",
    dispensary_name="Curaleaf",
    dispensary_location="Springville, UT",
    schedule_minutes=120,
    description="Playwright-based scraper for Curaleaf Utah Springville location"
)
class CuraleafSpringvilleScraper(CuraleafScraper):
    """Scraper for Curaleaf Springville location"""

    def __init__(self, dispensary_id: str = "curaleaf-springville"):
        super().__init__(dispensary_id=dispensary_id, location="springville")


# Note: Park City location exists (1351 Kearns Blvd, Park City, UT 84060)
# but does NOT have an online menu. The page at
# https://ut.curaleaf.com/dispensary/utah/curaleaf-ut-wellness-park
# is a pharmacy information page only, not a browsable menu.
# Customers must visit the store or call to order.
#
# If this changes and Park City gets an online menu, the scraper
# can be enabled by changing enabled=False to enabled=True
# and updating the URL to the correct menu page.

# @register_scraper(
#     id="curaleaf-park-city",
#     name="Curaleaf Utah - Park City",
#     dispensary_name="Curaleaf",
#     dispensary_location="Park City, UT",
#     schedule_minutes=120,
#     enabled=False,  # No online menu available
#     description="Playwright-based scraper for Curaleaf Utah Park City location (DISABLED - no online menu)"
# )
# class CuraleafParkCityScraper(CuraleafScraper):
#     """Scraper for Curaleaf Park City location - DISABLED due to no online menu"""
#
#     def __init__(self, dispensary_id: str = "curaleaf-park-city"):
#         # This location doesn't have a /stores/ menu page
#         # Would need to find the correct URL if one becomes available
#         super().__init__(dispensary_id=dispensary_id, location="park-city")
