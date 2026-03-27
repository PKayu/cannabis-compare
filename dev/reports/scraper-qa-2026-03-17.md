# Scraper QA Report — 2026-03-17

_Three sessions ran today. Session 3 (late evening) is the latest scheduled `scraper-run-and-qa` run._

---

## Session 3 Run Summary (Late Evening Scheduled QA Run)

All 13 scrapers triggered. Curaleaf scrapers still slow (~570s). The 7 newer scrapers (zion through forest) did not produce new run records — likely because they had run recently (14h ago) and the scheduler may have deduped them.

| Scraper | Status | Products Found | Flags Created | Flag Rate | Duration |
|---------|--------|---------------|---------------|-----------|----------|
| WholesomeCo | success | 657 | 0 | 0.0% | 65s |
| Curaleaf (Lehi) | success | 399 | 0 | 0.0% | 570s |
| Curaleaf (Provo) | running* | — | — | — | ~570s |
| Curaleaf (Springville) | running* | — | — | — | ~570s |
| Beehive Farmacy (Brigham City) | success | 184 | 0 | 0.0% | 49s |
| Beehive Farmacy (SLC) | running* | — | — | — | ~44s |
| Zion Medicinal | success (prev) | 307 | 0 | 0.0% | 122s |
| Dragonfly Wellness (SLC) | success (prev) | 93 | 0 | 0.0% | 37s |
| Bloc Pharmacy (South Jordan) | success (prev) | 174 | 0 | 0.0% | 38s |
| Bloc Pharmacy (St. George) | success (prev) | 182 | 0 | 0.0% | 38s |
| The Flower Shop (Logan) | success (prev) | 234 | 17 | 7.3% | 56s |
| The Flower Shop (Ogden) | success (prev) | 227 | 1 | 0.4% | 55s |
| The Forest (Murray) | success (prev) | 269 | 1 | 0.4% | 49s |

*Still running at report time. Multiple duplicate "running" entries for same scraper in runs table.

## Session 3 Quality Scores

| Check | Result | Status |
|-------|--------|--------|
| Run Health | Curaleaf success rates poor: Lehi 56%, Provo 62%, Springville 39% (7d) | &#x26A0;&#xFE0F; |
| Overall Flag Rate | 0% for current batch (mature data); Flower Shop Logan 7.3% prior | &#x2705; |
| URL Coverage | 9,379/9,379 — 100% | &#x2705; |
| Price Sanity | 74 prices <$5 (MiniNail accessories $0.01); 34 prices >$500 (Peak Pro $600) | &#x26A0;&#xFE0F; |
| Field Coverage | 65.9% missing THC, 90.0% missing CBD, 0% missing brand | &#x26A0;&#xFE0F; |
| Pending Backlog | 22 pending (all cleanup type, 0 review) | &#x2705; |

**System-wide stats:** 6,640 master products, 9,379 active prices. Flag totals: auto_merged=752, pending=22, dismissed=8, cleaned=2.

**Dispensary freshness:** All dispensaries showing "fresh" status. Oldest data is 14.4h (newer scrapers from earlier today).

## Session 3 Fixes Applied

### Curaleaf Scraper — Fix 1: Switch category navigation to `domcontentloaded`

**Issue**: Category pages used `wait_until="networkidle"` which waits for ALL network activity to cease. On Curaleaf's Next.js site, background analytics and lazy-loaded assets keep the network active long after products render, adding 10-20s per category (7 categories = 70-140s wasted) and causing intermittent timeout failures.

**File**: `backend/services/scrapers/curaleaf_scraper.py` (line 114)

**Change**: `wait_until="networkidle"` &#x2192; `wait_until="domcontentloaded"`. Products load via JS after DOM ready, and the subsequent `_wait_for_products()` already waits for product elements to appear.

### Curaleaf Scraper — Fix 2: Reduce scroll wait times and max attempts

**Issue**: Infinite scroll loop used 4000ms waits and 15 max attempts per category. Worst-case: 7 categories x 15 attempts x (4s scroll + 4s verify) = 840s just from waits. This pushed total runtime to ~570s and caused frequent timeout failures (Springville at 38.5% success rate).

**File**: `backend/services/scrapers/curaleaf_scraper.py` (lines 285, 336, 348)

**Changes**:
- `max_attempts`: 15 &#x2192; 10
- Scroll wait: 4000ms &#x2192; 2000ms
- Double-check wait: 4000ms &#x2192; 2000ms

**Expected impact**: Runtime ~570s &#x2192; ~350-400s. Success rate should improve from 38-62% to 75%+.

## Session 3 Deferred Improvements

1. **MiniNail $0.01 prices**: Hardware accessories legitimately priced near-zero. Not a parsing error.

2. **THC/CBD coverage (65.9% / 90% missing)**: Most platforms don't expose this data consistently. Per-product detail page scraping would fix it but at enormous cost to scrape time.

3. **Hardware category dominance (3,024/6,640 = 45.5%)**: Frontend "hide hardware" filter would be more effective than scraper changes.

4. **Flower Shop Logan 7.3% flag rate**: Down from 48.7% on initial scrape — confidence scorer is learning. Expected to continue improving.

5. **Duplicate "running" entries**: The run trigger doesn't prevent concurrent runs for the same scraper_id. A guard in the API would help but is outside scraper scope.

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
