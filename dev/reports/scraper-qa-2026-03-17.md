# Scraper QA Report — 2026-03-17

## Run Summary

All 13 registered scrapers were triggered sequentially. `curaleaf-springville` was still
completing at report time (typical duration ~564 s). `dragonfly-price` appears in the run
history as a `warning` (0 products) — this scraper is intentionally commented out pending
URL investigation; the history entry is a stale record.

| Scraper | Status | Products Found | Processed | Flags | Duration |
|---------|--------|---------------|-----------|-------|----------|
| wholesomeco | ✅ success | 325 | 325 | 21 | 81 s |
| curaleaf-lehi | ✅ success | 392 | 392 | 10 | 564 s |
| curaleaf-provo | ✅ success | 406 | 406 | 1 | 564 s |
| curaleaf-springville | ⏳ running | — | — | — | ~564 s |
| beehive-brigham-city | ✅ success | 196 | 196 | 10 | 38 s |
| beehive-slc | ✅ success | 132 | 132 | 0 | 48 s |
| zion-medicinal | ✅ success | 311 | 311 | 173 | 129 s |
| dragonfly-slc | ✅ success | 93 | 93 | 64 | 50 s |
| dragonfly-price | ⚠️ warning | 0 | 0 | 0 | 36 s (stale/disabled) |
| bloc-south-jordan | ✅ success | 175 | 175 | 90 | 46 s |
| bloc-st-george | ✅ success | 183 | 183 | 58 | 38 s |
| flower-shop-logan | ✅ success | 234 | 234 | 114 | 37 s |
| flower-shop-ogden | ✅ success | 227 | 227 | 132 | 56 s |
| the-forest-murray | ✅ success | 269 | 269 | 135 | 56 s |

**Note:** `bloc`, `flower-shop`, and `the-forest` scrapers are newly added (untracked in git).
High flag rates on first run are expected — no matching master products exist yet.

## Quality Scores

| Check | Result | Status |
|-------|--------|--------|
| Run Health | 12/13 success; 1 running (curaleaf-springville), 1 stale warning (dragonfly-price, disabled) | ⚠️ |
| Flag Rate (all scrapers) | 808 flags / 2943 products = 27.5% | ⚠️ |
| Flag Rate (excluding 3 new scrapers) | 280 flags / 1749 products = 16.0% | ✅ |
| URL Coverage | 5,804 / 5,804 prices have product_url = 100% | ✅ |
| Price Sanity | 28 prices < $5 (all hardware accessories); 22 prices > $500 (Volcano Hybrid vaporizers ~$700) | ✅ |
| Field Coverage — THC | 56.5% of master products missing THC% | ⚠️ |
| Field Coverage — CBD | 90.7% of master products missing CBD% | ⚠️ |
| Pending Flag Backlog | 22 pending flags (well below 50 threshold) | ✅ |

### Flag Rate by Scraper

| Scraper | Flag Rate | Note |
|---------|-----------|------|
| dragonfly-slc | 68.8% (64/93) | ❌ Established scraper — DOM fallback suspected |
| flower-shop-ogden | 58.1% (132/227) | ❌ New scraper — expected on first run |
| zion-medicinal | 55.6% (173/311) | ❌ High for Dutchie-based scraper |
| bloc-south-jordan | 51.4% (90/175) | ❌ New scraper — expected on first run |
| the-forest-murray | 50.2% (135/269) | ❌ New scraper — expected on first run |
| flower-shop-logan | 48.7% (114/234) | ⚠️ New scraper — expected on first run |
| bloc-st-george | 31.7% (58/183) | ⚠️ New scraper — expected on first run |
| wholesomeco | 6.5% (21/325) | ✅ |
| beehive-brigham-city | 5.1% (10/196) | ✅ |
| curaleaf-lehi | 2.6% (10/392) | ✅ |
| beehive-slc | 0% (0/132) | ✅ |
| curaleaf-provo | 0.2% (1/406) | ✅ |

## Fixes Applied

### The Flower Shop (Logan & Ogden) — Fix 1: Capture All Weight/Price Options

**Issue**: `_parse_product` in `FlowerShopBaseScraper` only captured the **first** element of
`available_weights`, silently discarding all other weight options and their prices. For
flower products, this typically meant only the 1g price was recorded while 3.5g, 7g, 14g,
and 28g options — the sizes most patients buy — were never stored. This directly reduces
price comparison value and could contribute to flag rates on subsequent runs when a product
re-appears with a different weight.

**File**: `backend/services/scrapers/flower_shop_scraper.py`

**Change**: Changed `_parse_product` to return `List[ScrapedProduct]` (was `Optional[ScrapedProduct]`)
and loop over all `available_weights`, creating one `ScrapedProduct` per weight/price pair.
Added a fallback to `bucket_price` with no weight when `available_weights` is empty.
Updated the caller in `scrape_products` to use `kind_products.extend(parsed)` instead of
`kind_products.append(parsed)`. This fix also applies to `TheForestMurrayScraper` which
inherits from `FlowerShopBaseScraper`.

**Impact**: Future runs should roughly double (or more) the number of price records captured
per product, improving price comparison coverage for patients.

---

### Dragonfly Wellness (SLC) via Beehive Base — Fix 2: Name Cleaning in DOM Fallback

**Issue**: `BeehiveFarmacyBaseScraper._parse_dom_item` (the DOM extraction fallback path) did
not apply Dutchie-specific name cleanups. When `dutchie.com/stores/dragonfly-wellness`
fails to populate `window.__dutchieCaptures` (likely because the fetch interception script
doesn't intercept responses from the Dutchie stores CDN), the scraper falls back to DOM
extraction. DOM-extracted names retained:
- The `m` medical-tier indicator (e.g., `"Select Elite Vape m TAHOE OG"` instead of `"Select Elite Vape TAHOE OG"`)
- Trailing category labels after `|` (e.g., `"White Runtz | Flower"`)

These uncleaned names cause significantly lower confidence scores during matching (flags in
the 0.35–0.65 range were observed), generating `auto_missed` events and new master products
instead of merging with existing records. This is the primary driver of Dragonfly SLC's
68.8% flag rate.

**File**: `backend/services/scrapers/beehive_farmacy_scraper.py`

**Change**: Added the same three `re.sub()` name-cleaning steps that `_parse_dutchie_product`
applies (API path) to `_parse_dom_item` (DOM fallback path):
1. Strip ` m ` medical-tier indicator: `r'\s+\bm\b\s+'`
2. Strip trailing empty pipe: `r'\s*\|\s*$'`
3. Strip trailing Dutchie category label after `|` (Topical, Tincture, Flower, etc.)

This fix benefits Dragonfly SLC and Zion Medicinal scrapers whenever DOM fallback is used.

---

## Deferred Improvements (not auto-applied)

### 1. Dragonfly SLC — Confirm DOM vs. API Extraction Path
The 68.8% flag rate strongly suggests DOM extraction is being used instead of API
interception for `dutchie.com/stores/`. A future investigation should add explicit
logging to confirm which extraction path is active, and if DOM is consistently used,
consider adding category-URL iteration (like Zion Medicinal) to improve product coverage.

### 2. Zion Medicinal — Edible Weight Formatting (0.09g → 90mg)
Dutchie reports some edible unit quantities in grams (e.g., `0.09g` for a 90mg dose).
Schema 2 (Options/Prices parallel arrays) passes the raw option string directly, so these
appear in the DB as `0.09g` rather than `90mg`. The Schema 1 (variants) path already
handles sub-gram conversion (`if 0 < qty_float < 1: weight = f"{qty_float * 1000:.4g}mg"`),
but Schema 2 doesn't. Fixing this would require verifying the live Dutchie API response
structure for Zion to confirm which schema path is active. Skipped as it requires manual
site inspection.

### 3. Curaleaf — Dart Battery Duplicate Records
`Dart Battery` appears in the DB 9–15 times per run (once per Curaleaf location × multiple
runs). The product's price ($1.00–$4.00) appears genuine per the aria-label, but the
duplicate master-product entries could be reduced by improving the confidence scorer's
hardware-matching threshold or deduplicate by (name, dispensary) more aggressively.
Skipped because it requires coordinated scorer and matcher changes.

### 4. THC/CBD Coverage (56%/91% missing)
THC/CBD fields are not available for all product types in the Dutchie API response (e.g.,
hardware accessories, many edibles). This is a data availability issue upstream at
dispensaries, not a scraper bug. The field coverage metrics are expected to improve
gradually as more flower/concentrate products dominate the catalogue.
