# Curaleaf Scraper Improvements - Context

**Last Updated**: 2026-02-14
**Status**: In Progress

## Key Files

- **Primary**: `backend/services/scrapers/curaleaf_scraper.py` (731 lines)
  - `_load_all_products()` - Lines 253-339
  - `_extract_products()` - Lines 341-642

- **Reference**: `backend/services/scrapers/playwright_scraper.py`
  - WholesomeCo implementation with optimized patterns (lines 298-679)

- **Schema**: `backend/services/scrapers/base_scraper.py`
  - ScrapedProduct dataclass (lines 28-43)
  - Already has `cbg_percentage` field (line 38)
  - Already has `url` field (line 42)

## Key Decisions

1. **Hybrid Approach**: Following `docs/guides/LLM_ASSISTED_SCRAPER_DISCOVERY.md`
   - Verify selectors manually before making changes
   - Apply proven WholesomeCo regex patterns
   - Test extraction rates against expected coverage

2. **CBN Handling**: Extract to `raw_data` only (no structured field yet)
   - `ScrapedProduct` and `Product` models don't have `cbn_percentage`
   - Future enhancement: add CBN as structured field with migration

3. **Wait Time Strategy**: Increase from 2s to 4-5s
   - WholesomeCo demonstrated this handles lazy loading better
   - Double-check stabilization prevents premature exit

4. **URL Extraction**: Critical missing feature
   - Users need direct product links for purchases
   - Admins need URLs for flagging verification
   - Stored on `Price.product_url` field

## Inheritance Impact

All changes benefit three scrapers (they inherit from `CuraleafScraper`):
- `CuraleafScraper` (Lehi) - id: `curaleaf-lehi`
- `CuraleafProvoScraper` - id: `curaleaf-provo`
- `CuraleafSpringvilleScraper` - id: `curaleaf-springville`

## WholesomeCo Patterns Applied

From `playwright_scraper.py` WholesomeCoScraper:

1. **URL extraction** (lines 468-476):
   ```javascript
   const linkEl = el.querySelector('a[href]');
   let url = linkEl?.href || null;
   if (url && !url.startsWith('http')) {
       url = new URL(url, window.location.origin).href;
   }
   ```

2. **CBG extraction** (lines 561-568):
   ```javascript
   let cbgMatch = attrsText.match(/(\d+\.?\d*)%\s*CBG/i);
   if (!cbgMatch) {
       cbgMatch = attrsText.match(/(\d+\.?\d*)\s*(?:mg\s+)?CBG/i);
   }
   ```

3. **Stock quantity** (lines 621-625):
   ```javascript
   const stockMatch = fullText.match(/Only (\d+) left/i);
   if (stockMatch) {
       stockStatus = 'low_stock';
       stockQuantity = parseInt(stockMatch[1]);
   }
   ```

4. **Scroll stabilization** (lines 427-433):
   ```javascript
   if (new_count == last_product_count) {
       await page.wait_for_timeout(5000);  // Double-check wait
       new_count = await page.locator(".productListItem").count();
       if (new_count == last_product_count) break;
   }
   ```
