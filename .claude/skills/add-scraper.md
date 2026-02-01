# Add New Dispensary Scraper

## Overview
Add a new Playwright-based scraper for a Utah dispensary to the cannabis aggregator project. This skill guides you through creating a complete scraper implementation.

## Steps

### 1. Gather Dispensary Information
- Get the dispensary's website URL
- Note the dispensary name and location
- Check if there's an age gate (21+ verification)
- Identify if it uses JavaScript rendering (most modern sites do)

### 2. Create Scraper File
Create a new file `backend/services/scrapers/[dispensary]_scraper.py`

Use this template:

```python
"""
[Dispensary Name] Scraper

Scrapes [Dispensary Name] using Playwright browser automation.
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
    id="[unique-id]",
    name="[Display Name]",
    dispensary_name="[Dispensary Name]",
    dispensary_location="[City, UT]",
    schedule_minutes=120,
    description="[Brief description]"
)
class [DispensaryName]Scraper(PlaywrightScraper):
    """
    Scraper for [Dispensary Name]

    Site characteristics:
    - [Age gate?]
    - [Infinite scroll? Load more button?]
    - [Product data available]
    """

    def __init__(self, dispensary_id: str = "[unique-id]"):
        super().__init__(
            menu_url="[URL]",
            dispensary_name="[Display Name]",
            dispensary_id=dispensary_id
        )

    async def scrape_products(self) -> List[ScrapedProduct]:
        """Main scraping method"""
        products = []
        logger.info(f"Scraping {self.dispensary_name}...")

        browser = None
        try:
            async with await self._get_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()
                page.set_default_timeout(30000)

                await page.goto(self.menu_url, wait_until="domcontentloaded")

                # Handle age gate if present
                await self._dismiss_age_gate(page)

                # Wait for products
                await self._wait_for_products(page)

                # Load all products
                await self._load_all_products(page)

                # Extract products
                products = await self._extract_products(page)

                await page.close()

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)

        finally:
            if browser:
                await browser.close()

        return products

    async def _get_playwright(self):
        from playwright.async_api import async_playwright
        return async_playwright()

    async def _dismiss_age_gate(self, page: "Page"):
        """Dismiss age gate - customize selectors per site"""
        selectors = [
            'button:has-text("Enter")',
            'button:has-text("Yes")',
            'button:has-text("I am 21")',
            'button:has-text("I\'m 21")',
        ]

        for selector in selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=3000)
                if button:
                    await button.click()
                    await page.wait_for_timeout(2000)
                    return
            except:
                continue

    async def _wait_for_products(self, page: "Page"):
        """Wait for products to load - customize selectors"""
        selectors = [
            '[data-testid*="product"]',
            '.product-card',
            '.product-item',
        ]

        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                return
            except:
                continue

    async def _load_all_products(self, page: "Page"):
        """Load all products via infinite scroll or load more"""
        last_count = 0
        attempts = 0

        while attempts < 30:
            # Try load more button
            try:
                button = page.locator('button:has-text("Load More")').first
                if await button.is_visible(timeout=1000):
                    await button.click()
                    await page.wait_for_timeout(2000)
            except:
                pass

            # Scroll
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)

            # Check count
            current_count = await page.locator('[data-testid*="product"], .product-card').count()
            if current_count == last_count and current_count > 0:
                break
            last_count = current_count
            attempts += 1

    async def _extract_products(self, page: "Page") -> List[ScrapedProduct]:
        """Extract products - customize based on site's DOM"""
        product_data = await page.evaluate("""
            () => {
                const products = [];
                const elements = document.querySelectorAll('[data-testid*="product"], .product-card');

                elements.forEach(el => {
                    const name = el.querySelector('h2, h3')?.textContent?.trim();
                    const brand = el.querySelector('[class*="brand"]')?.textContent?.trim();
                    let price = null;
                    const priceEl = el.querySelector('[class*="price"]');
                    if (priceEl) {
                        const match = priceEl.textContent.match(/\$?(\d+\.?\d*)/);
                        if (match) price = match[1];
                    }

                    if (name && price) {
                        products.push({ name, brand, price });
                    }
                });

                return products;
            }
        """)

        # Convert to ScrapedProduct
        products = []
        for item in product_data:
            try:
                product = ScrapedProduct(
                    name=item["name"],
                    brand=item.get("brand"),
                    category="other",  # Map from site data
                    price=float(item["price"]),
                    raw_data=item
                )
                products.append(product)
            except Exception as e:
                logger.warning(f"Parse error: {e}")

        return products

    def _parse_float(self, value: str | None) -> float | None:
        if not value:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        return []
```

### 3. Register Scraper in main.py
Add import to `backend/main.py` (around line 25-30):

```python
from services.scrapers.[dispensary]_scraper import [DispensaryName]Scraper  # noqa: F401
```

### 4. Test the Scraper

**Option A: Using Python script**
```bash
cd backend
python -c "
import asyncio
from services.scraper_runner import ScraperRunner
from database import SessionLocal

async def test():
    db = SessionLocal()
    runner = ScraperRunner(db, triggered_by='manual')
    result = await runner.run_by_id('[unique-id]')
    print(f'Status: {result.status}')
    print(f'Products: {result.products_count}')
    db.close()

asyncio.run(test())
"
```

**Option B: Using Admin Dashboard**
1. Start backend: `cd backend && python -m uvicorn main:app --reload`
2. Visit http://localhost:3000/admin/scrapers
3. Find your scraper and click "Run Now"
4. Check results

### 5. Verify Results

Check database for products:
```bash
cd backend
python -c "
from database import SessionLocal
from models import Product

db = SessionLocal()
count = db.query(Product).filter(Product.dispensary_id == '[dispensary-id]').count()
print(f'Products in database: {count}')
db.close()
"
```

### 6. Inspect DOM for Customization

If the scraper isn't extracting products correctly:

1. Set `headless=False` in `__init__` for debugging:
```python
super().__init__(..., headless=False)
```

2. Use browser DevTools (F12) to inspect:
   - Product card HTML structure
   - Data attributes (data-testid, data-name, etc.)
   - CSS classes
   - Price formats

3. Update selectors in `_extract_products()` based on findings

## Category Mapping

Map site categories to standard types:

| Site Category | Standard Category |
|---------------|-------------------|
| flower, bud | Flower |
| pre-roll, preroll, joint | Pre-roll |
| vape, cartridge, cart | Vaporizer |
| edible, gummy, chocolate | Edible |
| concentrate, wax, shatter, rosin | Concentrate |
| tincture, oil | Tincture |
| topical, lotion, balm | Topical |

## Data Structure

Required `ScrapedProduct` fields:
- `name: str` (required)
- `price: float` (required)
- `brand: str` (optional)
- `category: str` (one of standard categories)
- `in_stock: bool` (default True)
- `thc_percentage: float` (optional)
- `cbd_percentage: float` (optional)
- `weight: str` (optional, e.g., "3.5g")
- `raw_data: dict` (preserves original scraped data)

## Common Issues

| Issue | Solution |
|-------|----------|
| Age gate not dismissed | Add more selectors to `_dismiss_age_gate()` |
| Products not found | Update selectors in `_wait_for_products()` and `_extract_products()` |
| Infinite scroll not working | Increase timeout, check for "Load More" button |
| Price parsing fails | Check price format, update regex in extraction |
| Category wrong | Improve category mapping logic |

## Success Criteria

- [ ] Scraper file created
- [ ] Registered with `@register_scraper`
- [ ] Imported in `main.py`
- [ ] Products extracted successfully
- [ ] Products appear in database
- [ ] Scheduled runs work (visible in admin dashboard)

## Notes

- Always set `headless=False` initially for debugging
- Use `self.logger` for all logging
- Preserve original data in `raw_data` field
- Handle exceptions gracefully
- Test with real browser before trusting headless mode
- Check site's terms of service before scraping
