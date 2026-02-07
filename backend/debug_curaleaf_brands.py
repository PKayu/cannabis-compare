"""
Debug script to inspect Curaleaf product HTML to find brand extraction patterns.

Run with: python debug_curaleaf_brands.py
"""
import asyncio
import logging
import json
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URL = "https://ut.curaleaf.com/stores/curaleaf-ut-lehi"


async def debug_curaleaf_brands():
    """Inspect Curaleaf page HTML to find brand information"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(60000)

        try:
            logger.info(f"Loading {URL}...")
            await page.goto(URL, wait_until="domcontentloaded")

            # Handle age gate
            logger.info("Checking for age gate...")
            age_gate_selectors = [
                'button:has-text("I\'m over 18")',
                'button:has-text("I am over 18")',
                'button:has-text("Enter")',
            ]
            for selector in age_gate_selectors:
                try:
                    button = await page.wait_for_selector(selector, timeout=3000)
                    if button:
                        logger.info(f"Clicking age gate with selector: {selector}")
                        await button.click()
                        await page.wait_for_timeout(3000)
                        break
                except:
                    continue

            # Dismiss cookies
            try:
                cookie_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=2000)
                if cookie_btn:
                    await cookie_btn.click()
                    await page.wait_for_timeout(1000)
            except:
                pass

            # Navigate to flower category
            flower_url = f"{URL}/products/flower"
            logger.info(f"Navigating to {flower_url}")
            await page.goto(flower_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            # Wait for products and scroll to load more
            product_selectors = [
                '[class*="product-item-list"]',
                '[class*="product-carousel"]',
                '.product-card',
                '[data-testid*="product"]',
            ]

            products_found = False
            for selector in product_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    logger.info(f"Found {count} products with selector: {selector}")
                    products_found = True
                    # Scroll to load more
                    for i in range(5):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(2000)
                    break

            if not products_found:
                logger.warning("No products found!")
                return

            # Get detailed HTML structure of first few products
            product_analysis = await page.evaluate("""
                () => {
                    const results = [];

                    // Try different selectors
                    const selectors = [
                        '[class*="product-item-list"]',
                        '[class*="product-carousel"]',
                        '.product-card',
                        '[class*="ProductCard"]'
                    ];

                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 0) {
                            console.log(`Using selector: ${selector}, found ${elements.length} elements`);

                            // Analyze first 5 products
                            for (let i = 0; i < Math.min(5, elements.length); i++) {
                                const el = elements[i];

                                // Look for brand in various places
                                const brandSelectors = [
                                    '[data-brand]',
                                    '.brand',
                                    '.product-brand',
                                    '.vendor',
                                    '[class*="brand"]',
                                    'span[class*="vendor"]',
                                    'div[class*="brand"]'
                                ];

                                let brandInfo = null;
                                for (const brandSel of brandSelectors) {
                                    const brandEl = el.querySelector(brandSel);
                                    if (brandEl) {
                                        brandInfo = {
                                            selector: brandSel,
                                            text: brandEl.textContent.trim(),
                                            html: brandEl.outerHTML.substring(0, 200)
                                        };
                                        break;
                                    }
                                }

                                // Check for JSON-LD structured data
                                const jsonLd = el.querySelector('script[type="application/ld+json"]');
                                let structuredData = null;
                                if (jsonLd) {
                                    try {
                                        structuredData = JSON.parse(jsonLd.textContent);
                                    } catch (e) {
                                        // Invalid JSON
                                    }
                                }

                                // Get all attributes that might contain brand
                                const allAttrs = {};
                                for (const attr of el.attributes) {
                                    if (attr.name.includes('brand') || attr.name.includes('data-')) {
                                        allAttrs[attr.name] = attr.value;
                                    }
                                }

                                results.push({
                                    index: i,
                                    selector: selector,
                                    textContent: el.textContent.substring(0, 150),
                                    brandFound: brandInfo,
                                    structuredData: structuredData,
                                    dataAttributes: allAttrs,
                                    htmlSnippet: el.outerHTML.substring(0, 500)
                                });

                                // Only get 3 products per selector
                                if (results.length >= 3) {
                                    break;
                                }
                            }

                            // If we found products, stop checking other selectors
                            if (results.length > 0) {
                                break;
                            }
                        }
                    }

                    return results;
                }
            """)

            logger.info("\n" + "=" * 80)
            logger.info("PRODUCT ANALYSIS:")
            logger.info("=" * 80)

            for product in product_analysis:
                logger.info(f"\n--- Product {product['index'] + 1} ---")
                logger.info(f"Selector: {product['selector']}")
                logger.info(f"Text: {product['textContent']}")
                logger.info(f"Brand Found: {json.dumps(product['brandFound'], indent=2)}")
                if product.get('structuredData'):
                    logger.info(f"Structured Data: {json.dumps(product['structuredData'], indent=2)[:200]}")
                if product.get('dataAttributes'):
                    logger.info(f"Data Attributes: {json.dumps(product['dataAttributes'], indent=2)}")
                logger.info(f"HTML Snippet: {product['htmlSnippet'][:200]}")

            # Also check for any global structured data on the page
            page_structured_data = await page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    return Array.from(scripts).map(s => {
                        try {
                            return JSON.parse(s.textContent);
                        } catch (e) {
                            return {error: 'Invalid JSON'};
                        }
                    });
                }
            """)

            logger.info("\n" + "=" * 80)
            logger.info("PAGE STRUCTURED DATA (JSON-LD):")
            logger.info("=" * 80)
            for data in page_structured_data[:2]:  # First 2 scripts
                logger.info(json.dumps(data, indent=2)[:500])

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_curaleaf_brands())
