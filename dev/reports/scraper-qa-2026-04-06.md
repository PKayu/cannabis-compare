# Scraper QA Report — 2026-04-06

**Note**: Backend was not running; analysis based on database query of most recent runs (2026-04-04 ~22:43 UTC). Scrapers were not re-triggered.

## Run Summary

| Scraper | Status | Products Found | Processed | Flags | Duration |
|---------|--------|---------------|-----------|-------|----------|
| wholesomeco | success | 695 | 695 | 0 | ~81s |
| beehive-brigham-city | success | 202 | 202 | 0 | ~42s |
| beehive-slc | success | 133 | 133 | 1 | ~44s |
| zion-medicinal | success | 300 | 300 | 0 | ~125s |
| dragonfly-slc | success | 93 | 93 | 0 | ~40s |
| dragonfly-price | success | 1134 | 1134 | 0 | ~23s |
| bloc-south-jordan | success | 182 | 182 | 3 | ~40s |
| bloc-st-george | success | 195 | 195 | 9 | ~46s |
| flower-shop-logan | success | 259 | 259 | 0 | ~57s |
| flower-shop-ogden | success | 241 | 241 | 0 | ~57s |
| the-forest-murray | success | 277 | 277 | 0 | ~47s |
| curaleaf-lehi | success | 350 | 350 | 1 | ~507s |
| curaleaf-park-city | success | 500 | 500 | 0 | ~83s |
| curaleaf-provo | **error** | 0 | 0 | 0 | ~503s |
| curaleaf-springville | **error** | 0 | 0 | 0 | ~503s |
| curaleaf-payson | **warning** | 0 | 0 | 0 | ~588s |

**Totals**: 13/16 scrapers successful, 4,561 products scraped, 14 flags created

## Quality Scores

| Check | Result | Status |
|-------|--------|--------|
| Run Health | 13/16 success; 2 errors (Provo, Springville), 1 warning (Payson) | ⚠️ |
| Flag Rate | 0.3% (14/4561) | ✅ |
| URL Coverage | 100% (2858/2858 recent prices have product_url) | ✅ |
| Price Sanity | 162 < $5, 22 > $500 — see notes below | ⚠️ |
| Field Coverage | 0 missing weight, 0 missing URL, 0 missing price in recent flags | ✅ |
| Pending Backlog | 24 pending flags | ✅ |

### Price Sanity Notes

**Low prices ($1.00)**: Non-cannabis service/utility items being scraped as products:
- "Rounding donation" (Dragonfly Price) — $1.00
- "DF Herbal Viewer" (Dragonfly Price) — $1.00
- "Dept of Health Transaction Fee" (Dragonfly Price)
- "Scribe Ink Replacement" (Zion Medicinal) — $1.00
- Various accessories (Zion, Bloc) at $2-4

**High prices ($700)**: Volcano Hybrid dry herb vaporizers from WholesomeCo — legitimate hardware prices. No parsing errors.

### Failing Scrapers Detail

**curaleaf-provo**: Was working until 2026-04-04 04:43 (441 products), then consistently errors with "Process exited with code 1". Likely a Curaleaf site change affecting the Provo location.

**curaleaf-springville**: Intermittent — alternates between success (434-462 products) and failure. Flaky age gate dismissal suspected.

**curaleaf-payson**: Has NEVER succeeded across all 24 recorded runs. Every run takes ~590s (near the 600s timeout) and finds 0 products. The Payson location likely does not have a functional online menu at the /stores/ URL. Should be disabled to stop wasting ~10 min of compute every 2 hours.

## Fixes Applied

### Dragonfly Price — Fix 1: Filter non-product service items

**Issue**: Non-product items like "Rounding donation" ($1), "DF Herbal Viewer" ($1), and "Dept of Health Transaction Fee" were being scraped and stored as cannabis products, polluting price data with sub-$5 entries.
**File**: `backend/services/scrapers/dragonfly_price_scraper.py`
**Change**: Added `_NON_PRODUCT_PATTERNS` regex class attribute that matches known non-product service items by name. The `_parse_product` method now returns `None` for matching items, preventing them from entering the pipeline. This removes 3 recurring false products per run (~9 price records per day).

## Deferred Improvements (not auto-applied)

1. **Disable curaleaf-payson scraper**: It has never returned products and wastes ~10 minutes per run (12x/day = 2 hours of compute daily). Requires changing `enabled=True` to `enabled=False` in the `@register_scraper` decorator, but the `register_scraper` decorator doesn't currently support an `enabled` parameter in production — needs manual intervention or a registry update.

2. **Curaleaf Provo site investigation**: The Provo scraper broke on 2026-04-04 and needs manual verification of whether `https://ut.curaleaf.com/stores/curaleaf-ut-provo` still exists. If Curaleaf has migrated Provo to the SweedPOS platform (like Park City), a new scraper class would be needed.

3. **Curaleaf Springville flakiness**: The intermittent failures (50% success rate) suggest the age gate dismissal is unreliable for this location. Could benefit from retry logic or a longer hydration wait, but needs live testing to verify.

4. **Zion Medicinal accessory items**: Items like "Scribe Ink Replacement" ($1), "USB Chargers 510 Threading" ($3.50), and "Integra 4G 62% Humidipack" ($2) are hardware/accessories from the Dutchie menu. These are already categorized as "hardware" which is correct, but a minimum price threshold for the hardware category could filter truly non-cannabis utility items. Deferred because these items don't generate flags and the threshold would need careful tuning.

5. **Bloc St. George high flag rate**: 9 flags / 195 products (4.6%) — highest among working scrapers. All flags are `match_review` type (near-miss cross-dispensary matches, 65-84% confidence). These appear to be genuine new products not yet in the catalog rather than scraper parsing issues. No code fix needed — admin should review and approve/dismiss the backlog.
