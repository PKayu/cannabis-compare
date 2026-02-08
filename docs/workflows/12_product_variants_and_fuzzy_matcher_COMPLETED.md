# Workflow 12: Product Variants & Fuzzy Matcher Wiring

## Status: COMPLETED (2026-02-07)

## Context
- Extends Workflow 03 (Scraper Foundation) and Workflow 11 (Automated Scraping)
- Addresses the need for products to exist at multiple weights (e.g., "Blue Dream 3.5g" vs "Blue Dream 7g")
- Activates the fuzzy matching system that was previously implemented but not wired into the scraper pipeline

## Overview

This workflow implements two major features:

1. **Parent/Variant Product Model**: Products now follow a hierarchical structure where a parent product represents the canonical strain and variant products represent specific weights. Reviews attach to parents; prices attach to variants.

2. **Fuzzy Matcher Activation**: The `ConfidenceScorer` is now the active matching system in `scraper_runner.py`, replacing the old exact-match `ProductMatcher`. Scraped products are automatically matched, flagged, or created as new products based on confidence thresholds.

---

## Phase 1: Parent/Variant Data Model (COMPLETED)

### Step 1.1: Product Model Changes
- **File**: `backend/models.py`
- Added columns to Product model:
  - `weight` (String, Optional) - Display label like "3.5g", "1oz"
  - `weight_grams` (Float, Optional) - Normalized weight in grams
  - `is_master` (Boolean, Default: True) - True for parent products
  - `master_product_id` (UUID, FK to Product.id, Optional) - Self-referential FK for variants
- Added self-referential relationship:
  - `Product.variants` - List of child variants (from parent)
  - `Product.master_product` - Parent reference (from variant)

### Step 1.2: ScraperFlag Model Changes
- **File**: `backend/models.py`
- Added fields to ScraperFlag:
  - `original_weight` (String, Optional) - Weight from the scraped product
  - `original_price` (Float, Optional) - Price from the scraped product
  - `original_category` (String, Optional) - Category from the scraped product

### Step 1.3: Database Migration
- **File**: `backend/alembic/versions/20260207_000001_add_product_variants_and_weight.py`
- Adds `weight`, `weight_grams`, `is_master`, `master_product_id` to products table
- Adds `original_weight`, `original_price`, `original_category` to scraper_flags table
- Adds self-referential foreign key constraint

### Verification
```bash
cd backend
alembic upgrade head
# Verify columns exist:
python -c "
from database import SessionLocal
from models import Product
db = SessionLocal()
p = db.query(Product).first()
print(f'is_master: {p.is_master}, weight: {p.weight}, weight_grams: {p.weight_grams}')
db.close()
"
```

---

## Phase 2: Weight Parser (COMPLETED)

### Step 2.1: Weight Parser Service
- **File**: `backend/services/normalization/weight_parser.py` (NEW)
- Parses weight strings from product names and explicit weight fields
- Supports formats: "3.5g", "1oz", "1/8 oz", "1000mg", "1g Pre-Roll"
- Returns normalized label (e.g., "3.5g") and gram value (e.g., 3.5)
- Handles edge cases: fractions, mixed units, embedded weights in names

### Step 2.2: Weight Parser Tests
- **File**: `backend/tests/test_weight_parser.py` (NEW)
- Unit tests covering all supported weight formats
- Edge case testing for unusual inputs

### Verification
```bash
cd backend
pytest tests/test_weight_parser.py -v
```

---

## Phase 3: Fuzzy Matcher Wiring (COMPLETED)

### Step 3.1: ConfidenceScorer Updates
- **File**: `backend/services/normalization/scorer.py`
- Added `find_or_create_variant()` method for variant-aware product creation
- When a match is found (or new product created), the scorer:
  1. Parses weight from the scraped product
  2. Finds or creates a variant under the parent product
  3. Returns the variant product for price attachment
- Uses `db.flush()` for transaction control (caller commits)

### Step 3.2: ScraperRunner Integration
- **File**: `backend/services/scraper_runner.py`
- Now imports `ConfidenceScorer` instead of old `ProductMatcher`
- Pre-loads master product candidates at start of scraper run (candidate caching)
- Confidence thresholds:
  - **>90%**: Auto-merge with existing product
  - **60-90%**: Create ScraperFlag for admin review
  - **<60%**: Create new parent product
- Prices are attached to variant products returned by the scorer

### Step 3.3: Flag Processor Updates
- **File**: `backend/services/normalization/flag_processor.py`
- Approve action now creates a variant under the matched product
- Reject action creates a new parent product with a variant
- Both actions preserve weight/price/category from the flag

### Step 3.4: Variant Creation Tests
- **File**: `backend/tests/test_variant_creation.py` (NEW)
- Tests for variant creation logic
- Tests for parent/variant relationship integrity

### Verification
```bash
cd backend
pytest tests/test_variant_creation.py -v
pytest tests/test_weight_parser.py -v
```

---

## Phase 4: API Updates (COMPLETED)

### Step 4.1: Product Detail & Prices
- **File**: `backend/routers/products.py`
- Product detail endpoint resolves variants to parent for display
- Price endpoint returns prices grouped by weight variant
- `/api/products/{id}/prices` returns `prices_by_weight` structure

### Step 4.2: Search Results
- **File**: `backend/routers/search.py`
- Search aggregates prices across all variants of a parent product
- Response includes `available_weights` field listing all variant weights
- Lowest price is computed across all variants

### Step 4.3: Reviews (Variant-to-Parent Resolution)
- **File**: `backend/routers/reviews.py`
- When a review is posted with a variant product ID, the backend resolves it to the parent product
- Reviews are always stored on parent products

### Step 4.4: Watchlist (Variant-to-Parent Resolution)
- **File**: `backend/routers/watchlist.py`
- When a variant ID is added to watchlist, it resolves to the parent product
- Watchlist entries always reference parent products

### Step 4.5: Dispensary Inventory
- **File**: `backend/routers/dispensaries.py`
- Inventory endpoint includes weight information from variant products

### Step 4.6: Alert Detectors
- **Files**: `backend/services/alerts/stock_detector.py`, `backend/services/alerts/price_detector.py`
- Both detectors now query prices through variant products
- Alert notifications reference the parent product name with variant weight context

### Verification
```bash
# Test grouped prices
curl http://localhost:8000/api/products/prod-001/prices

# Test search with available_weights
curl "http://localhost:8000/api/products/search?q=blue+dream"

# Test dispensary inventory with weight info
curl http://localhost:8000/api/dispensaries/disp-001/inventory
```

---

## Phase 5: Frontend Updates (COMPLETED)

### Step 5.1: Product Detail Page
- **File**: `frontend/app/products/[id]/page.tsx`
- Price comparison table now grouped by weight with tab/section navigation
- Each weight group shows dispensary prices side-by-side

### Step 5.2: Search Results
- **File**: `frontend/components/ResultsTable.tsx`
- Weight badges displayed on search result cards
- Shows available weights for each product

### Step 5.3: Admin Cleanup Queue
- **File**: `frontend/app/(admin)/admin/cleanup/page.tsx`
- Flag cards now display `original_weight`, `original_price`, and `original_category`
- Provides context for admin when reviewing fuzzy match flags

### Verification
```bash
cd frontend && npm run dev
# Navigate to product detail page - verify grouped price tables
# Search for a product - verify weight badges
# Visit /admin/cleanup - verify weight/price/category on flag cards
```

---

## Phase 6: Data Migration (COMPLETED)

### Step 6.1: Migration Script
- **File**: `backend/scripts/migrate_to_variants.py` (NEW)
- Three-phase migration for existing data:
  1. **Create variants**: For each existing product with prices, create variant records
  2. **Deduplicate**: Merge products that represent the same strain at different weights
  3. **Parse weights**: Extract and normalize weight information from product names

### Running the Migration
```bash
cd backend
# Dry run (no database changes)
python scripts/migrate_to_variants.py --dry-run

# Full migration
python scripts/migrate_to_variants.py
```

---

## Phase 7: Seed Data Updates (COMPLETED)

### Step 7.1: Updated Seed Data
- **File**: `backend/seed_test_data.py`
- Seed data now creates parent products (`is_master=True`) with no weight
- Creates variant products (`is_master=False`) with `weight`, `weight_grams`, and `master_product_id`
- Prices are attached to variant products
- Reviews are attached to parent products

---

## Success Criteria

- [x] Product model supports parent/variant hierarchy with `is_master`, `master_product_id`, `weight`, `weight_grams`
- [x] Weight parser correctly handles "3.5g", "1oz", "1/8 oz", "1000mg" formats
- [x] ConfidenceScorer is wired into ScraperRunner with candidate caching
- [x] >90% confidence auto-merges, 60-90% creates flag, <60% creates new product
- [x] Variant products are created with weight fields during scraper runs
- [x] Prices always attach to variant products, never parents
- [x] Reviews resolve variant IDs to parent IDs
- [x] Watchlist resolves variant IDs to parent IDs
- [x] Product detail page shows prices grouped by weight
- [x] Search results include `available_weights`
- [x] Admin cleanup queue shows weight/price/category on flag cards
- [x] Flag approve/reject operations are variant-aware
- [x] Alert detectors query prices through variants
- [x] Seed data follows parent/variant structure
- [x] Data migration script handles existing data conversion
- [x] Database migration adds all required columns
- [x] All new tests pass

## Files Modified/Created

| File | Action |
|------|--------|
| `backend/models.py` | Modified - Product weight columns, ScraperFlag new fields, self-referential relationship |
| `backend/services/normalization/scorer.py` | Modified - `find_or_create_variant()`, variant-aware product creation |
| `backend/services/normalization/weight_parser.py` | Created - Weight string parsing and normalization |
| `backend/services/normalization/flag_processor.py` | Modified - Variant-aware approve/reject |
| `backend/services/scraper_runner.py` | Modified - Uses ConfidenceScorer with candidate caching |
| `backend/routers/products.py` | Modified - Variant resolution, grouped-by-weight prices |
| `backend/routers/search.py` | Modified - Aggregated prices across variants, available_weights |
| `backend/routers/reviews.py` | Modified - Variant-to-parent resolution |
| `backend/routers/watchlist.py` | Modified - Variant-to-parent resolution |
| `backend/routers/dispensaries.py` | Modified - Weight info in inventory |
| `backend/services/alerts/stock_detector.py` | Modified - Query prices through variants |
| `backend/services/alerts/price_detector.py` | Modified - Query prices through variants |
| `backend/seed_test_data.py` | Modified - Parent/variant structure |
| `backend/scripts/migrate_to_variants.py` | Created - Three-phase data migration |
| `backend/tests/test_weight_parser.py` | Created - Weight parser unit tests |
| `backend/tests/test_variant_creation.py` | Created - Variant creation logic tests |
| `backend/alembic/versions/20260207_000001_add_product_variants_and_weight.py` | Created - Migration |
| `frontend/app/products/[id]/page.tsx` | Modified - Grouped price tables by weight |
| `frontend/components/ResultsTable.tsx` | Modified - Weight badges on search results |
| `frontend/app/(admin)/admin/cleanup/page.tsx` | Modified - Weight/price/category on flag cards |

---

## Addendum: Product Name Cleaning (2026-02-07)

### Issue Identified

After implementing the parent/variant model, we discovered that weights were being stored redundantly:
- Scraped product names often contained weights (e.g., "Blue Dream 3.5g")
- The `scorer.py` was using these names directly when creating parent products
- This resulted in weights appearing in both the `name` field AND the `weight`/`weight_grams` fields

### Fix Applied

**Updated `scorer.py` to clean product names before creating parents:**

1. Added import for `extract_weight_from_name()` from `weight_parser.py`
2. Modified `process_scraped_product()` to extract weights from names before fuzzy matching
3. Parent products now use clean names (e.g., "Blue Dream" instead of "Blue Dream 3.5g")
4. Extracted weights are used as fallback if scraper didn't provide weight separately
5. Fuzzy matching now compares clean names for better match quality

**Files Modified:**
- `backend/services/normalization/scorer.py` - Added name cleaning logic

**New Scripts Created:**
- `backend/scripts/audit_product_names.py` - Audit script to check for products with weights in names
- `backend/scripts/purge_scraped_data.py` - Purge script to delete scraped data while preserving seed data

**New Tests:**
- `backend/tests/test_scorer_name_cleaning.py` - Comprehensive tests for name cleaning functionality (6 tests, all passing)

### Result

- ✅ Parent products have clean names without weights
- ✅ Variant products inherit clean names from parents
- ✅ Weights stored exclusively in `weight` and `weight_grams` fields
- ✅ Fuzzy matching improved (compares "Blue Dream" to "Blue Dream", not "Blue Dream 3.5g")
- ✅ No redundant weight information

### Data Migration

If you have existing scraped data with weights in names, use the provided scripts:
```bash
# 1. Audit current data
python scripts/audit_product_names.py

# 2. Purge scraped data (preserves seed data)
python scripts/purge_scraped_data.py

# 3. Re-run scrapers with fixed pipeline
# Visit /admin/scrapers and trigger manual runs
```
