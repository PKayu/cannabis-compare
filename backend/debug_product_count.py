"""
Debug script to inspect Curaleaf product loading in browser.

Run with: python debug_product_count.py
This will launch a visible browser to observe the product loading behavior.
"""
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Curaleaf Lehi URL
URL = "https://ut.curaleaf.com/stores/curaleaf-ut-lehi"


async def debug_curaleaf():
    """Inspect Curaleaf page to understand product loading"""

    async with async_playwright() as p:
        # Launch in non-headless mode to observe
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        page.set_default_timeout(30000)

        try:
            # Navigate to main page
            logger.info(f"Loading {URL}...")
            await page.goto(URL, wait_until="domcontentloaded")

            # Handle age gate
            logger.info("Looking for age gate...")
            try:
                button = await page.wait_for_selector('button:has-text("I\'m over 18")', timeout=5000)
                if button:
                    logger.info("Clicking age gate button...")
                    await button.click()
                    await page.wait_for_timeout(5000)
            except:
                logger.info("No age gate found")

            # Check for cookie consent
            try:
                cookie_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=3000)
                if cookie_btn:
                    await cookie_btn.click()
                    await page.wait_for_timeout(1000)
            except:
                pass

            # Navigate to flower category
            flower_url = f"{URL}/products/flower"
            logger.info(f"Navigating to flower category: {flower_url}")
            await page.goto(flower_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            # Count initial products
            product_selector = '[class*="product-item-list"]'
            initial_count = await page.locator(product_selector).count()
            logger.info(f"Initial product count on flower page: {initial_count}")

            if initial_count == 0:
                product_selector = '[class*="product-carousel"]'
                initial_count = await page.locator(product_selector).count()
                logger.info(f"Trying alternative selector, count: {initial_count}")

            # Try scrolling to load more
            logger.info("Scrolling to load more products...")
            last_count = initial_count

            for i in range(10):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)

                current_count = await page.locator(product_selector).count()
                logger.info(f"Scroll {i+1}: {current_count} products")

                if current_count == last_count:
                    # No change, try waiting a bit longer
                    await page.wait_for_timeout(3000)
                    current_count = await page.locator(product_selector).count()
                    if current_count == last_count:
                        logger.info("Product count stabilized - no more loading")
                        break
                last_count = current_count

            # Check for category tabs/links on the page
            logger.info("Checking for category navigation...")
            category_links = await page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a'));
                    return links
                        .filter(a => a.href && a.href.includes('/products/'))
                        .map(a => ({
                            text: a.textContent.trim(),
                            href: a.href
                        }))
                        .slice(0, 10);
                }
            """)
            logger.info(f"Found category links: {category_links}")

            # Check page height before and after scroll
            page_height_before = await page.evaluate("document.body.scrollHeight")
            logger.info(f"Page height: {page_height_before}px")

            # Get some sample product data
            sample_data = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('[class*="product-item-list"]');
                    return Array.from(elements).slice(0, 3).map(el => ({
                        text: el.textContent.substring(0, 200),
                        html: el.outerHTML.substring(0, 300)
                    }));
                }
            """)
            logger.info(f"Sample products ({len(sample_data)}):")
            for i, sample in enumerate(sample_data):
                logger.info(f"  Product {i+1} text: {sample['text'][:100]}...")

            # Pause for manual inspection
            logger.info("")
            logger.info("=" * 60)
            logger.info("Browser will stay open for 30 seconds for manual inspection.")
            logger.info("Press Ctrl+C to close early if needed.")
            logger.info("=" * 60)
            await page.wait_for_timeout(30000)

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_curaleaf())
