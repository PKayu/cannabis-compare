# Scraper QA Report — 2026-06-25

**Run by:** Manual test session  
**Baseline:** 2026-04-14 (15 scrapers, all success, 5860 products)

---

## Summary

| Status | Count | Scrapers |
|--------|-------|---------|
| ✅ Success | 14 | All except Forest Murray |
| ⚠️ Platform change | 1 | the-forest-murray |
| 🚫 Disabled (no menu) | 1 | curaleaf-payson |

**Total products from active scrapers:** ~5,955 (up from 5,860 baseline)

---

## Results by Scraper

| Scraper | Status | Products | Duration |
|---------|--------|----------|----------|
| beehive-brigham-city | ✅ success | 187 | 41s |
| beehive-slc | ✅ success | 141 | 40s |
| bloc-south-jordan | ✅ success | 189 | 45s |
| bloc-st-george | ✅ success | 172 | 50s |
| curaleaf-lehi | ✅ success | 560 | 104s |
| curaleaf-park-city | ✅ success | 698 | 141s |
| curaleaf-payson | 🚫 disabled | 0 | — |
| curaleaf-provo | ✅ success | 640 | 114s |
| curaleaf-springville | ✅ success | 640 | 143s |
| dragonfly-price | ✅ success | 1366 | 46s |
| dragonfly-slc | ✅ success | 93 | 39s |
| flower-shop-logan | ✅ success | 250 | 74s |
| flower-shop-ogden | ✅ success | 229 | 60s |
| the-forest-murray | ⚠️ needs rewrite | 0 | — |
| wholesomeco | ✅ success | 624 | 88s |
| zion-medicinal | ✅ success | 166 | 123s |

---

## Issues Found and Fixed

### Curaleaf Lehi / Provo / Springville — Age Gate Broken

**Root cause:** Curaleaf's age gate uses two Radix UI checkboxes (`button[role="checkbox"]`) that must both be `aria-checked=true` before the "I'm over 21" confirm button becomes enabled. The old code had two separate loops over the same elements, double-clicking each checkbox and toggling it back to unchecked. Additionally, the code didn't wait for React's async state propagation between clicks.

**Fix applied to `backend/services/scrapers/curaleaf_scraper.py`:**
- Use `page.locator('button[role="checkbox"]')` (no duplicates)
- Click each checkbox exactly once
- Wait 800ms for React state change
- Use `wait_for_function` to confirm button is enabled before clicking
- Only click confirm button when `is_disabled()` returns False

**Verified:** Lehi 560 ✓, Provo 640 ✓, Springville 640 ✓

---

## Issues Requiring Future Work

### The Forest Murray — Platform Changed to Dutchie

The Forest Murray switched from iHeartJane to Dutchie since the April baseline.

- **Old URL:** `theforestutah.com/shop/menu/{category}` (intercepted `dmerch.iheartjane.com/v2/multi`)
- **New URL:** `theforestutah.com/stores/the-forest-murray/products/{category}`
- **New API:** `theforestutah.com/api-1/graphql` (Dutchie GraphQL, same as Beehive Farmacy)
- **Dispensary ID:** `69cd22a84028784c6f7ecf8a`
- **Fix needed:** Rewrite `the_forest_scraper.py` using `beehive_farmacy_scraper.py` as reference

---

## Backend Issues Fixed This Session

- **Route ordering bug:** `/scrapers/run/all` was shadowed by `/scrapers/run/{scraper_id}` — fixed by reordering routes in `backend/routers/scrapers.py`
- **SECRET_KEY:** Was placeholder string — replaced with real 64-char hex in `backend/.env`
- **Stuck runs:** Server killed mid-scrape left `status=running` records — marked failed and cleaned up

---

## Production Readiness

See `dev/active/production-launch/checklist.md`. Phase 1 and 2 complete. Phase 3 (Railway) and Phase 4 (Vercel) require manual account setup.
