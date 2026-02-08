# Product Variants - Task Checklist

**Last Updated**: 2026-02-07

## Phase A: Schema Changes
- [x] A1: Add `weight` and `weight_grams` columns to Product model
- [x] A1: Create Alembic migration for Product weight columns + indexes
- [x] A2: Add `original_weight`, `original_price`, `original_category` to ScraperFlag model
- [x] A2: Create Alembic migration for ScraperFlag columns
- [x] A3: Create `services/normalization/weight_parser.py` with parse_weight()
- [x] A3: Add self-referential `variants` / `master_product` relationships to Product

## Phase B: Wire Up Fuzzy Matcher
- [x] B1: Update `scraper_runner.py` import to use ConfidenceScorer
- [x] B1: Update scraper loop to handle flagged_review / auto_merge / new_product actions
- [x] B2: Fix ConfidenceScorer `db.commit()` -> `db.flush()` (3 locations)
- [x] B3: Add candidate caching (pre-load master products once per scraper run)

## Phase C: Parent/Variant Logic
- [x] C1: Implement `find_or_create_variant()` helper in scorer.py
- [x] C1: Update auto_merge path to create/find variant
- [x] C1: Update new_product path to create parent + variant
- [x] C2: Update `flag_processor.py` approve_flag() for variant-aware resolution
- [x] C2: Update `flag_processor.py` reject_flag() for variant-aware resolution

## Phase D: Data Migration
- [x] D1: Create `scripts/migrate_to_variants.py`
- [x] D1: Phase 1 - Create variants from existing masters, move prices
- [x] D1: Phase 2 - Deduplicate products (fuzzy match same brand+name)
- [x] D1: Phase 3 - Parse weights from product names

## Phase E: Backend API Updates
- [x] E1: `routers/products.py` - resolve variant IDs to parent in detail endpoint
- [x] E2: `routers/products.py` - group price comparison by weight
- [x] E3: `routers/search.py` - aggregate prices across variants, add available_weights
- [x] E4: `routers/reviews.py` - resolve variant IDs to parent for create/get
- [x] E5: `services/alerts/stock_detector.py` - query prices through variants
- [x] E5: `services/alerts/price_detector.py` - query prices through variants
- [x] E6: `routers/watchlist.py` - resolve variant IDs to parent
- [x] E7: `routers/dispensaries.py` - include weight in inventory response

## Phase F: Frontend Updates
- [x] F1: `products/[id]/page.tsx` - render grouped price tables per weight
- [x] F2: `products/search/page.tsx` - show weight badges on results
- [x] F3: `admin/cleanup/page.tsx` - show weight/price on flag cards

## Phase G: Seed Data & Tests
- [x] G1: Update `seed_test_data.py` for parent/variant structure
- [x] G2: Create `tests/test_weight_parser.py`
- [x] G2: Create `tests/test_variant_creation.py`
- [x] G2: `tests/test_matcher.py` - existing tests still valid (matcher unchanged)

## Phase H: Documentation
- [x] H1: Update CLAUDE.md (schema, architecture, patterns, file references)
- [x] H2: Update docs/ARCHITECTURE.md (data flow, schema)
- [x] H3: Update docs/API_TEST_PLAN.md (new test cases)
- [x] H4: Update docs/guides/SCRAPING.md (fuzzy matcher active)
- [x] H5: Create docs/workflows/12_product_variants_and_fuzzy_matcher.md
