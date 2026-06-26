# Scraper QA Report — 2026-04-11

## Run Summary

All 15 enabled scrapers triggered sequentially (parallel fire, sequential execution). All completed with status `success`. `curaleaf-payson` was disabled and skipped.

| Scraper | Status | Products Found | Processed | Flags | Duration |
|---------|--------|---------------|-----------|-------|----------|
| wholesomeco | ✅ success | 693 | 693 | 0 | 70s |
| curaleaf-lehi | ✅ success | 427 | 427 | 0 | 497s |
| curaleaf-provo | ✅ success | 441 | 441 | 0 | 512s |
| curaleaf-springville | ✅ success | 427 | 427 | 0 | 505s |
| beehive-brigham-city | ✅ success | 190 | 190 | 0 | 40s |
| beehive-slc | ✅ success | 113 | 113 | 0 | 38s |
| zion-medicinal | ✅ success | 278 | 278 | 0 | 121s |
| dragonfly-slc | ✅ success | 93 | 93 | 0 | 37s |
| bloc-south-jordan | ✅ success | 189 | 189 | 0 | 39s |
| bloc-st-george | ✅ success | 193 | 193 | 0 | 40s |
| flower-shop-logan | ✅ success | 250 | 250 | 0 | 39s |
| flower-shop-ogden | ✅ success | 240 | 240 | 0 | 39s |
| the-forest-murray | ✅ success | 269 | 269 | 0 | 44s |
| dragonfly-price | ✅ success | 1,152 | 1,152 | 0 | 25s |
| curaleaf-park-city | ✅ success | 519 | 519 | 0 | 86s |

**Note**: Curaleaf (Lehi/Provo/Springville) durations are 497–512s due to multi-category Playwright scraping with full scroll-load; all other scrapers use API interception or GraphQL.

## Quality Scores

| Check | Result | Status |
|-------|--------|--------|
| Run Health | 15/15 scrapers succeeded, 0 errors, 0 silent failures | ✅ |
| Flag Rate | 0 flags created / 5,474 products processed = 0% | ✅ |
| URL Coverage | 24,251 / 24,251 prices have `product_url` = 100% | ✅ |
| Price Sanity | 10 prices at $0.01 (historical MiniNail items, filter already in place); $600 Peak Pro 2 dab rig is legitimate | ⚠️ |
| Field Coverage | 24 pending flags total, all `data_cleanup` / `unknown_brand` type | ✅ |
| Pending Backlog | 24 pending flags (all cleanup, none blocking review) | ✅ |

### Additional Quality Notes

**THC Coverage by Dispensary** (% of price records with `thc_percentage` populated):
- Dragonfly Wellness SLC: 97.8%
- Curaleaf Lehi/Springville: ~78–79%
- Flower Shop Logan/Ogden: ~67–72%
- WholesomeCo: 37.4% (hardware-heavy inventory)
- Zion Medicinal: 8.2% (2,924 hardware + edibles are mg-dosed, not %; flower/vape = 95–100%)

The overall 79.8% missing THC figure from `/api/admin/scrapers/quality/metrics` is dominated by hardware accessories (15,699 master products = 77.7% of all products) which correctly have no THC value. Cannabis-specific products generally have good THC coverage.

**Category Inconsistency (pre-existing)**:
- `vaporizer`: 1,258 master products (from PlaywrightScraper / WholesomeCo)
- `vape`: 1,166 master products (from Dutchie/Beehive/Bloc scrapers)
- These represent the same product type — split by scraper origin
- Zero `pre-roll` products in entire DB despite Curaleaf having a pre-rolls category page

## Fixes Applied

### playwright_scraper.py — Fix 1: Category "vaporizer" → "vape" consistency

**Issue**: `PlaywrightScraper._map_category()` and the inline DOM extraction script mapped "vape"/"cartridge" to "vaporizer". All other scrapers (Beehive, Bloc, Dragonfly, iHeartJane) use "vape". This caused a 1,258 vs 1,166 split for the same product type, showing as two separate categories in the frontend.

**File**: `backend/services/scrapers/playwright_scraper.py`

**Change**: Updated both locations (Python `_map_category` dict at line 255–256 and inline JS at line 597) to output "vape" instead of "vaporizer". Future WholesomeCo scrape runs will create new products with type "vape"; existing "vaporizer" records remain and will be cleaned up in a future data migration.

### curaleaf_scraper.py — Fix 2: Add "pre-rolls" category to Curaleaf scraper

**Issue**: The Curaleaf scraper `CATEGORIES` list included flower, vaporizers, edibles, concentrates, tinctures, topicals, and accessories — but not "pre-rolls". The inline JS at line 479 already recognized pre-roll products in aria-labels, but the scraper never navigated to the pre-rolls category page (`/products/pre-rolls`), so zero pre-roll products existed in the DB despite Curaleaf selling them.

**File**: `backend/services/scrapers/curaleaf_scraper.py`

**Change 1**: Added "pre-rolls" to `CATEGORIES` (between flower and vaporizers).

**Change 2**: Added a category override block alongside the existing accessories→hardware override: when processing the pre-rolls page, all extracted products are forced to `category = "pre-roll"` (the JS inference might otherwise categorize them as "flower" since they contain flower keywords).

## Deferred Improvements (not auto-applied)

1. **Data migration: vaporizer → vape** — 1,258 existing `product_type='vaporizer'` master products and their variants should be updated to `product_type='vape'`. Skipped here because it requires a DB migration or admin script, not a scraper code change.

2. **Curaleaf Park City pre-rolls** — `curaleaf_park_city_scraper.py` uses the SweedPOS platform and its `_CATEGORIES` list also lacks pre-rolls. Adding the correct SweedPOS `category_id` for pre-rolls requires verifying the numeric ID from a live GetProductList API call. Category IDs are static and platform-specific (e.g., flower=1854, vape=1863). Cannot safely add without manual verification.

3. **Zion Medicinal / Dutchie edible THC coverage (2.7%)** — Edibles at Zion are dosed in mg (e.g., "Boost- Tablets 100mg (20-Pack | 5mg each)"). The Dutchie API doesn't return `THCContent` for mg-dosed products; the info is embedded in the product name. Parsing mg from names is feasible but requires careful regex work to avoid false positives and would store mg content only (not a percentage), which is already done via `thc_content` field. Not a blocker.

4. **$0.01 price records (10 items)** — Historical MiniNail hardware entries from Dragonfly Price. The scraper already filters `price < 0.50` for new runs (added in a prior session). These legacy records should be deleted via admin script. Skipped here as data cleanup, not a scraper bug.

---

## Run Session #2 — 2026-04-11 ~13:42 UTC

Second automated QA session of the day. All 15 enabled scrapers triggered simultaneously via admin API.

| Scraper | Status | Products Found | Processed | Flags | Duration |
|---------|--------|---------------|-----------|-------|----------|
| wholesomeco | ✅ success | 695 | 695 | 0 | 92s |
| curaleaf-lehi | ❌ error | 0 | 0 | 0 | 580s |
| curaleaf-provo | ✅ success | 504 | 504 | 0 | 588s |
| curaleaf-springville | ❌ error | 0 | 0 | 0 | 599s |
| beehive-brigham-city | ✅ success | 207 | 207 | 0 | 43s |
| beehive-slc | ✅ success | 129 | 129 | 0 | 42s |
| zion-medicinal | ✅ success | 278 | 278 | 0 | 131s |
| dragonfly-slc | ✅ success | 93 | 93 | 0 | 38s |
| bloc-south-jordan | ✅ success | 191 | 191 | 0 | 40s |
| bloc-st-george | ✅ success | 193 | 193 | 0 | 40s |
| flower-shop-logan | ✅ success | 249 | 249 | 0 | 61s |
| flower-shop-ogden | ✅ success | 240 | 240 | 0 | 60s |
| the-forest-murray | ✅ success | 269 | 269 | 0 | 65s |
| dragonfly-price | ✅ success | 1152 | 1152 | 0 | 49s |
| curaleaf-park-city | ✅ success | 519 | 519 | 0 | 103s |

**Total this session**: 4,719 products across 13 successful scrapers.

### Session #2 Errors

**curaleaf-springville**: Subprocess timed out at 599s. Today's run history: success at 05:58 (504s), success at 05:35 (520s), **error at 09:35** (599s), success at 11:35 (581s), **error at 13:35** (599s). Pattern shows the scraper runs right at the edge of the 600s limit — small page-load variance determines pass/fail.

**curaleaf-lehi**: `sqlite3.OperationalError: database is locked` during `INSERT INTO scraper_runs` at startup. Cause: all 15 scrapers triggered simultaneously, creating a burst of concurrent SQLite writes. WAL mode is configured but under extreme burst concurrency the serialization can still exceed 30s. Same run succeeded in the next scheduled cycle (~5 min later).

### Session #2 Quality Scores

| Check | Result | Status |
|-------|--------|--------|
| Run Health | 2 errors (springville timeout, lehi db-lock) | ⚠️ |
| Flag Rate | 0 flags / 4,719 products = 0% | ✅ |
| URL Coverage | 25,768 / 25,768 prices have product_url = 100% | ✅ |
| Price Sanity | 843 <$5 (small hardware accessories); 109 >$500 (premium vaporizers) — all legitimate | ✅ |
| Field Coverage | 24 pending flags, 0 missing URL, 3 missing weight (tinctures) — all pre-existing | ✅ |
| Pending Flag Backlog | 24 pending (21 Dragonfly SLC, 2 Zion, 1 WholesomeCo — all data_cleanup type) | ✅ |

### Session #2 Fix Applied

**curaleaf_scraper.py — Reorder `_wait_for_products` selector list**

**Issue**: `_wait_for_products()` tried 6 legacy selectors before reaching `[class*="ProductCard"]` (the current Mar 2026+ layout). Each non-matching selector waits the full `timeout=10000ms` (10s). Per category: 6 × 10s = **60s wasted**. Across 8 categories: **~480s wasted per run**.

This is why Curaleaf runs take 497–588s despite relatively fast scraping logic — nearly all of the time was spent in selector polling, not page loading or product extraction.

**Root cause of Springville timeouts**: The 480s overhead left only ~120s of safety margin. Any slow page load or extra age-gate retry (33s each) pushed it past the 600s limit.

**Change**: Moved `[class*="ProductCard"]` and `[class*="ProductItem"]` to positions 1 and 2. Legacy selectors kept as fallbacks.

**Expected impact**: All Curaleaf locations should drop from ~500s to ~80–120s per run. Springville timeout issue should be resolved.

---

## Run Session #3 — 2026-04-11 ~14:06 UTC

Third automated QA session. All 15 enabled scrapers triggered concurrently via `/scrapers/run/{id}`. Session #2 fix (selector reorder) confirmed effective — Curaleaf runs completed in 95–118s.

| Scraper | Status | Products Found | Flags | Duration |
|---------|--------|---------------|-------|----------|
| wholesomeco | ✅ success | 695 | 0 | 108s |
| curaleaf-lehi | ✅ success | 488 | 0 | 118s |
| curaleaf-provo | ✅ success | 504 | 0 | 100s |
| curaleaf-springville | ✅ success | 488 | 0 | 95s |
| beehive-brigham-city | ✅ success | 207 | 0 | 42s |
| beehive-slc | ✅ success | 129 | 0 | 38s |
| zion-medicinal | ✅ success | 278 | 0 | 121s |
| dragonfly-slc | ✅ success | 93 | 0 | 38s |
| bloc-south-jordan | ✅ success | 191 | 0 | ~60s |
| bloc-st-george | ✅ success | 193 | 0 | 45s |
| flower-shop-logan | ✅ success | 249 | 0 | 41s |
| flower-shop-ogden | ✅ success | 240 | 0 | 43s |
| the-forest-murray | ✅ success | 269 | 0 | 65s |
| dragonfly-price | ✅ success | 1152 | 0 | 30s |
| curaleaf-park-city | ✅ success | 519 | 0 | 87s |

**Total this session**: 5,517 products across 15 scrapers. 0 errors. 0 new flags.

### Session #3 Quality Scores

| Check | Result | Status |
|-------|--------|--------|
| Run Health | 15/15 success, 0 errors | ✅ |
| Flag Rate | 0% (0 / 5,517 products) | ✅ |
| URL Coverage | 100% of sampled prices have product_url | ✅ |
| Price Sanity | 1 pre-existing $1.00 Jams Edible (Dragonfly SLC) — not new | ⚠️ |
| Field Coverage | 24 pending flags (all pre-existing March data_cleanup) | ✅ |
| Pending Flag Backlog | 24 pending — all pre-existing, no new flags today | ✅ |
| Curaleaf 7-day reliability | 47–53% (inflated by pre-fix failures earlier today) | ⚠️ |

### Session #3 Fixes Applied

**Fix 1 — Increase subprocess timeout to 900s**

**Issue**: Even after the selector-reorder fix, the subprocess timeout remained at 600s. On slow-network days or with extra age-gate retry (33s each), Curaleaf runs could still push toward 600s. The 600s limit also affected the admin fire-and-forget runner.

**Files**:
- `backend/routers/scrapers.py:278` — `timeout=600` → `timeout=900`
- `backend/routers/admin_scrapers.py:203` — `timeout=600` → `timeout=900`

**Change**: Increased subprocess timeout from 600s to 900s in both endpoints. With Curaleaf runs now completing in 95–120s, this is generous overhead, but ensures even a worst-case triple age-gate retry (~100s) + slow product loading won't cause a timeout.

---

**Fix 2 — Curaleaf age gate: networkidle → domcontentloaded**

**Issue**: The age gate dismissal used `wait_until="networkidle"` which blocks until all background network activity settles. Curaleaf's age gate page has continuous analytics/XHR traffic that can delay `networkidle` by 5–10s per attempt (3 attempts = up to 30s). Same pattern in the main store re-navigation and category page age-gate re-navigation.

**File**: `backend/services/scrapers/curaleaf_scraper.py`

**Changes**:
- Line 237: age gate `goto()` `networkidle` → `domcontentloaded`
- Line 238: hydration wait `3000ms` → `2000ms`
- Line 106: main store re-navigation `networkidle` → `domcontentloaded`
- Line 135: category age-gate re-navigation `networkidle` → `domcontentloaded`

**Safety**: The React component check (`wait_for_selector` with 5s timeout) already handles the remaining hydration time — `domcontentloaded` is sufficient to start polling for the button.

**Expected impact**: ~10–30s saved per run on the age gate path (more on retry runs). Cumulative with the selector-reorder fix, Curaleaf runs should now complete in 90–150s on typical days.
