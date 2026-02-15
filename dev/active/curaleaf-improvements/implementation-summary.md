# Curaleaf Scraper Improvements - Implementation Summary

**Date**: 2026-02-14
**Status**: Code Changes Complete - Ready for Testing
**Modified File**: `backend/services/scrapers/curaleaf_scraper.py`

## Changes Implemented

### 1. Enhanced Lazy Loading Performance (`_load_all_products()`)

**Lines Modified**: 314-338

```python
# BEFORE: 2-second waits
await page.wait_for_timeout(2000)
await page.wait_for_timeout(2000)  # Double-check wait

# AFTER: 4-5 second waits (WholesomeCo pattern)
await page.wait_for_timeout(4000)  # Base wait increased
await page.wait_for_timeout(5000)  # Double-check wait increased
```

**Impact**: Better handling of slow lazy-loading content, should capture more products per run

---

### 2. Product URL Extraction

**Lines Added**: 391-400 (JavaScript)

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

**Impact**:
- Users can click direct product links instead of searching dispensary sites
- Admins can verify flagged items at the source
- URLs stored in `Price.product_url` field

---

### 3. CBG Cannabinoid Extraction

**Lines Added**: 424-431 (JavaScript)

```javascript
// Extract CBG (WholesomeCo pattern - supports percentage and milligram)
let cbg = null;
const cbgPercentMatch = fullText.match(/CBG:\\s*(\\d+\\.?\\d*)%/i);
if (cbgPercentMatch) {
    cbg = cbgPercentMatch[1];
} else {
    const cbgMgMatch = fullText.match(/CBG:\\s*(\\d+\\.?\\d*)\\s*mg/i);
    if (cbgMgMatch) cbg = cbgMgMatch[1];
}
```

**Python ScrapedProduct**: Added `cbg_percentage=self._parse_float(item.get("cbg"))`

**Impact**: Captures CBG data in both percentage (flower) and milligram (edibles) formats

---

### 4. CBN Cannabinoid Extraction (raw_data only)

**Lines Added**: 433-440 (JavaScript)

```javascript
// Extract CBN (WholesomeCo pattern - stored in raw_data)
let cbn = null;
const cbnPercentMatch = fullText.match(/CBN:\\s*(\\d+\\.?\\d*)%/i);
if (cbnPercentMatch) {
    cbn = cbnPercentMatch[1];
} else {
    const cbnMgMatch = fullText.match(/CBN:\\s*(\\d+\\.?\\d*)\\s*mg/i);
    if (cbnMgMatch) cbn = cbnMgMatch[1];
}
```

**Note**: CBN is captured in `raw_data` for future use. No structured field exists yet (requires model migration to add `cbn_percentage`).

---

### 5. Stock Quantity Detection

**Lines Modified**: 620-638

```javascript
// BEFORE: Simple binary check
const outOfStock = el.classList.contains('out-of-stock') || ...;

// AFTER: WholesomeCo pattern with urgency detection
let stockStatus = 'in_stock';
let stockQuantity = null;

const outOfStock = ...;

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
```

**Impact**: Captures "Only X left" urgency messages for frontend display

---

### 6. Updated Product Object (JavaScript)

**Lines Modified**: 644-658

**New fields added**:
- `cbg: cbg`
- `cbn: cbn`
- `stockStatus: stockStatus`
- `stockQuantity: stockQuantity`
- `url: url`

**Modified fields**:
- `inStock: stockStatus === 'in_stock'` (uses new stockStatus variable)

---

## Scrapers Affected

All three Curaleaf location scrapers inherit from `CuraleafScraper`, so they all benefit:

1. **curaleaf-lehi** - Lehi, UT location
2. **curaleaf-provo** - Provo, UT location
3. **curaleaf-springville** - Springville, UT location

---

## Testing Required

### Manual Testing via Admin Dashboard

1. Navigate to http://localhost:4002/admin/scrapers
2. Trigger manual run for `curaleaf-lehi`
3. Check scraper run logs for:
   - ✅ No errors
   - ✅ Product count (should be higher than previous runs)
   - ✅ Successful completion status

### Database Verification

```python
# Verify URLs are being captured
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

```python
# Verify CBG data is being captured
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

---

## Expected Results

- ✅ Product count matches or exceeds previous runs (better lazy loading)
- ✅ ~95%+ of products have URLs populated
- ✅ CBG data extracted for products that display it
- ✅ CBN data preserved in `raw_data` for products that display it
- ✅ Stock quantity captured for "Only X left" messages
- ✅ No scraper errors in logs
- ✅ All three location scrapers work correctly

---

## Rollback Plan

If issues occur, revert `backend/services/scrapers/curaleaf_scraper.py` to previous commit:

```bash
git checkout HEAD~1 backend/services/scrapers/curaleaf_scraper.py
```

---

## Next Steps

1. ✅ Code changes complete
2. ⏳ Test via admin dashboard
3. ⏳ Verify database records
4. ⏳ Monitor scraper runs for 24-48 hours
5. ⏳ Update CLAUDE.md if needed
