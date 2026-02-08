# Product Variants - Context & Key Files

**Last Updated**: 2026-02-07
**Status**: IMPLEMENTATION COMPLETE - All phases A through H done

## Key Decisions

1. **No new table** — reuse existing Product model with `is_master` / `master_product_id` hierarchy
2. **Parent + Variants** — parents hold reviews, variants hold prices with weight info
3. **Group by quantity** for price comparison (not price-per-gram normalization)
4. **Include data migration** for existing products
5. **Fuzzy matcher wired up** — ConfidenceScorer now active in scraper pipeline

## Implementation Summary

### Phase A: Schema Changes (DONE)
- Added `weight` (String) and `weight_grams` (Float, indexed) to Product model
- Added `original_weight`, `original_price`, `original_category` to ScraperFlag model
- Updated self-referential relationships to explicit `variants`/`master_product` with `back_populates`
- Created weight_parser.py utility and Alembic migration

### Phase B: Fuzzy Matcher Wiring (DONE)
- `scraper_runner.py` now imports ConfidenceScorer instead of ProductMatcher
- Processing loop handles flagged_review / auto_merge / new_product actions
- Candidate caching (pre-load master products once per run)
- ConfidenceScorer uses `db.flush()` for transaction control

### Phase C: Parent/Variant Logic (DONE)
- `find_or_create_variant()` helper in scorer.py
- Auto-merge creates/finds variant under matched parent
- New product creates parent + variant
- Flag processor approve/reject updated for variant-aware resolution

### Phase D: Data Migration (DONE)
- `scripts/migrate_to_variants.py` with 3 phases: create variants, deduplicate, parse weights

### Phase E: Backend API Updates (DONE)
- products.py: variant resolution, grouped price comparison by weight
- search.py: prices aggregated across variants, `available_weights` in response
- reviews.py: variant-to-parent resolution for create and get
- watchlist.py: variant-to-parent resolution
- dispensaries.py: weight info in inventory response
- stock_detector.py / price_detector.py: query prices through variants

### Phase F: Frontend Updates (DONE)
- Product detail page: grouped price tables per weight with weight headers
- Search results: weight badges on ResultsTable (mobile + desktop)
- Admin cleanup: weight, price, category shown on flag cards

### Phase G: Seed Data & Tests (DONE)
- seed_test_data.py: parent/variant structure (5 parents, 8 variants)
- Prices point to variants, reviews point to parents
- test_weight_parser.py: 20+ unit tests
- test_variant_creation.py: variant creation and price relationship tests

### Phase H: Documentation (DONE)
- CLAUDE.md, ARCHITECTURE.md, API_TEST_PLAN.md, SCRAPING.md updated
- New workflow #12 created

## Critical Files (Post-Implementation)

### Models & Schema
- `backend/models.py` — Product (weight/weight_grams, variants/master_product relationships), ScraperFlag (original_weight/price/category)
- `backend/alembic/versions/20260207_000001_add_product_variants_and_weight.py` — Migration

### Scraper Pipeline
- `backend/services/scraper_runner.py` — Uses ConfidenceScorer with candidate caching
- `backend/services/normalization/scorer.py` — ConfidenceScorer with find_or_create_variant()
- `backend/services/normalization/matcher.py` — ProductMatcher (fuzzy matching engine, unchanged)
- `backend/services/normalization/flag_processor.py` — Variant-aware approve/reject
- `backend/services/normalization/weight_parser.py` — Weight string parsing

### Backend API
- `backend/routers/products.py` — Variant-aware endpoints
- `backend/routers/search.py` — Aggregated variant prices
- `backend/routers/reviews.py` — Variant-to-parent resolution
- `backend/routers/watchlist.py` — Variant-to-parent resolution
- `backend/routers/dispensaries.py` — Weight in inventory
- `backend/services/alerts/stock_detector.py` — Variant-aware queries
- `backend/services/alerts/price_detector.py` — Variant-aware queries

### Frontend
- `frontend/app/products/[id]/page.tsx` — Grouped price tables
- `frontend/components/ResultsTable.tsx` — Weight badges
- `frontend/app/(admin)/admin/cleanup/page.tsx` — Flag card details

### Data & Tests
- `backend/seed_test_data.py` — Parent/variant test data
- `backend/scripts/migrate_to_variants.py` — One-time migration
- `backend/tests/test_weight_parser.py` — Weight parser tests
- `backend/tests/test_variant_creation.py` — Variant logic tests

## Data Model Reference

```
Product (is_master=True, weight=None) — "Blue Dream"
  ├── Product (is_master=False, weight="3.5g") — variant
  │     └── Price (dispensary_id, amount) — per-dispensary pricing
  ├── Product (is_master=False, weight="7g") — variant
  │     └── Price (dispensary_id, amount)
  ├── Review (user_id, rating, ...) — on parent
  └── Watchlist (user_id) — on parent
```

## Fuzzy Matcher Thresholds
- >90% confidence -> auto_merge (link to existing parent, create variant)
- 60-90% confidence -> flagged_review (create ScraperFlag for admin)
- <60% confidence -> new_product (create new parent + variant)

## Post-Implementation Verification Steps

```bash
# Apply migration
cd backend && alembic upgrade head

# Run migration script (for existing data)
python scripts/migrate_to_variants.py

# Run tests
pytest tests/test_weight_parser.py tests/test_variant_creation.py tests/test_matcher.py -v

# Reseed test data (if needed)
python seed_test_data.py --clear && python seed_test_data.py

# Verify API responses
curl http://localhost:8000/api/products/prod-001 | python -m json.tool
curl http://localhost:8000/api/products/prod-001/prices | python -m json.tool
curl 'http://localhost:8000/api/products/search?q=blue+dream' | python -m json.tool
```
