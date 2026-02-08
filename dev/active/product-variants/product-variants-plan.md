# Product Variants, Fuzzy Matcher Wiring & Data Migration

**Created**: 2026-02-07
**Last Updated**: 2026-02-07
**Status**: In Progress

## Problem

Two related usability issues:

1. **Products separated by quantity**: Same product in different sizes (e.g., Gorilla Glue #4 in 3.5g vs 1oz) are stored as separate products. Reviews are split, price comparison across dispensaries is harder.

2. **Admin duplicate detection dashboard is empty**: The admin cleanup queue at `/admin/cleanup` shows zero flags. Root cause: the fuzzy matching system (`services/normalization/matcher.py` + `scorer.py`) is fully implemented but never wired up. `scraper_runner.py` imports the wrong matcher (`services/product_matcher.py`) which only does exact matching and never creates ScraperFlags.

## Solution

### Data Model: Parent + Variants (using existing fields)

The Product model already has `is_master` and `master_product_id` fields that are unused. We repurpose them:

- **Parent product**: `is_master=True`, `weight=None` — represents the product (e.g., "Gorilla Glue #4 by Tryke")
- **Variant product**: `is_master=False`, `master_product_id` -> parent, `weight="3.5g"`, `weight_grams=3.5`
- **Reviews** attach to parent products
- **Prices** attach to variant products
- **Search** returns parent products only (already does)
- **Price comparison** grouped by weight/quantity

### New columns on Product: `weight` (String), `weight_grams` (Float)
### New columns on ScraperFlag: `original_weight`, `original_price`, `original_category`

## Implementation Phases

### Phase A: Schema Changes (Non-Breaking)
- A1: Add weight columns to Product + Alembic migration
- A2: Add weight/price fields to ScraperFlag + Alembic migration
- A3: Create weight parsing utility (`services/normalization/weight_parser.py`)

### Phase B: Wire Up Fuzzy Matcher
- B1: Switch `scraper_runner.py` from `product_matcher.ProductMatcher` to `normalization.scorer.ConfidenceScorer`
- B2: Fix ConfidenceScorer transaction management (`commit()` -> `flush()`)
- B3: Cache fuzzy match candidates for performance

### Phase C: Parent/Variant Logic in Scraper Pipeline
- C1: Variant-aware product creation in ConfidenceScorer (find_or_create_variant helper)
- C2: Variant-aware flag resolution in FlagProcessor

### Phase D: Data Migration
- D1: Migration script (`scripts/migrate_to_variants.py`) - creates variants from existing masters, deduplicates, parses weights

### Phase E: Backend API Updates
- E1: Product detail - resolve variants to parent
- E2: Price comparison - group by weight
- E3: Search - aggregate prices across variants, add available_weights
- E4: Reviews - resolve variants to parent
- E5: Alert detectors - query through variants
- E6: Watchlist - resolve variants to parent
- E7: Dispensary inventory - include weight info

### Phase F: Frontend Updates
- F1: Product detail page - render grouped price tables
- F2: Search results - show weight badges
- F3: Admin cleanup page - show weight/price on flags

### Phase G: Seed Data & Tests
- G1: Update seed_test_data.py for parent/variant structure
- G2: New tests (weight_parser, variant_creation) + update existing tests

### Phase H: Documentation Updates
- H1: CLAUDE.md (schema, scraper architecture, patterns)
- H2: docs/ARCHITECTURE.md (data flow, schema)
- H3: docs/API_TEST_PLAN.md (new test cases)
- H4: docs/guides/SCRAPING.md (fuzzy matcher now active)
- H5: New workflow doc #12

## Deploy Notes

- Phases A-D can deploy incrementally
- Phases E+F must deploy together (API response shape changes require matching frontend)
