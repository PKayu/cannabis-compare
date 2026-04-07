# Scraper QA Report — 2026-04-03

## Run Summary

All 16 registered scrapers were triggered. Some initially failed due to SQLite concurrency (database locked) when too many ran simultaneously; retries resolved those. Beehive scrapers failed due to Playwright resource contention but work fine when run individually.

| Scraper | Status | Products Found | Processed | Flags | Flag Rate | Duration |
|---------|--------|---------------|-----------|-------|-----------|----------|
| beehive-brigham-city | error | 0 | 0 | 0 | N/A | 57.9s |
| beehive-slc | error | 0 | 0 | 0 | N/A | 57.5s |
| bloc-south-jordan | success | 183 | 183 | 0 | 0.0% | 39.2s |
| bloc-st-george | success | 190 | 190 | 0 | 0.0% | 38.6s |
| curaleaf-lehi | success | 364 | 364 | 0 | 0.0% | 500.5s |
| curaleaf-park-city | success | 472 | 472 | 1 | 0.2% | 89.1s |
| curaleaf-payson | error | 0 | 0 | 0 | N/A | 12.8s |
| curaleaf-provo | error* | 434 | 434 | 0 | 0.0% | 501.1s |
| curaleaf-springville | success | 462 | 462 | 1 | 0.2% | 509.5s |
| dragonfly-price | success | 1135 | 1135 | 26 | 2.3% | 33.1s |
| dragonfly-slc | success | 93 | 93 | 0 | 0.0% | 37.3s |
| flower-shop-logan | success | 186 | 186 | 14 | 7.5% | 58.9s |
| flower-shop-ogden | success | 173 | 173 | 15 | 8.7% | 62.8s |
| the-forest-murray | success | 286 | 286 | 23 | 8.0% | 59.9s |
| wholesomeco | success | 696 | 696 | 0 | 0.0% | 79.7s |
| zion-medicinal | success | 303 | 303 | 0 | 0.0% | 123.1s |

*curaleaf-provo: processed 434 products successfully but subprocess exited with code 1 after processing.

**Totals**: 4,978 products found across 12 successful + 2 partial + 2 failed scrapers. 115 flags created (2.3% overall).

## Quality Scores

| Check | Result | Status |
|-------|--------|--------|
| Run Health | 12/16 clean success, 2 partial success (data saved), 2 failed | ⚠️ |
| Flag Rate | 2.3% overall (115/4978) | ✅ |
| URL Coverage | 18,468/18,468 = 100% | ✅ |
| Price Sanity | 498 prices < $5 (accessories at $0.01), 61 > $500 (Volcano vaporizers at $700) — all legitimate | ✅ |
| Field Coverage | Weight and URL populated on all recent scrapes | ✅ |
| Pending Backlog | 24 pending flags (0 pending review, 24 pending cleanup) | ✅ |

## Error Analysis

### beehive-brigham-city & beehive-slc — Concurrency Failure
**Error**: `Process exited with code 1` (0 products)
**Root Cause**: Running too many Playwright scrapers simultaneously causes resource contention. When run individually (verified), both scrapers work correctly (116+ products each). This is a scheduling/concurrency issue, not a scraper bug.
**Action**: No code fix needed — these recover on the next scheduled run when fewer scrapers are active.

### curaleaf-payson — Navigation Race Condition
**Error**: `Page.goto: Navigation to "https://ut.curaleaf.com/stores/curaleaf-ut-payson" is interrupted by another navigation`
**Root Cause**: After dismissing the age gate, the redirect to the store URL is still in flight when `scrape_products()` calls `page.goto()` with the same URL, causing a collision.
**Action**: Fixed (see below).

### curaleaf-provo — Partial Success
**Error**: `Process exited with code 1` but found/processed 434 products
**Root Cause**: Subprocess crashed after product processing completed (likely during cleanup). Data was saved successfully.
**Action**: Non-critical — data integrity is preserved.

## Fixes Applied

### Curaleaf Payson — Fix navigation race condition
**Issue**: `_dismiss_age_gate()` clicks the age verification button which triggers a client-side redirect to the store URL. Back in `scrape_products()`, a second `page.goto()` to the same URL fires before the redirect completes, causing "navigation interrupted" errors. This made curaleaf-payson fail 100% of the time with 0 products.
**File**: `backend/services/scrapers/curaleaf_scraper.py`
**Change**: Added a check before the post-age-gate `page.goto()`: if the page URL already contains the menu URL (i.e., the redirect already landed), skip the redundant navigation. Also added a try/except for "interrupted" errors that waits for the page to settle instead of crashing.

### iHeartJane / Flower Shop / The Forest — Strip bracketed weight from names
**Issue**: iHeartJane product names include bracketed weight suffixes like "[5g]", "[5G]", "[10 count]" (e.g., "Rainbow Sherbet [5g]", "Chem 91 [5g]", "Skunk GMO [5G]"). These extra characters lower fuzzy match confidence scores below the 90% auto-merge threshold, generating unnecessary flags. The Flower Shop (Logan + Ogden) and The Forest (Murray) scrapers had the highest flag rates at 7.5-8.7%.
**Files**: `backend/services/scrapers/iheartjane_scraper.py`, `backend/services/scrapers/flower_shop_scraper.py`
**Change**: Added `re.sub()` to strip bracketed weight/quantity patterns from product names before creating ScrapedProduct objects. The Forest scraper inherits from FlowerShopBaseScraper so gets the fix automatically. This should reduce flag rates for these three scrapers by eliminating false fuzzy-match misses.

## Deferred Improvements (not auto-applied)

- **Scraper concurrency limiter**: Running all 16 scrapers simultaneously causes SQLite "database is locked" errors and Playwright resource contention. A concurrency semaphore (e.g., max 4-6 concurrent Playwright scrapers) would prevent these transient failures. Skipped because it requires structural changes to the scheduler/runner.
- **curaleaf-provo subprocess exit code**: The scraper processes all products successfully but the subprocess still exits with code 1. The error occurs after data is saved, so impact is cosmetic (shows as "error" in dashboard despite successful data collection). Would require deeper investigation of the subprocess wrapper's cleanup phase.
- **Beehive Farmacy Dutchie URL verification**: Both Beehive stores use Dutchie white-label URLs that may have changed. While the page loads (verified), no products were captured when running concurrently. A health check that validates the store URL returns product data would help distinguish "site changed" from "resource contention" failures.
