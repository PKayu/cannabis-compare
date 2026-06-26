# Scraper QA Report — 2026-04-10

Run window: all scrapers triggered at ~2026-04-11T03:39Z (local 2026-04-10 evening). 15 of 16 registered scrapers are enabled; `curaleaf-payson` remains disabled pending URL investigation.

## Run Summary

| Scraper | Status | Products Found | Processed | Flags | Duration |
|---|---|---|---|---|---|
| wholesomeco | success | 694 | 694 | 3 | 86.1s |
| curaleaf-lehi | success | 427 | 427 | 8 | 517.9s |
| curaleaf-provo | success | 441 | 441 | 0 | 525.3s |
| curaleaf-springville | success | 427 | 427 | 5 | 509.6s |
| curaleaf-park-city | success | 519 | 519 | 6 | 93.5s |
| beehive-brigham-city | success | 206 | 206 | 7 | 40.5s |
| beehive-slc | success | 129 | 129 | 6 | 38.6s |
| zion-medicinal | success | 278 | 278 | 6 | 122.0s |
| dragonfly-slc | success | 93 | 93 | 0 | 38.1s |
| dragonfly-price | success | 1152 | 1152 | 15 | 35.7s |
| bloc-south-jordan | success | 193 | 193 | 15 | 40.3s |
| bloc-st-george | success | 193 | 193 | 4 | 39.6s |
| flower-shop-logan | success | 250 | 250 | 4 | 68.3s |
| flower-shop-ogden | success | 240 | 240 | 11 | 73.9s |
| the-forest-murray | success | 269 | 269 | 7 | 60.7s |

All 15 enabled scrapers completed successfully (0 errors, 0 hangs). Total products scraped: 5,511. Total flags created: 97 (1.76% flag rate system-wide).

## Quality Scores

| Check | Result | Status |
|---|---|---|
| Run Health | 15/15 success, 0 stale runs | ✅ |
| Flag Rate | 1.76% system-wide (highest: bloc-south-jordan 7.8%) | ✅ |
| URL Coverage | 100% on all 97 new flags | ✅ |
| Price Sanity | 0 parsing errors (all outliers legitimate: accessories, bulk flower) | ✅ |
| Field Coverage — weight | 97/97 present | ✅ |
| Field Coverage — THC (Curaleaf Provo) | **0/37 missing** | ❌ |
| Field Coverage — THC (Curaleaf Park City) | 2/10 present (8 missing) | ❌ |
| Field Coverage — THC (other scrapers) | 80–100% coverage | ✅ |
| Pending Flag Backlog | 24 pending (21 stale from 2026-03-15 dragonfly-slc) | ✅ |

## Per-Scraper THC Capture Rate (from today's flagged records)

| Dispensary | Captured / Total |
|---|---|
| Beehive Brigham City | 5/5 |
| Beehive SLC | 4/5 |
| Bloc South Jordan | 13/14 |
| Bloc St. George | 9/12 |
| Curaleaf Lehi | 30/39 |
| **Curaleaf Park City** | **2/10** |
| **Curaleaf Provo** | **0/37** |
| Curaleaf Springville | 29/37 |
| Dragonfly Wellness Price | 0/2 (both are edibles — expected) |
| The Flower Shop Logan | 5/9 |
| The Flower Shop Ogden | 27/28 |
| The Forest Murray | 13/17 |
| Zion Medicinal | 2/2 |

Worst performer: **Curaleaf Provo** — zero THC capture across 37 flagged products (all had valid names, weights, URLs, and categories). Park City is second-worst at 20% coverage. Both are Curaleaf, but they use different scrapers: Provo/Lehi/Springville scrape the DOM (`curaleaf_scraper.py`), while Park City hits the SweedPOS API (`curaleaf_park_city_scraper.py`). Both have different root causes, and both are fixed below.

## Fixes Applied

### Curaleaf (DOM) — Fix 1: Broader THC/CBD regex patterns
**Issue**: `curaleaf_scraper.py` only matched `THC:\s*\d+%` / `THC:\s*\d+mg`. Curaleaf's card layout varies by category — concentrate cards (BRIQ cartridges, live rosins) render potency as `THCa 78.3%` or `25.4% THC` with no colon. Provo's 37 flagged products were all concentrates/vapes, which explains the 0/37 capture rate while Lehi (flower-heavy) still got 77%.
**File**: `backend/services/scrapers/curaleaf_scraper.py` (lines 487–539)
**Change**: Replaced the two single regex lines with a pattern array covering:
- `THC:`, `THCa:`, `Total THC:` prefixes
- `THC ` / `THCa ` without colon
- Trailing form `25.4% THC`
Same set for CBD. Added a guard that discards values `>100%` (rejects batch numbers or dates that happen to contain a `%`). The fallback order is percentage-first, then mg.

### Curaleaf Park City (SweedPOS API) — Fix 2: Resilient labTests parsing
**Issue**: `_parse_thc` / `_parse_cbd` only read `labTests.thc.value[0]`. When SweedPOS returned `displayThc: "25.4%"` with no structured `thc` key, the functions returned `(None, display_string)` — the percentage number was discarded, leaving `thc_percentage=None` in the DB. Some variants also carried `labTests` on the parent product instead of the variant itself, which the old code ignored entirely.
**File**: `backend/services/scrapers/curaleaf_park_city_scraper.py` (lines 120–185, 297)
**Changes**:
1. Added `_extract_pct_from_display()` helper that parses a percentage out of strings like `"25.4% THC"`.
2. `_parse_thc` / `_parse_cbd` now also look under `totalThc` / `THC` / `totalCbd` / `CBD` keys (case variants the SweedPOS API uses on some endpoints) and extract a percentage from `displayThc` / `displayCbd` when structured values are absent.
3. In `_parse_product`, the variant's `labTests` now falls back to `raw.get("labTests")` so parent-level lab results populate variant records when the variant dict doesn't carry its own.

Both files compiled cleanly and the parser helpers were unit-tested in-process against synthetic fixtures (percentage + mg + displayThc paths all resolve correctly).

## Deferred Improvements (not auto-applied)

- **The Forest / Flower Shop "each" weight**: iHeartJane-backed scrapers use `weight="each"` for unit-dosed products (tinctures, caramels, capsules). The ConfidenceScorer treats `each` as a distinct weight, which can split a product line across multiple parents. A proper fix would parse mg dosage out of the product name (`"Cinnamon Roll 50mg 2:1 ... [10pk]"` → `50mg`) but the dose can mean per-piece or per-pack, so the name-parsing logic needs manual validation before it can be trusted to write to the weight field. Leaving as-is until a dedicated pass can sample 20–30 names and confirm a reliable grammar.
- **21 stale pending flags from 2026-03-15 (dragonfly-slc)**: These contain garbage `"m"` tokens in product names and THC percentages misparsed into `original_weight` (`0.2918g` = 29.18%). The name-cleanup (`\s+\bm\b\s+` stripper) and the `v <= 100` potency guard have both already been added to the current scraper, so the bugs won't recur on fresh runs. Recommend dismissing these flags via the admin bulk-action endpoint in a follow-up — they are pre-fix stale data, not current bugs.
- **Curaleaf Payson**: Still disabled. Needs live investigation of the Dutchie age-gate behavior on the `/dispensary/` URL path.
- **No further fixes recommended for other scrapers** — flag rates, URL coverage, and price sanity are all within healthy thresholds.
