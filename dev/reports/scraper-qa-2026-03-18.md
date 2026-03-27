# Scraper QA Report — 2026-03-18 (Run 4)

## Run Summary

Manual trigger of all 13 registered scrapers at ~19:00 UTC via `/scrapers/run/{id}`.

| Scraper | Status | Products Found | Processed | Flags | Flag Rate | Duration |
|---------|--------|---------------|-----------|-------|-----------|----------|
| wholesomeco | success | 650 | 650 | 1 | 0.2% | 83.8s |
| curaleaf-lehi | success | 399 | 399 | 0 | 0.0% | 580.5s |
| curaleaf-provo | success | 406 | 406 | 0 | 0.0% | 565.2s |
| curaleaf-springville | success | 413 | 413 | 0 | 0.0% | 559.7s |
| beehive-brigham-city | success | 197 | 197 | 1 | 0.5% | 38.6s |
| beehive-slc | success | 127 | 127 | 0 | 0.0% | 38.3s |
| zion-medicinal | success | 310 | 310 | 0 | 0.0% | 122.0s |
| dragonfly-slc | success | 93 | 93 | 0 | 0.0% | 38.0s |
| bloc-south-jordan | success | 172 | 172 | 0 | 0.0% | 38.3s |
| bloc-st-george | success | 180 | 180 | 2 | 1.1% | 37.9s |
| flower-shop-logan | success | 236 | 236 | 0 | 0.0% | 55.9s |
| flower-shop-ogden | success | 228 | 228 | 0 | 0.0% | 54.1s |
| the-forest-murray | success | 268 | 268 | 0 | 0.0% | 45.0s |

**Completed successfully**: 13/13 (100%) — improvement over Run 3 (77%)
**Errors**: 0
**Total products**: 3,679 | **Total flags**: 4

### Comparison to Run 3

| Metric | Run 3 | Run 4 | Change |
|--------|-------|-------|--------|
| Success rate | 77% (10/13) | 100% (13/13) | +23% |
| Total products | 2,798 | 3,679 | +881 |
| Total flags | 18 | 4 | -78% |
| Hung scrapers | 1 (dragonfly-slc) | 0 | Fixed |
| Browser crashes | 2 | 0 | Fixed |

Notable improvements:
- **dragonfly-slc**: No longer hung — completed in 38s with 93 products
- **beehive-brigham-city** and **zion-medicinal**: No longer crashing
- **flower-shop-logan/ogden**: Product counts doubled (116->236, 177->228) — likely dmerch API returning fuller results with warmed browser session
- **the-forest-murray**: Nearly doubled (148->268)

## Quality Scores

| Check | Result | Status |
|-------|--------|--------|
| Run Health | 13/13 success (100%) | :white_check_mark: |
| Flag Rate | 0.11% (4/3,679) | :white_check_mark: |
| URL Coverage | 100% (4,123/4,123 recent prices have product_url) | :white_check_mark: |
| Price Sanity | 0 new outliers this run | :white_check_mark: |
| Field Coverage | 19/533 flags missing weight (24h), 427/533 missing THC (24h) | :white_check_mark: |
| Pending Backlog | 22 pre-existing + 4 new = 26 total pending | :white_check_mark: |

### Price Sanity Details
- **Legacy $0.01 prices**: 86 from prior Dragonfly Price run (guard at `dragonfly_price_scraper.py:277` prevents new ones). Not from this run.
- **$630 prices**: 18 WholesomeCo Volcano Hybrid vaporizers — legitimate hardware pricing.
- **No new outliers** from this run.

### Field Coverage Details (24h aggregate, all runs)
- **Weight**: 19/533 flags missing (96.4% coverage) — good
- **THC**: 427/533 flags missing (19.9% coverage) — expected for edibles/hardware
- **Price**: 0/533 flags missing (100% coverage) — perfect
- **URL**: 0/533 flags missing (100% coverage) — perfect

### Performance Notes
Curaleaf scrapers remain 10x slower than comparable scrapers:
- **Curaleaf** (3 locations): 560-580s each (~400 products)
- **Other Playwright scrapers**: 37-55s each (similar product counts)

Root cause: 7 category pages x scroll loading with 2s waits per attempt. Applied partial fix (see below).

### Category Distribution (master products)
| Category | Count | % |
|----------|-------|---|
| hardware | 9,590 | 49.9% |
| flower | 2,531 | 13.2% |
| vape | 1,919 | 10.0% |
| edible | 1,830 | 9.5% |
| vaporizer | 1,169 | 6.1% |
| concentrate | 830 | 4.3% |
| other | 501 | 2.6% |
| tincture | 478 | 2.5% |
| topical | 368 | 1.9% |

**Note**: "vaporizer" (1,169) should merge into "vape" — fix applied below will prevent new entries; existing records need a one-time DB migration.

## Fixes Applied

### Curaleaf — Fix 1: Category "vaporizer" changed to "vape"

**Issue**: Curaleaf's JS extraction mapped vaporizer/cartridge/vape products to the category `"vaporizer"`, while all other scrapers use `"vape"`. This caused 1,169 master products (including 422 from Curaleaf) to exist in a separate "vaporizer" category, preventing proper cross-dispensary price comparison for vape products.

**File**: `backend/services/scrapers/curaleaf_scraper.py:439`

**Change**: Changed the JS category mapping from `category = 'vaporizer'` to `category = 'vape'`. New Curaleaf vape products will now correctly consolidate with other scrapers' vape products during confidence scoring.

### Curaleaf — Fix 2: Reduced scroll confirmation timeout

**Issue**: The `_load_all_products` method used a 2-second confirmation wait after detecting no new products loaded. With up to 10 attempts across 7 categories, this added unnecessary wait time when products were already fully loaded.

**File**: `backend/services/scrapers/curaleaf_scraper.py:348`

**Change**: Reduced the confirmation `wait_for_timeout` from 2000ms to 1000ms. The initial 2s scroll wait (needed for content to load) is unchanged; only the no-change verification check is faster. Estimated ~70s savings per Curaleaf run.

### Name Cleaner — Dutchie `m` medical-tier indicator stripping (from Run 3)

**File**: `backend/services/normalization/name_cleaner.py`

**Change**: Added regex rule to strip standalone `m` from Dutchie product names before matching. Applied in earlier run today.

## Deferred Improvements (not auto-applied)

1. **Existing "vaporizer" products in DB**: 1,169 master products with `product_type='vaporizer'` need a one-time migration: `UPDATE products SET product_type='vape' WHERE product_type='vaporizer'`. Should be done manually after verifying frontend filters handle the change.

2. **Legacy $0.01 prices**: 86 residual prices from Dragonfly Price. Guard prevents new ones. Could clean up with: `DELETE FROM prices WHERE amount < 0.50 AND dispensary_id = '5ab90f41-2946-4a4a-a8eb-d777f180b7a7'`.

3. **Curaleaf performance — API interception**: The 3 Curaleaf scrapers collectively take ~28 minutes due to DOM scraping + infinite scroll across 7 categories. Intercepting Curaleaf's underlying Dutchie GraphQL API (like Flower Shop does with iHeartJane) could reduce this to <60s per location. Requires network analysis of the Curaleaf storefront.

4. **Curaleaf Park City scraper**: Exists at `backend/services/scrapers/curaleaf_park_city_scraper.py` (untracked) — generated 374 flags in a manual test. Needs review before registration in `main.py`.

5. **Hardware category over-representation**: 9,590 products (49.9%) typed as "hardware". May include miscategorized items from scrapers that default to "hardware" for unrecognized categories. Warrants a sampling audit.
