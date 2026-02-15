# Plan: Improve Curaleaf Scrapers Using WholesomeCo Learnings

## Context

The WholesomeCo Playwright scraper has been successfully optimized and is "pulling in very quickly" with reliable data extraction. The Curaleaf scrapers use the same Playwright-based architecture but can benefit from the performance improvements and data extraction enhancements implemented in WholesomeCo.

**Why this change is needed:**
- WholesomeCo demonstrates better handling of lazy-loaded content with longer, more patient wait times
- WholesomeCo extracts more comprehensive cannabinoid data (CBG, CBN) with dual-format support
- WholesomeCo has better product URL extraction (critical for user purchases and admin verification)
- WholesomeCo has more robust scrolling logic with double-check stabilization
- Applying these learnings will improve Curaleaf's scraper reliability and data completeness

## Methodology: Hybrid Approach

Following the **Hybrid LLM-Assisted Discovery Workflow** (see `docs/guides/LLM_ASSISTED_SCRAPER_DISCOVERY.md`), we should:

1. **Verify existing selectors** - Ensure Curaleaf's current selectors actually match elements (not assumptions)
2. **Apply WholesomeCo patterns** - Use regex patterns and edge case handling from WholesomeCo
3. **Test extraction rates** - Validate improvements against expected coverage

This is the same approach used to optimize WholesomeCo, combining LLM pattern insights with manual selector verification.

## Key Improvements to Apply

### 1. Increase Wait Times for Lazy Loading
**Current (Curaleaf):** 2-second waits between scroll attempts
**WholesomeCo approach:** 4-5 second waits with additional patience for slow lazy loading

**Change:**
- `_load_all_products()`: Increase base wait from 2000ms to 4000ms
- Add 5-second double-check wait when count stabilizes (like WholesomeCo line 429-432)

### 2. Add Product URL Extraction
**Current (Curaleaf):** Product URLs are NOT extracted at all
**WholesomeCo approach:** Extracts URLs from link elements and makes them absolute

**Missing feature impact:** Without URLs, users can't directly link to products, and admins can't verify flagged items at the source.

**Change:**
- Add URL extraction in the JavaScript `_extract_products()` evaluation
- Follow WholesomeCo pattern (lines 468-476): find link element, extract href, make absolute

### 3. Add CBG Cannabinoid Extraction
**Current (Curaleaf):** Only extracts THC and CBD
**WholesomeCo approach:** Extracts THC, CBD, CBG with dual-format support (percentage + milligrams)

**Note:** CBN is extracted by WholesomeCo into `raw_data` but not as a structured field (no `cbn_percentage` in ScrapedProduct or Product models). We'll extract CBN for raw_data preservation but won't add it as a structured field yet.

**Change:**
- Add CBG extraction regex (support both `X% CBG` and `X mg CBG`)
- Add CBN extraction regex for raw_data (support both `X% CBN` and `X mg CBN`)
- Update `ScrapedProduct` creation to include `cbg_percentage` field
- CBN will be preserved in `raw_data` for future use

### 4. Improve Scrolling Reliability
**Current (Curaleaf):** Single check when count stabilizes
**WholesomeCo approach:** Double-check with 5-second wait to ensure all products loaded

**Change:**
- After detecting stabilization, wait 5 seconds and check count again
- Only break loop if count remains stable across both checks

### 5. Add Stock Quantity Detection
**Current (Curaleaf):** Only detects out-of-stock status
**WholesomeCo approach:** Detects "Only X left" urgency messages

**Change:**
- Add regex pattern to extract stock quantity from "Only X left" messages
- Store as `stockQuantity` in raw data (for future use in frontend urgency messaging)

## Files to Modify

### Primary File
- **`backend/services/scrapers/curaleaf_scraper.py`** (731 lines)
  - `_load_all_products()` method (lines 253-339) - increase wait times, add double-check
  - `_extract_products()` method (lines 341-642) - add URL extraction, CBG/CBN, stock quantity

## Implementation Details

### Changes to `_load_all_products()` (lines 253-339)

```python
async def _load_all_products(self, page: "Page"):
    """
    Load all products via infinite scroll or load more button

    WholesomeCo learnings applied:
    - Increased wait times (4s base, 5s stabilization check)
    - Double-check stabilization to ensure all products loaded
    """
    logger.info("Loading all Curaleaf products...")

    last_count = 0
    attempts = 0
    max_attempts = 30

    # ... existing selector logic ...

    while attempts < max_attempts:
        # ... existing load more button logic ...

        # Scroll to bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(4000)  # CHANGED: 2000 -> 4000 (WholesomeCo learning)

        # Check if product count has changed
        try:
            current_count = await page.locator(product_selector).count()
        except:
            current_count = 0

        logger.info(f"Scroll attempt {attempts + 1}/{max_attempts}: {current_count} products")

        if current_count == last_count and current_count > 0:
            # WholesomeCo pattern: Double-check with longer wait
            await page.wait_for_timeout(5000)  # ADDED: Extra stabilization wait
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
```

### Changes to `_extract_products()` JavaScript (lines 360-620)

**Add URL extraction (after line 380):**
```javascript
// Extract product URL (WholesomeCo pattern)
const linkEl = el.querySelector('a[href]');
let url = null;
if (linkEl) {
    url = linkEl.href;
    if (url && !url.startsWith('http')) {
        url = new URL(url, window.location.origin).href;
    }
}
```

**Add CBG/CBN extraction (after CBD extraction around line 411):**
```javascript
// Extract CBG (WholesomeCo pattern - supports percentage and milligram)
let cbg = null;
const cbgPercentMatch = fullText.match(/CBG:\s*(\d+\.?\d*)%/i);
if (cbgPercentMatch) {
    cbg = cbgPercentMatch[1];
} else {
    const cbgMgMatch = fullText.match(/CBG:\s*(\d+\.?\d*)\s*mg/i);
    if (cbgMgMatch) cbg = cbgMgMatch[1];
}

// Extract CBN (WholesomeCo pattern - supports percentage and milligram)
let cbn = null;
const cbnPercentMatch = fullText.match(/CBN:\s*(\d+\.?\d*)%/i);
if (cbnPercentMatch) {
    cbn = cbnPercentMatch[1];
} else {
    const cbnMgMatch = fullText.match(/CBN:\s*(\d+\.?\d*)\s*mg/i);
    if (cbnMgMatch) cbn = cbnMgMatch[1];
}
```

**Add stock quantity detection (after stock status check around line 595):**
```javascript
// Check stock status and extract urgency messages (WholesomeCo pattern)
let stockStatus = 'in_stock';
let stockQuantity = null;

const outOfStock = /* existing logic */;

if (outOfStock) {
    stockStatus = 'out_of_stock';
} else {
    // Check for low stock urgency message
    const stockMatch = fullText.match(/Only (\d+) left/i);
    if (stockMatch) {
        stockStatus = 'low_stock';
        stockQuantity = parseInt(stockMatch[1]);
    }
}
```

**Update product object (around line 598):**
```javascript
if (name && price && name.length > 3) {
    products.push({
        name: name,
        brand: brand,
        category: category,
        price: price,
        thc: thc,
        cbd: cbd,
        cbg: cbg,          // ADDED
        cbn: cbn,          // ADDED
        weight: weight,
        strainType: strainType,
        inStock: !outOfStock,
        stockStatus: stockStatus,      // ADDED
        stockQuantity: stockQuantity,  // ADDED
        url: url,          // ADDED
        html: el.outerHTML.substring(0, 500)
    });
}
```

**Update ScrapedProduct creation (around line 626):**
```python
product = ScrapedProduct(
    name=item["name"],
    brand=item.get("brand"),
    category=item.get("category", "other"),
    price=float(item["price"]),
    thc_percentage=self._parse_float(item.get("thc")),
    cbd_percentage=self._parse_float(item.get("cbd")),
    cbg_percentage=self._parse_float(item.get("cbg")),  # ADDED
    weight=item.get("weight"),
    in_stock=item.get("inStock", True),
    url=item.get("url"),  # ADDED
    raw_data=item  # CBN preserved here for future use
)
```

**Note:** CBN data will be in `raw_data` but not as a structured field since `ScrapedProduct` doesn't have a `cbn_percentage` field yet.

## Pre-Implementation: Selector Verification

Before making changes, verify Curaleaf's current selectors are accurate (following hybrid approach):

1. **Test current selectors in browser console** (visit https://ut.curaleaf.com/stores/curaleaf-ut-lehi/products/flower):
   ```javascript
   // Test product container selector
   document.querySelectorAll('[class*="product-item-list"]').length
   document.querySelectorAll('[class*="product-carousel"]').length

   // Verify these match the visible product count
   ```

2. **If selectors fail**, use DevTools to find actual class names:
   - Right-click product element → Inspect
   - Note the real class name
   - Update scraper with verified selector

3. **Document any selector changes** in implementation notes

## Verification

After implementing these changes, verify:

1. **Scraper runs successfully:**
   ```bash
   cd backend
   python -m pytest tests/ -k curaleaf -v
   ```

2. **Manual scraper test via admin dashboard:**
   - Navigate to `/admin/scrapers`
   - Trigger manual run for `curaleaf-lehi`
   - Verify:
     - Product count is higher (lazy loading works better)
     - Products have `url` field populated
     - CBG/CBD percentages extracted where available
     - No errors in scraper run logs

3. **Database verification:**
   ```python
   # Check that URLs are being saved
   from database import SessionLocal
   from models import Price
   db = SessionLocal()
   curaleaf_prices_with_url = db.query(Price).filter(
       Price.dispensary_id == 'curaleaf-lehi',
       Price.product_url.isnot(None)
   ).count()
   print(f"Curaleaf prices with URLs: {curaleaf_prices_with_url}")
   db.close()
   ```

4. **CBG/CBN data check:**
   ```python
   from database import SessionLocal
   from models import Product
   from sqlalchemy import func
   db = SessionLocal()
   products_with_cbg = db.query(Product).filter(
       Product.cbg_percentage.isnot(None)
   ).count()
   print(f"Products with CBG data: {products_with_cbg}")
   db.close()
   ```

## Success Criteria

- ✅ **Selectors verified** - Current selectors tested in browser console and confirmed accurate
- ✅ Curaleaf scraper completes without errors
- ✅ Product count matches or exceeds previous runs (better lazy loading)
- ✅ Product URLs are extracted and stored in Price records
- ✅ CBG cannabinoid data is extracted where available (with dual-format support)
- ✅ CBN data captured in raw_data for future use
- ✅ Stock quantity urgency messages are detected
- ✅ Wait times are increased to 4-5 seconds for lazy loading
- ✅ Double-check stabilization prevents premature exit from scroll loop
- ✅ All three Curaleaf location scrapers benefit (lehi, provo, springville)
- ✅ Extraction rates match or exceed WholesomeCo patterns (~95%+ for core fields)

## Notes

- These changes apply to all Curaleaf location scrapers since they inherit from the base `CuraleafScraper` class
- The `BaseScraper.cbg_percentage` field already exists in the schema (added previously for WholesomeCo)
- Product URLs flow through to Price records via `ScraperRunner._update_price()`
- If CBG/CBN fields aren't in ScrapedProduct dataclass, they'll need to be added (check `base_scraper.py`)
