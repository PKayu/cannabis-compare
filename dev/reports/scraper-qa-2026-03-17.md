# Scraper QA Report — 2026-03-17

_Two sessions ran today. This report covers the second session (evening) triggered by the
scheduled `scraper-run-and-qa` task. See the first-run data in the session 1 section below._

---

## Session 2 Run Summary (Scheduled QA Run)

All 13 scrapers triggered. Curaleaf scrapers were still completing at report time (consistent ~565s due to Playwright heavy pagination). `dragonfly-price` appears in run history as `warning (0 products)` — stale record from a disabled/removed scraper, safe to ignore.

| Scraper | Status | Products Found | Flags Created | Flag Rate | Duration |
|---------|--------|---------------|---------------|-----------|----------|
| WholesomeCo | ✅ success | 655 | 10 | 1.5% | 72s |
| Curaleaf (Lehi) | ✅ success | 385 | 1 | 0.3% | 562s |
| Curaleaf (Provo) | ⏳ running | — | — | — | ~565s |
| Curaleaf (Springville) | ⏳ running | — | — | — | ~565s |
| Beehive Farmacy (Brigham City) | ✅ success | 194 | 0 | 0.0% | 45s |
| Beehive Farmacy (Salt Lake City) | ✅ success | 133 | 0 | 0.0% | 43s |
| Zion Medicinal | ✅ success | 307 | 36 | 11.7% | 126s |
| Dragonfly Wellness (SLC) | ✅ success | 93 | 1 | 1.1% | 38s |
| Bloc Pharmacy (South Jordan) | ✅ success | 174 | 14 | 8.0% | 41s |
| Bloc Pharmacy (St. George) | ✅ success | 182 | 10 | 5.5% | 39s |
| The Flower Shop (Logan) | ✅ success | 234 | 0 | 0.0% | 59s |
| The Flower Shop (Ogden) | ✅ success | 227 | 0 | 0.0% | 38s |
| The Forest (Murray) | ✅ success | 269 | 0 | 0.0% | 44s |
| **TOTAL (completed)** | | **2,853** | **72** | **2.5%** | |

## Session 2 Quality Scores

| Check | Result | Status |
|-------|--------|--------|
| Run Health | 11/13 success; 2 Curaleaf still running (consistent ~9 min each) | ⚠️ |
| Overall Flag Rate | 2.5% (72/2,853) | ✅ |
| Highest Scraper Flag Rate | zion-medicinal 11.7% (36 flags; all auto_merged/auto_missed, 0 pending) | ⚠️ |
| URL Coverage | 6,628/6,628 — 100% | ✅ |
| Price Sanity | 39 prices <$5 (all $1.00 Curaleaf battery add-ons); 24 prices >$500 (Volcano Hybrid $700, Peak Pro — legitimate premium hardware) | ✅ |
| Field Coverage | 22 pending flags: all `data_cleanup` / `unknown_brand`, no missing weight/URL | ✅ |
| Pending Flag Backlog | 22 pending (well under 50 threshold) | ✅ |

**Flag breakdown (system-wide):** auto_merged=518, auto_missed=537, pending=22, dismissed=8, cleaned=2

Note: Zion Medicinal's 36 flags are all `match_review` type (auto_merged or auto_missed), none pending. Bloc flags are cross-dispensary match_review — expected behavior.

## Session 2 Fix Applied

### WholesomeCo — Non-product URL filter

**Issue**: The Playwright scraper was capturing a promotional banner element ("your first app order", $30, URL: `https://www.wholesome.co/app`) as a product. This generated a persistent low-confidence flag (score=0.42) on every run. Two similar non-product items ("Medical Card Educational Events!", "Discover Nano") had been manually dismissed in prior sessions.

**File**: `backend/services/scrapers/playwright_scraper.py`

**Change**: Added a URL path guard in `_extract_products()` (Python post-processing loop). Any item whose URL exists but does not contain `/shop/` is skipped with a debug-level log. All real WholesomeCo product URLs follow `https://www.wholesome.co/shop/{category}/{slug}`. Items with no URL pass through unaffected.

```python
# Skip non-product pages (e.g. promo banners linking to /app)
item_url = item.get("url")
if item_url and "/shop/" not in item_url:
    logger.debug(f"Skipping non-shop URL: {item_url} (name: {item.get('name', '')[:40]})")
    continue
```

**Expected impact**: Eliminates the recurring "your first app order" junk flag. No valid products affected (all product pages are under `/shop/`).

## Session 2 Deferred Improvements

### Zion Medicinal — Cross-dispensary match_review flags (11.7%)
All 36 flags are auto_merged/auto_missed with 0 pending. Root cause: cross-dispensary fuzzy matching for products shared across Utah dispensaries with slightly different name formatting. No code change needed until these start creating pending backlog.

### Bloc Pharmacy — Trailing category suffix in product names
Names like "Sour Chillz | Flower" cause cross-dispensary confidence to drop slightly. The Beehive base scraper already strips trailing ` | `, but the ` | Category` middle segment remains. Stripping everything after the first ` | ` would help cross-dispensary matching but risks truncating intentional descriptors. Deferred pending manual verification.

### Curaleaf — Slow run duration (~565s each)
Three Curaleaf scrapers each take ~9.4 min due to Playwright pagination. No data loss; throughput issue. Deferred until it causes scheduling conflicts.

---

## Session 1 Run Summary (Earlier Today — First-Time Runs for New Scrapers)

| Scraper | Status | Products Found | Flags | Flag Rate | Note |
|---------|--------|---------------|-------|-----------|------|
| wholesomeco | ✅ success | 325 | 21 | 6.5% | |
| curaleaf-lehi | ✅ success | 392 | 10 | 2.6% | |
| curaleaf-provo | ✅ success | 406 | 1 | 0.2% | |
| curaleaf-springville | ✅ success | 420 | 8 | 1.9% | |
| beehive-brigham-city | ✅ success | 196 | 10 | 5.1% | |
| beehive-slc | ✅ success | 132 | 0 | 0.0% | |
| zion-medicinal | ✅ success | 311 | 173 | 55.6% | ❌ High — fixes applied in session 1 |
| dragonfly-slc | ✅ success | 93 | 64 | 68.8% | ❌ High — DOM fallback suspected |
| bloc-south-jordan | ✅ success | 175 | 90 | 51.4% | ⚠️ New scraper |
| bloc-st-george | ✅ success | 183 | 58 | 31.7% | ⚠️ New scraper |
| flower-shop-logan | ✅ success | 234 | 114 | 48.7% | ⚠️ New scraper |
| flower-shop-ogden | ✅ success | 227 | 132 | 58.1% | ⚠️ New scraper |
| the-forest-murray | ✅ success | 269 | 135 | 50.2% | ⚠️ New scraper |

Session 1 fixes applied: Flower Shop multi-weight capture; Beehive DOM fallback name cleaning. See session 1 commit history for details.
