# Scraper QA Report — 2026-03-16

> **Note**: Backend was not running at report time. All metrics sourced directly from Supabase DB via SQLAlchemy. Scrapers were not re-run; analysis is based on the most recent completed run per scraper.

---

## Run Summary

| Scraper | Status | Products Found | Processed | Flags | Flag Rate | Duration |
|---------|--------|---------------|-----------|-------|-----------|----------|
| bloc-st-george | success | 183 | 183 | 58 | 31.7% | 37s |
| bloc-south-jordan | success | 175 | 175 | 90 | 51.4% | 46s |
| beehive-brigham-city | success | 196 | 196 | 10 | 5.1% | 38s |
| zion-medicinal | success | 311 | 311 | 173 | 55.6% | 128s |
| dragonfly-price | warning | 0 | 0 | 0 | — | 35s |
| dragonfly-slc | success | 93 | 93 | 64 | 68.8% | 49s |
| curaleaf-springville | stuck/running | 0 | 0 | 0 | — | — |
| curaleaf-provo | success | 406 | 406 | 14 | 3.4% | 568s |
| wholesomeco | success | 671 | 671 | 3 | 0.4% | 69s |
| beehive-slc | success | 132 | 132 | 0 | 0% | 48s |
| curaleaf-lehi | success | 399 | 399 | 1 | 0.3% | 564s |

---

## Quality Scores

| Check | Result | Status |
|-------|--------|--------|
| Run Health | 2 issues: `dragonfly-price` returning 0 products (warning); `curaleaf-springville` stuck in "running" state since 2026-03-14 | ⚠️ |
| Flag Rate | dragonfly-slc 68.8%, zion-medicinal 55.6%, bloc-south-jordan 51.4%, bloc-st-george 31.7% | ❌ |
| URL Coverage | 5073/5073 (100%) | ✅ |
| Price Sanity | 28 prices <$5, 22 prices >$500 — all legitimate (cheap accessories like batteries/dab tools; premium vaporizers like Volcano Hybrid $700, Puffco Peak Pro $600) | ✅ |
| Field Coverage | 21 pending flags: 0 missing weight, 0 missing URL | ✅ |
| Pending Flag Backlog | 21 pending flags (all `data_cleanup` type) | ✅ |

---

## Root Cause Analysis — High Flag Rates

All four high-flag-rate scrapers extend `BeehiveFarmacyBaseScraper` and share the same Dutchie product name parsing. Two naming artifacts were identified in `_parse_dutchie_product`:

**Artifact 1 — Trailing pipe in Bloc Pharmacy names**
Bloc Pharmacy's Dutchie API returns names formatted as `"{Strain} | {Concentrate Type} |"` with a trailing empty pipe section:
- `"Triangle Kush Cake | Crumble |"` → should be `"Triangle Kush Cake | Crumble"`
- `"J1 | Live Resin Sugar |"` → should be `"J1 | Live Resin Sugar"`

**Artifact 2 — Category label suffix in Zion Medicinal names**
Zion's Dutchie embedded-menu appends the product form as a trailing `| Category` label — already captured in the `category` field:
- `"White Runtz | Tincture"` → should be `"White Runtz"`
- `"Menthol Calm | Balm"` → should be `"Menthol Calm"`
- `"Salve 1:1 Stick ( THC:CBD) | Topical"` → should be `"Salve 1:1 Stick ( THC:CBD)"`

---

## Fixes Applied

### BeehiveFarmacyBaseScraper — Fix 1: Strip trailing pipe artifact (Bloc Pharmacy)

**Issue**: Bloc Pharmacy product names end with ` |` (empty pipe section), e.g. `"Triangle Kush Cake | Crumble |"`. This reduces fuzzy match confidence against identical products at other dispensaries.

**File**: `backend/services/scrapers/beehive_farmacy_scraper.py`

**Change**: Added `re.sub(r'\s*\|\s*$', '', name)` after the existing ` m ` indicator strip in `_parse_dutchie_product`. Removes any trailing pipe with surrounding whitespace before names reach the ConfidenceScorer.

**Expected impact**: Improved match confidence for Bloc products that appear at other dispensaries, reducing `match_review` flag rate.

---

### BeehiveFarmacyBaseScraper — Fix 2: Strip Dutchie embedded-menu category suffixes (Zion Medicinal)

**Issue**: Zion Medicinal product names contain a pipe-delimited category label at the end (e.g. `"White Runtz | Tincture"`, `"Menthol Calm | Balm"`). This suffix is redundant (already in `category` field) and lowers cross-dispensary fuzzy match confidence.

**File**: `backend/services/scrapers/beehive_farmacy_scraper.py`

**Change**: Added a `re.sub` that strips known Dutchie category labels (`Topical`, `Tincture`, `Balm`, `Patches`, `Cream`, `Lotion`, `Flower`, `Concentrate`, `Pre-Roll`, `Vape`, `Vaporizer`, `Cartridge`, `Edible`, `Accessory`, `Accessories`, `Gear`) when they appear as the final pipe-delimited segment.

**Expected impact**: Cleaner product names for Zion Medicinal, improving cross-dispensary match confidence for tinctures, topicals, and other form-labeled products.

---

### BeehiveFarmacyBaseScraper — Fix 3: Sub-gram weight conversion for edibles/tinctures

**Issue**: Dutchie sometimes returns edible and tincture dosage quantities as sub-gram floats (e.g. `unitQuantity=0.5, unit="GRAMS"` for a 500mg gummy). The previous code concatenated these directly as `"0.5g"` — a non-standard weight string that the `WeightParser` doesn't recognise as an equivalent of `"500mg"`, causing match failures against products listed at other dispensaries with explicit `mg` weights.

**File**: `backend/services/scrapers/beehive_farmacy_scraper.py`

**Change**: In both the `FlavorVariant` (Schema 1) and the `FlavorProfile` (Schema 2-fallback) parsing branches inside `_parse_dutchie_product`, added a branch: when `"gram" in unit` and `0 < qty_float < 1`, convert to milligrams (`qty_float * 1000` formatted with `:.4g` to avoid trailing zeros) before building the weight string. Values ≥ 1 gram continue to produce `"{qty}g"` as before.

**Expected impact**: Edibles and tinctures with sub-gram dosages (common for 500mg and 100mg products) now produce canonical `mg` weight strings, improving cross-dispensary matching and reducing flags for these product types at Beehive, Bloc Pharmacy, and any future Dutchie-based scrapers.

---

## New Scrapers Added This Session

Two new scraper files were added and registered in `backend/main.py`:

| Scraper ID | File | Platform | Locations |
|------------|------|----------|-----------|
| `bloc-south-jordan` | `bloc_pharmacy_scraper.py` | Dutchie (BeehiveFarmacyBaseScraper) | South Jordan, UT |
| `bloc-st-george` | `bloc_pharmacy_scraper.py` | Dutchie (BeehiveFarmacyBaseScraper) | St. George, UT |
| `flower-shop-logan` | `flower_shop_scraper.py` | iHeartJane/dmerch | North Logan, UT |
| `flower-shop-ogden` | `flower_shop_scraper.py` | iHeartJane/dmerch | South Ogden, UT |

Both files inherit existing base scrapers (`BeehiveFarmacyBaseScraper` for Bloc Pharmacy; a new `FlowerShopBaseScraper` for The Flower Shop). The Flower Shop scraper uses Playwright to intercept `dmerch.iheartjane.com/v2/multi` POST responses and parses product data from `search_attributes`.

---

## Deferred Improvements (not auto-applied)

- **`curaleaf-springville` stuck run**: Run record has been in `running` state since 2026-03-14. Requires manual cleanup — update the run status to `error` in the DB, or restart the backend (which clears stale runs on startup).

- **`dragonfly-price` silent failure**: The Price, UT location is intentionally disabled (commented out) in `dragonfly_wellness_scraper.py` due to a Dutchie age-gate issue that produces a blank page. The `warning/0 products` run record is a leftover from before it was disabled. No code fix needed.

- **New scraper flag backlog (bloc, zion, dragonfly)**: A portion of the high flag rates reflects expected first-run behavior — cross-dispensary product matching improves as admins resolve `match_review` flags and build up the canonical product catalog. The three code fixes above address the preventable naming-artifact and weight-parsing portions of mismatches.

- **FlowerShopBaseScraper — single weight per product**: `_parse_product` takes only `available_weights[0]` and creates one `ScrapedProduct` per raw item. Products sold in multiple weights (e.g., flower sold at 1g and 3.5g) will only appear at the first listed weight. A future improvement would iterate all `available_weights` and emit one `ScrapedProduct` per weight/price pair, matching the pattern used by the Dutchie and Wholesome Co scrapers. Skipped because it requires verifying multi-weight price field alignment against live API responses.
