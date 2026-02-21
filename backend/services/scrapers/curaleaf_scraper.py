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
        # "accessories",  # Skip accessories - not cannabis products
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

                # First, navigate to main page and handle age gate
                logger.info(f"Loading {self.menu_url}...")
                await page.goto(self.menu_url, wait_until="domcontentloaded")
                await self._dismiss_age_gate(page)

                # Now visit each category page
                total_categories = len(self.CATEGORIES)
                for idx, category in enumerate(self.CATEGORIES, 1):
                    logger.info(f"Scraping category {idx}/{total_categories}: {category}")
                    category_url = f"{self.menu_url}/products/{category}"

                    try:
                        logger.info(f"  Loading {category_url}...")
                        await page.goto(category_url, wait_until="domcontentloaded", timeout=30000)
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
        Dismiss Curaleaf's age verification modal

        Curaleaf shows "Hey, Welcome to Curaleaf" age gate with an "I'm over 18" button.
        Note: The site uses "18" but Utah's legal age is 21+.
        """
        logger.info("Checking for Curaleaf age gate...")

        # Curaleaf uses "I'm over 18" button (site-wide, not Utah-specific)
        age_gate_selectors = [
            'button:has-text("I\'m over 18")',  # Curaleaf's actual button text
            'button:has-text("I am over 18")',
            'button:has-text("Enter")',
            'button:has-text("Yes")',
            'button:has-text("I am 21")',
            'button:has-text("I\'m 21")',
            'button:has-text("I am 21 or older")',
            'button:has-text("I\'m 21 or older")',
            '[data-testid*="age"] button',
            '[data-testid*="verify"] button',
            '.age-gate-yes',
            '#age-gate-yes',
        ]

        for selector in age_gate_selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=3000)
                if button:
                    logger.info(f"Dismissing age gate with selector: {selector}")
                    await button.click()
                    # Wait for navigation to complete - check if URL changed
                    await page.wait_for_timeout(5000)

                    # Also dismiss cookie consent if present
                    await self._dismiss_cookies(page)

                    # Additional wait for products to load
                    await page.wait_for_timeout(3000)

                    return
            except Exception:
                continue

        logger.info("No age gate found or already dismissed")

        # Even if no age gate, wait for page to load
        await page.wait_for_timeout(3000)

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
        # Category pages use product-item-list, main page uses product-carousel
        product_selectors = [
            '[class*="product-item-list"]',  # Category pages
            '[class*="product-carousel"]',   # Main page
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
        Extract products from Curaleaf's DOM structure

        Curaleaf product format (from text content):
        "Grape Cakes Whole FlowerDGTHybridTHC: 15.4%$94.50$135.0030% offAdd to cart"
        "Elite Clementine CartridgeSelectSativaTHC: 83.59%$48.00$60.0020% offAdd to cart"

        Pattern:
        - Product name (first part)
        - Brand (DGT, Select, Find., etc.)
        - Strain type (Hybrid, Sativa, Indica)
        - THC/CBD info (THC: XX% or THC: XX mg for edibles)
        - Price ($XX.XX)
        - Sometimes discount price and %
        """
        logger.info("Extracting Curaleaf products...")

        # Extract product data using JavaScript
        product_data = await page.evaluate("""
            () => {
                const products = [];

                // Curaleaf uses different class patterns:
                // - Main page: product-carousel
                // - Category pages: product-item-list
                // Try both patterns
                let elements = document.querySelectorAll('[class*="product-item-list"]');
                if (elements.length === 0) {
                    elements = document.querySelectorAll('[class*="product-carousel"]');
                }
                console.log(`Found ${elements.length} product elements`);

                elements.forEach(el => {
                    try {
                        const fullText = el.textContent || '';

                        // Skip empty or non-product elements
                        if (!fullText.includes('$') || fullText.length < 20) {
                            return;
                        }

                        // Extract product URL (WholesomeCo pattern)
                        const linkEl = el.querySelector('a[href]');
                        let url = null;
                        if (linkEl) {
                            url = linkEl.href;
                            if (url && !url.startsWith('http')) {
                                url = new URL(url, window.location.origin).href;
                            }
                        }

                        // Parse Curaleaf's specific format
                        // Example: "Grape Cakes Whole FlowerDGTHybridTHC: 15.4%$94.50$135.0030% offAdd to cart"

                        // Extract price (first $XX.XX is current price)
                        let price = null;
                        const priceMatches = fullText.match(/\\$\\s*(\\d+\\.\\d{2})/g);
                        if (priceMatches && priceMatches.length > 0) {
                            // First price is the current price (sometimes there's a discount)
                            price = priceMatches[0].replace(/\\$\\s*/, '');
                        }

                        // Extract THC (format: "THC: 15.4%" or "THC: 134 mg")
                        let thc = null;
                        let thcUnit = null;
                        const thcPercentMatch = fullText.match(/THC:\\s*(\\d+\\.?\\d*)%/i);
                        if (thcPercentMatch) {
                            thc = thcPercentMatch[1];
                            thcUnit = '%';
                        } else {
                            const thcMgMatch = fullText.match(/THC:\\s*(\\d+\\.?\\d*)\\s*mg/i);
                            if (thcMgMatch) { thc = thcMgMatch[1]; thcUnit = 'mg'; }
                        }

                        // Extract CBD (format: "CBD: 203.98 mg" or "CBD: 0.23%")
                        let cbd = null;
                        let cbdUnit = null;
                        const cbdPercentMatch = fullText.match(/CBD:\\s*(\\d+\\.?\\d*)%/i);
                        if (cbdPercentMatch) {
                            cbd = cbdPercentMatch[1];
                            cbdUnit = '%';
                        } else {
                            const cbdMgMatch = fullText.match(/CBD:\\s*(\\d+\\.?\\d*)\\s*mg/i);
                            if (cbdMgMatch) { cbd = cbdMgMatch[1]; cbdUnit = 'mg'; }
                        }

                        // Extract CBG (WholesomeCo pattern - supports percentage and milligram)
                        let cbg = null;
                        const cbgPercentMatch = fullText.match(/CBG:\\s*(\\d+\\.?\\d*)%/i);
                        if (cbgPercentMatch) {
                            cbg = cbgPercentMatch[1];
                        } else {
                            const cbgMgMatch = fullText.match(/CBG:\\s*(\\d+\\.?\\d*)\\s*mg/i);
                            if (cbgMgMatch) cbg = cbgMgMatch[1];
                        }

                        // Extract CBN (WholesomeCo pattern - supports percentage and milligram, stored in raw_data)
                        let cbn = null;
                        const cbnPercentMatch = fullText.match(/CBN:\\s*(\\d+\\.?\\d*)%/i);
                        if (cbnPercentMatch) {
                            cbn = cbnPercentMatch[1];
                        } else {
                            const cbnMgMatch = fullText.match(/CBN:\\s*(\\d+\\.?\\d*)\\s*mg/i);
                            if (cbnMgMatch) cbn = cbnMgMatch[1];
                        }

                        // Determine category from product name/text
                        let category = 'other';
                        const lowerText = fullText.toLowerCase();

                        if (lowerText.includes('whole flower') || lowerText.includes(' flower') ||
                            lowerText.includes('bud') || lowerText.includes('indoor')) {
                            category = 'flower';
                        } else if (lowerText.includes('cartridge') || lowerText.includes('vape') ||
                                   lowerText.includes('stiq') || lowerText.includes('briq')) {
                            category = 'vaporizer';
                        } else if (lowerText.includes('infusion') || lowerText.includes('gummy') ||
                                   lowerText.includes('edible') || lowerText.includes('chocolate') ||
                                   lowerText.includes('x-bites')) {
                            category = 'edible';
                        } else if (lowerText.includes('concentrate') || lowerText.includes('rosin') ||
                                   lowerText.includes('resin')) {
                            category = 'concentrate';
                        } else if (lowerText.includes('tincture')) {
                            category = 'tincture';
                        } else if (lowerText.includes('topical')) {
                            category = 'topical';
                        } else if (lowerText.includes('pre-roll') || lowerText.includes('preroll')) {
                            category = 'pre-roll';
                        }

                        // Extract strain type (Indica, Sativa, Hybrid)
                        let strainType = null;
                        if (fullText.includes('Indica')) strainType = 'Indica';
                        else if (fullText.includes('Sativa')) strainType = 'Sativa';
                        else if (fullText.includes('Hybrid')) strainType = 'Hybrid';

                        // Extract brand from original fullText BEFORE processing
                        // Curaleaf brands - comprehensive list based on their inventory
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
                            'Stiiizy', 'Select', 'RYTHM', 'Justice'
                        ];

                        let brand = null;
                        // Search in original fullText for brand names
                        // Use word boundaries where possible, but also handle concatenated text
                        for (const b of knownBrands) {
                            // First try simple string matching (handles special chars like . in "Find.")
                            if (fullText.includes(b)) {
                                brand = b;
                                break;
                            }
                            // Also try case-insensitive search
                            const lowerText = fullText.toLowerCase();
                            const lowerBrand = b.toLowerCase();
                            if (lowerText.includes(lowerBrand)) {
                                brand = b;
                                break;
                            }
                        }

                        // Fallback: Try to extract brand using position patterns
                        // Brands often appear right before strain type or product type
                        if (!brand) {
                            // Words that should never be treated as brands
                            const nonBrandWords = [
                                'Flower', 'Whole', 'Cartridge', 'Vape', 'Edible', 'Tincture',
                                'Topical', 'Concentrate', 'Preroll', 'Infusion', 'Gummies',
                                'Balm', 'Cream', 'Salve', 'Patch', 'Tablet', 'Tablets',
                                'Capsule', 'Capsules', 'Pod', 'Pods', 'Pen', 'Pens',
                                'Add', 'Buy', 'Cart', 'Off', 'Each', 'Pack', 'mg',
                                'THC', 'CBD', 'Sativa', 'Indica', 'Hybrid', 'or'
                            ];

                            // Pattern 1: Extract text between product type and strain type
                            // This is where brands typically appear in Curaleaf's format
                            const productTypes = ['Whole Flower', 'Cartridge', 'Infusion', 'Gummies', 'Tincture', 'Balm', 'Tablet'];
                            for (const prodType of productTypes) {
                                if (fullText.includes(prodType) && strainType) {
                                    // Find text between product type and strain type
                                    const parts = fullText.split(prodType);
                                    if (parts.length > 1) {
                                        const afterType = parts[1];
                                        // Find where strain type appears
                                        const strainIndex = afterType.indexOf(strainType);
                                        if (strainIndex > 0) {
                                            let potentialBrand = afterType.substring(0, strainIndex).trim();
                                            // Clean up - remove common non-brand words
                                            potentialBrand = potentialBrand.replace(/\\d+\\.?\\d*mg?/gi, '');
                                            potentialBrand = potentialBrand.replace(/\\s+/g, ' ').trim();
                                            // Only use if it looks reasonable
                                            if (potentialBrand.length > 1 && potentialBrand.length < 30 &&
                                                potentialBrand.length > 2 &&
                                                !nonBrandWords.includes(potentialBrand) &&
                                                !/\\d/.test(potentialBrand)) {
                                                brand = potentialBrand;
                                                break;
                                            }
                                        }
                                    }
                                }
                            }

                            // Pattern 2: Text before "Indica", "Sativa", or "Hybrid" might be brand
                            if (!brand) {
                                const strainPattern = /([A-Z][a-z]+)\\s*(Indica|Sativa|Hybrid)/i;
                                const strainMatch = fullText.match(strainPattern);
                                if (strainMatch) {
                                    const potentialBrand = strainMatch[1].trim();
                                    if (potentialBrand.length > 2 && potentialBrand.length < 30 &&
                                        !nonBrandWords.includes(potentialBrand)) {
                                        brand = potentialBrand;
                                    }
                                }
                            }

                            // Pattern 3: Text before "Whole Flower" might be brand
                            if (!brand) {
                                const flowerPattern = /([A-Z][A-Za-z]+)\\s+Whole Flower/i;
                                const flowerMatch = fullText.match(flowerPattern);
                                if (flowerMatch && flowerMatch[1].length > 2) {
                                    const potentialBrand = flowerMatch[1].trim();
                                    if (!nonBrandWords.includes(potentialBrand)) {
                                        brand = potentialBrand;
                                    }
                                }
                            }
                        }

                        // Parse product name and brand
                        // Curaleaf format: "ProductNameBrandStrainTypeTHC: XX%$Price"
                        // We need to extract the actual product name

                        // Remove common suffixes to isolate name
                        let name = fullText;

                        // Remove strain type
                        if (strainType) {
                            name = name.replace(strainType, ' ');
                        }

                        // Remove THC/CBD info
                        name = name.replace(/THC:\\s*\\d+\\.?\\d*%?/gi, ' ');
                        name = name.replace(/CBD:\\s*\\d+\\.?\\d*%?/gi, ' ');

                        // Remove prices
                        name = name.replace(/\\$\\d+\\.\\d{2}/g, ' ');
                        name = name.replace(/\\d+%/g, ' ');  // Remove discount percentages

                        // Remove "Add to cart" and similar
                        name = name.replace(/Add to cart/gi, '');
                        name = name.replace(/BUY \\(\\d+\\)[^+]+/g, ' ');  // Remove promos like "BUY (4) SELECT..."

                        // Remove the brand we found from the name (if found)
                        if (brand) {
                            // Simple case-insensitive replace
                            const brandRegex = new RegExp(brand, 'gi');
                            name = name.replace(brandRegex, ' ');
                        }

                        // Clean up name
                        name = name.replace(/\\s+/g, ' ').trim();
                        // Remove trailing descriptors that aren't part of name
                        name = name.replace(/\\s+(Whole Flower|Cartridge|Infusion|Gummies).*$/, '');
                        name = name.trim();

                        // Extract weight from name or text
                        let weight = null;
                        const weightMatch = fullText.match(/(\\d+\\.?\\d*)\\s*(gr?|g|oz|ml|mg)/i);
                        if (weightMatch) {
                            weight = weightMatch[1] + weightMatch[2];
                        }

                        // Check stock status and extract urgency messages (WholesomeCo pattern)
                        let stockStatus = 'in_stock';
                        let stockQuantity = null;

                        const outOfStock =
                            el.classList.contains('out-of-stock') ||
                            el.classList.contains('sold-out') ||
                            lowerText.includes('out of stock') ||
                            lowerText.includes('sold out');

                        if (outOfStock) {
                            stockStatus = 'out_of_stock';
                        } else {
                            // Check for low stock urgency message
                            const stockMatch = fullText.match(/Only (\\d+) left/i);
                            if (stockMatch) {
                                stockStatus = 'low_stock';
                                stockQuantity = parseInt(stockMatch[1]);
                            }
                        }

                        // Only include products with name and price
                        if (name && price && name.length > 3) {
                            products.push({
                                name: name,
                                brand: brand,
                                category: category,
                                price: price,
                                thc: thc,
                                thcUnit: thcUnit,
                                cbd: cbd,
                                cbdUnit: cbdUnit,
                                cbg: cbg,  // WholesomeCo learning: CBG extraction
                                cbn: cbn,  // WholesomeCo learning: CBN for raw_data
                                weight: weight,
                                strainType: strainType,
                                inStock: stockStatus === 'in_stock',
                                stockStatus: stockStatus,  // WholesomeCo learning: detailed stock status
                                stockQuantity: stockQuantity,  // WholesomeCo learning: urgency detection
                                url: url,  // WholesomeCo learning: product URL for direct links
                                html: el.outerHTML.substring(0, 500)
                            });
                        }
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
