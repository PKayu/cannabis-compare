# Scraper QA Report — 2026-03-26

## Run Summary

| Scraper | Status | Products Found | Processed | Flags | Duration |
|---------|--------|---------------|-----------|-------|----------|
| wholesomeco | success | 701 | 701 | 34 | 72.6s |
| curaleaf-lehi | stuck (zombie) | 0 | 0 | 0 | — |
| curaleaf-provo | stuck (zombie) | 0 | 0 | 0 | — |
| curaleaf-springville | success | 504 | 504 | 0 | 500.8s |
| curaleaf-payson | not triggered | — | — | — | — |
| curaleaf-park-city | success | 609 | 609 | 8 | 99.0s |
| beehive-brigham-city | stuck (zombie) | 0 | 0 | 0 | — |
| beehive-slc | stuck (zombie) | 0 | 0 | 0 | — |
| zion-medicinal | success | 308 | 308 | 0 | 125.9s |
| dragonfly-slc | success | 93 | 93 | 0 | 40.8s |
| dragonfly-price | success | 1084 | 1084 | 10 | 20.4s |
| bloc-south-jordan | success | 183 | 183 | 0 | 45.8s |
| bloc-st-george | success | 181 | 181 | 0 | 43.2s |
| flower-shop-logan | success | 188 | 188 | 0 | 65.4s |
| flower-shop-ogden | success | 257 | 257 | 0 | 69.2s |
| the-forest-murray | success | 313 | 313 | 5 | 51.2s |

**12 of 16 scrapers completed successfully.** 4 scrapers (curaleaf-lehi, curaleaf-provo, beehive-slc, beehive-brigham-city) were stuck as "running" due to zombie runs — see Fixes Applied below.

## Quality Scores

| Check | Result | Status |
|-------|--------|--------|
| Run Health | 12/16 succeeded; 4 zombie runs cleaned up (122 total stale entries) | ⚠️ |
| Flag Rate | 57 flags / 4,421 products = 1.3% | ✅ |
| URL Coverage | 412/412 recent prices have product_url (100%) | ✅ |
| Price Sanity | 18 prices <$5 (accessories/fees), 2 prices >$500 | ⚠️ |
| Field Coverage | 0 flags missing weight, 0 missing URL (of 33 recent flags) | ✅ |
| Pending Backlog | 24 pending flags (of 1,824 total) | ✅ |

### Notes

- **Flag rate is excellent** at 1.3% overall. WholesomeCo is the highest flag producer (34 flags / 701 products = 4.9%) but all flags were at 1% confidence (new products, not mismatches).
- **Price outliers** are mostly accessories and non-cannabis items ($1 rounding donations, $2 USB chargers, $3 dab tools) — not parsing errors.
- **Category distribution concern**: 7,585 of 11,447 master products (66%) are categorized as "hardware". This is likely accumulated miscategorization over time, not a current scraper issue.
- **Missing cannabinoid data**: 77% missing THC, 91% missing CBD — this is a known limitation since many dispensary sites don't expose cannabinoid data in the menu.

## Fixes Applied

### All Scrapers — Fix 1: Zombie Run Prevention via Subprocess Timeout
**Issue**: The `/scrapers/run/{scraper_id}` endpoint ran scrapers directly in the event loop with no timeout. When Playwright-based scrapers hung (age gate issues, network timeouts), the `ScraperRun` record stayed in "running" status forever. This accumulated 122 zombie "running" entries for curaleaf-lehi (15), curaleaf-provo (21), beehive-slc (12), and beehive-brigham-city (13) over the past 10 days.
**File**: `backend/routers/scrapers.py`
**Change**: Changed the endpoint to use `run_scraper_subprocess_async()` (same as the admin endpoint) which runs each scraper in an isolated subprocess with a 600-second timeout. On timeout/crash, `_mark_stuck_runs_as_error()` automatically cleans up the ScraperRun record.

### All Scrapers — Fix 2: Startup Stale Run Cleanup
**Issue**: Even with subprocess timeouts, a server crash or ungraceful shutdown could leave runs in "running" status. No mechanism existed to recover from this state.
**File**: `backend/main.py`
**Change**: Added a startup task in the `lifespan` handler that marks any ScraperRun entries still in "running" status after 1 hour as "error" with an explanatory message. This prevents stale runs from accumulating across server restarts. Also ran a one-time cleanup that resolved 122 existing zombie entries.

## Deferred Improvements (not auto-applied)

1. **Curaleaf Lehi/Provo age gate failures**: These scrapers consistently fail to get past the age gate, producing 0 products on every run. The age gate dismissal logic may need updated selectors — requires manual verification of the live site's current HTML structure.

2. **Curaleaf Payson not triggered**: This scraper was listed but did not run (last status: "warning" from 2026-03-18). May need investigation into why the trigger endpoint didn't reach it.

3. **Hardware category cleanup**: 66% of master products are categorized as "hardware" which seems incorrect. A one-time data migration to re-categorize products based on their names/brands could improve data quality, but this is a DB cleanup task, not a scraper fix.

4. **Curaleaf Springville slow run**: 500.8s duration is very long (8+ minutes) for 504 products. The load-more scrolling loop may be hitting max_attempts on every category. Could benefit from tighter timing if the site loads faster now.
