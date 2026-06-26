# Scraper QA Report — 2026-04-14

## Run Summary

All 15 enabled scrapers triggered and completed successfully. `curaleaf-payson` remains disabled.

| Scraper | Status | Products Found | Flags | Flag% | Duration |
|---------|--------|---------------|-------|-------|----------|
| Beehive Farmacy (Brigham City) | ✅ success | 198 | 4 | 2.0% | 40s |
| Beehive Farmacy (Salt Lake City) | ✅ success | 136 | 5 | 3.7% | 61s |
| Bloc Pharmacy (South Jordan) | ✅ success | 192 | 12 | 6.2% | 41s |
| Bloc Pharmacy (St. George) | ✅ success | 186 | 8 | 4.3% | 40s |
| Curaleaf Utah - Lehi | ✅ success | 504 | 0 | 0.0% | 145s |
| Curaleaf Utah - Park City | ✅ success | 655 | 13 | 2.0% | 112s |
| Curaleaf Utah - Provo | ✅ success | 504 | 0 | 0.0% | 121s |
| Curaleaf Utah - Springville | ✅ success | 520 | 1 | 0.2% | 170s |
| Dragonfly Wellness (Price) | ✅ success | 1,152 | 11 | 1.0% | 42s |
| Dragonfly Wellness (Salt Lake City) | ✅ success | 93 | 0 | 0.0% | 61s |
| The Flower Shop (Logan) | ✅ success | 250 | 3 | 1.2% | 67s |
| The Flower Shop (Ogden) | ✅ success | 238 | 3 | 1.3% | 49s |
| The Forest (Murray) | ✅ success | 253 | 4 | 1.6% | 54s |
| WholesomeCo | ✅ success | 703 | 10 | 1.4% | 99s |
| Zion Medicinal (Cedar City) | ✅ success | 276 | 0 | 0.0% | 136s |
| **TOTAL** | | **5,860** | **74** | **1.3%** | |

> Note: Backend was not running at task start. `slowapi` was missing from venv; installed and server started automatically. `beehive-brigham-city` required a second trigger after the initial batch.

## Quality Scores

| Check | Result | Status |
|-------|--------|--------|
| Run Health | All 15 runs succeeded; no timeouts or silent failures | ✅ |
| Flag Rate | 74 flags / 5,860 products = 1.3% overall | ✅ |
| URL Coverage | 28,040 / 28,040 prices (100%) have `product_url` | ✅ |
| Price Sanity (high) | $700 Volcano Hybrid (hardware, legitimate) · $600 Puffco Peak Pro (hardware, legitimate) | ✅ |
| Price Sanity (low) | $1.00 edible (Dragonfly SLC, Dutchie per-piece variant) — **fixed** | ⚠️ |
| Field Coverage | 27.1% of flags missing THC (hardware + Dutchie edible mg/% mismatch) | ⚠️ |
| Pending Flag Backlog | 24 pending flags (21 Dragonfly SLC stale `data_cleanup`, 2 Zion Medicinal, 1 WholesomeCo) | ✅ |

## Fixes Applied

### Beehive/Bloc/Dragonfly (Dutchie scrapers) — Fix 1: Expanded category label strip

**Issue**: Dutchie product names frequently contain `| Category |` suffixes (e.g., `"Purple Turple | Live Resin Badder |"`, `"Purple Jack | Disposable |"`, `"Afterglow | Live Resin Sugar |"`). The existing strip regex only covered a limited set of category keywords; concentrate subtypes (`Live Resin Sugar`, `Live Resin Badder`, `Live Budder`, `Sugar Wax`) and vape form factors (`Disposable`, `AIO`) were missing, causing names to reach the ConfidenceScorer uncleaned. This produces 60–90% confidence matches against existing clean-named products, generating unnecessary audit flags.

**File**: `backend/services/scrapers/beehive_farmacy_scraper.py`

**Change**: Added `Disposable`, `AIO`, `Live Resin Sugar`, `Live Resin Badder`, `Live Budder`, `Sugar Wax`, `Live Piatella`, `Gel Cube`, `Kief`, and `Rosin` to the trailing `| Category |` strip regex. Applied in **both** `_parse_dutchie_product` (JSON API path, line ~583) and `_parse_dom_item` (DOM fallback path, line ~918) so all scraping paths benefit.

**Verified**: Confirmed correct output for all 13 dirty-name patterns from today's Bloc Pharmacy flags.

---

### Beehive/Bloc/Dragonfly (Dutchie scrapers) — Fix 2: Sub-$2 edible/tincture variant guard

**Issue**: Dutchie's API returns per-piece (1ct) variants alongside full package variants for some edibles. `"Jams Edible 90mgTHC SOUR GREEN APPLE"` at Dragonfly Wellness SLC was stored at **$1.00** with weight `0.09g` (a single-gummy dosage weight), while the actual package price should be ~$10–30. This data error produces stale `data_cleanup` flags and pollutes price comparison data.

**File**: `backend/services/scrapers/beehive_farmacy_scraper.py`

**Change**: In `_parse_dutchie_product` Schema 1 (variants loop, line ~748), added a guard that skips any variant priced below $2.00 when the product category is `edible` or `tincture`. Hardware accessories can legitimately cost <$2 (replacement coils, etc.) so only cannabis consumable categories are filtered. Debug-level log emitted when a variant is skipped.

---

## Deferred Improvements (not auto-applied)

### 1. Complex Dutchie name patterns with embedded weight

`"Live Piatella - Viper City #13 | Cartridge | .5g"` and `"Peach Mango | Gel Cube | 40mg | 20pk"` contain weight data after the category label (`.5g`, `40mg | 20pk`). The current strip regex requires the category to appear at the very end of the string (after stripping trailing `|`), so these don't match. A more complete fix would parse weight from the Dutchie-formatted suffix and strip the entire `| Category | Weight` block. Deferred because the weight is still being extracted correctly from the variant `option` field via the API path.

### 2. Stale pending flag backlog (Dragonfly SLC)

21 Dragonfly SLC flags have been pending since March 2026, all with `flag_type=data_cleanup` and `brand=Unknown`. These are cross-dispensary brand-name matches involving products at other stores. Recommend bulk-dismissing these via the admin UI — none are actionable without manual brand resolution.

### 3. WholesomeCo "your first app order" promotional flag

A `$30 / no weight / no THC` item scraped as a product with URL `https://www.wholesome.co/app` is in the pending queue. The WholesomeCo Playwright scraper already has a URL guard (`if "/shop/" not in item_url: skip`) at line ~680, but this flag predates that guard. Dismiss it manually; no code change needed since the guard is already in place.

### 4. Dutchie THC % on edibles (systematic issue)

THC values on edibles from Dutchie-platform scrapers (Dragonfly, Beehive, Bloc, Zion) show implausibly low percentages (e.g., 0.09%, 0.21%, 0.69%). These are per-unit mg doses stored as percentages after the `>100` guard discards true mg totals. The scraper already converts out-of-range `PERCENTAGE` values to `mg` content strings (line ~668) but some slips through as very low `%`. Root cause: Dutchie sometimes returns per-piece mg values (e.g., 9 mg/piece) with `unit=PERCENTAGE`. A targeted fix would detect edible products where `thc_pct < 1.0` and `unit=PERCENTAGE` and treat the value as mg rather than %. Deferred pending manual verification of the raw Dutchie API payload.

### 5. Curaleaf Lehi/Provo/Springville historical failure rate

7-day success rates: Lehi 53.8%, Provo 71.4%, Springville 69.2%. The `avg_duration_seconds` for Lehi is ~23,357s — inflated by old zombie/hanging run records. Current runs are healthy (145s, 121s, 170s). No code change needed; the outlier averages are a data artefact from previous hanging runs that were not marked as error before the zombie-run fix.
