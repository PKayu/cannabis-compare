# Plan: Simplify Product Flagging & Cleanup Dashboard

## Context

The admin is frustrated with the 60-90% confidence "match review" workflow. Every flagged card asks "is this a match?" — but if it's below 90%, it's never a match. The admin wants:
- Products with clean data auto-created silently (no review needed)
- Products with dirty data flagged so they can **clean up the data** (not decide on matches)

This overhaul eliminates match reviews entirely and replaces them with a data quality cleanup workflow.

## New Scoring Logic

```
>90% match  → Auto-merge to existing product (UNCHANGED)
<90% match  → Always create as new product
                ├─ Clean data  → is_active=True, no flag (done)
                └─ Dirty data  → is_active=False, "data_cleanup" flag for admin
```

**Dirty data triggers** (user-confirmed):
- Junk/garbage in name (HTML, special chars, promo text surviving cleanup)
- Missing or zero price
- Unknown/missing brand

**NOT dirty** (user explicitly excluded): missing weight, missing category.

## Step 0: Setup — `.claude/launch.json`

Create `.claude/launch.json` for dev server management:
```json
{
  "version": "0.0.1",
  "configurations": [
    { "name": "frontend", "runtimeExecutable": "npm", "runtimeArgs": ["--prefix", "frontend", "run", "dev"], "port": 4002 },
    { "name": "backend", "runtimeExecutable": "python", "runtimeArgs": ["backend/run_server.py"], "port": 8000 }
  ]
}
```

## Step 1: Database Migration — Add `flag_type` column

**New migration file**: `backend/alembic/versions/XXXX_add_flag_type.py`
- Add `flag_type` (String, default `"match_review"`, indexed) to `scraper_flags`
- Backfill all existing rows to `"match_review"`

**Modify**: `backend/models.py`
- Add `flag_type = Column(String, default="match_review", index=True)` to ScraperFlag
- Add `"cleaned"` to status comment

## Step 2: Create Data Quality Checker

**New file**: `backend/services/normalization/data_quality.py`

```python
def check_data_quality(scraped: ScrapedProduct, cleaned_name: str) -> Tuple[bool, List[str]]:
```

Three checks:
1. `_has_junk_in_name(raw, cleaned)` — compares raw vs cleaned name; checks if >30% was removed or if junk patterns remain
2. `missing_price` — `price is None or price <= 0`
3. `_is_unknown_brand(brand)` — brand is None/empty/"Unknown"/"N/A"

Returns `(is_dirty, ["junk_in_name", "missing_price", ...])`.

## Step 3: Modify ConfidenceScorer — Core Logic Change

**File**: `backend/services/normalization/scorer.py`

Eliminate the `flagged_review` branch entirely. The `else` branch (which was only for `<60%`) now handles ALL `<90%` products:

- Always create parent (`is_active=not is_dirty`) + variant + price
- If dirty: also create ScraperFlag with `flag_type="data_cleanup"`, `status="pending"`, `matched_product_id=parent.id` (points to CREATED product, not a match suggestion), `issue_tags` pre-populated
- Return `"new_product_flagged"` (new action type) or `"new_product"`

Key: `matched_product_id` now means "the product TO EDIT" for data_cleanup flags, not "suggested match".

## Step 4: Update ProductMatcher Thresholds

**File**: `backend/services/normalization/matcher.py`

- Remove `REVIEW_THRESHOLD = 0.60`
- Simplify `score_match()` to only two outcomes: `"auto_merge"` (>=0.90) or `"new_product"`
- Update `get_threshold_description()`

## Step 5: Update ScraperRunner

**File**: `backend/services/scraper_runner.py`

- Remove the `if action == "flagged_review": continue` skip
- All products now get prices (even flagged dirty ones)
- Track `flags_created` for `"new_product_flagged"` action

## Step 6: New Flag Processor Methods

**File**: `backend/services/normalization/flag_processor.py`

Add two new methods:

### `clean_and_activate(db, flag_id, admin_id, edits...)`
- Loads the flag, verifies `flag_type="data_cleanup"` and `status="pending"`
- Loads the product via `flag.matched_product_id`
- Applies field edits (name, brand, category, THC, CBD, weight, price)
- Sets `product.is_active = True`
- Marks flag `status="cleaned"`
- Tracks corrections

### `delete_flagged_product(db, flag_id, admin_id, notes)`
- Deletes the linked product + variants (garbage data)
- Marks flag `status="dismissed"`
- Clears `matched_product_id` (product is gone)

Keep existing `approve_flag`, `reject_flag`, `dismiss_flag` for legacy match_review flags.

## Step 7: New API Endpoints

**File**: `backend/routers/admin_flags.py`

New endpoints:
- `POST /api/admin/flags/clean/{flag_id}` — Clean & activate (body: name, brand, category, etc.)
- `POST /api/admin/flags/delete-product/{flag_id}` — Delete garbage product

Updated endpoints:
- `GET /api/admin/flags/pending` — Add `flag_type` query param filter
- `GET /api/admin/flags/stats` — Add `pending_cleanup`, `pending_review`, `cleaned` counts
- `POST /api/admin/flags/bulk-action` — Support `"clean"` and `"delete_product"` actions

## Step 8: Frontend API & Types

**File**: `frontend/lib/api.ts`
- Add `api.admin.flags.clean(flagId, data)` and `api.admin.flags.deleteProduct(flagId, data)`
- Add `flag_type` param to `pending()` call
- Update `bulkAction` to support `"clean"` and `"delete_product"`

**File**: Types (in hooks or api.ts)
- Add `flag_type: 'match_review' | 'data_cleanup'` to ScraperFlag type
- Add `'cleaned'` to status union
- Add `pending_cleanup`, `pending_review`, `cleaned` to FlagStats

## Step 9: Overhaul Frontend Tabs

**File**: `frontend/app/(admin)/admin/cleanup/page.tsx` + `FilterTabs.tsx`

New tab structure:
| Tab | Filter | Purpose |
|-----|--------|---------|
| **Data Cleanup** (default) | `flag_type=data_cleanup` | Fix dirty products and activate |
| **Legacy Reviews** | `flag_type=match_review` | Clear remaining old-style flags |
| **Auto-Linked** | `include_auto_merged=true` | Spot-check >90% merges |
| **All** | none | Audit view |

Default tab: `data_cleanup` (most common workflow going forward).

## Step 10: Overhaul FlagCard Component

**File**: `frontend/app/(admin)/admin/cleanup/components/FlagCard.tsx`

Conditional rendering based on `flag.flag_type`:

**`data_cleanup` mode:**
- Hide confidence score badge (irrelevant)
- Hide "Suggested Match" comparison section entirely
- Show issue tag badges prominently: "Junk in Name", "Missing Price", "Unknown Brand"
- Show source URL link for verification
- Editable fields: name, brand, category, weight, price, THC, CBD
- Actions: **"Save & Activate"** (green) + **"Delete"** (red)

**`match_review` mode (legacy):**
- Keep existing approve/reject/dismiss UI unchanged

New props: `onCleanAndActivate`, `onDeleteProduct`

## Step 11: Update Bulk Actions & Swipe View

**File**: `BulkActions.tsx`
- When tab is `data_cleanup`: show "Activate All" + "Delete All" buttons
- When tab is `legacy_review`: show existing "Approve/Reject/Dismiss All"

**File**: `CleanupSwipeView.tsx`
- Default to loading `data_cleanup` flags
- Pass new handler props

## Step 12: Existing Data Migration

- All existing pending flags get `flag_type="match_review"` via migration default
- They appear under "Legacy Reviews" tab
- Admin resolves them at their own pace using existing approve/reject/dismiss
- Once cleared, the tab can be hidden in a future pass

## Step 13: Tests

**New**: `backend/tests/test_data_quality.py`
- Clean product returns `(False, [])`
- Missing price: `(True, ["missing_price"])`
- Unknown brand: `(True, ["unknown_brand"])`
- Junk name: `(True, ["junk_in_name"])`
- Multiple issues: all detected
- Missing weight: NOT flagged (explicit requirement)
- Missing category: NOT flagged

**Update**: `backend/tests/test_matcher.py`
- Remove `flagged_review` tests, only test `auto_merge` and `new_product`

**New**: `backend/tests/test_flag_processor_cleanup.py`
- `clean_and_activate`: product activated, edits applied, flag resolved
- `delete_flagged_product`: product deleted, flag dismissed
- Error cases: wrong flag_type, already resolved

## Critical Files Summary

| File | Change |
|------|--------|
| `backend/models.py` | Add `flag_type` column, update status comment |
| `backend/services/normalization/data_quality.py` | **NEW** — data quality checker |
| `backend/services/normalization/scorer.py` | Eliminate `flagged_review`, add quality check |
| `backend/services/normalization/matcher.py` | Remove `REVIEW_THRESHOLD`, two outcomes only |
| `backend/services/scraper_runner.py` | Remove flagged_review skip |
| `backend/services/normalization/flag_processor.py` | Add `clean_and_activate`, `delete_flagged_product` |
| `backend/routers/admin_flags.py` | New endpoints, `flag_type` filter, updated stats |
| `frontend/lib/api.ts` | New API methods, updated types |
| `frontend/.../cleanup/page.tsx` | New handlers, new default tab |
| `frontend/.../cleanup/components/FlagCard.tsx` | Dual-mode rendering |
| `frontend/.../cleanup/components/FilterTabs.tsx` | New tab structure |
| `frontend/.../cleanup/components/BulkActions.tsx` | Context-aware buttons |

## Verification

1. **Backend tests**: `cd backend && pytest tests/test_data_quality.py tests/test_matcher.py tests/test_flag_processor_cleanup.py -v`
2. **Full backend tests**: `cd backend && pytest`
3. **Frontend type check**: `cd frontend && npm run type-check`
4. **Manual test**: Run a scraper via admin dashboard, verify:
   - Clean products auto-created and visible in search
   - Dirty products appear in "Data Cleanup" tab with correct issue tags
   - "Save & Activate" applies edits and makes product visible
   - "Delete" removes garbage product
5. **Legacy flags**: Verify existing pending flags appear in "Legacy Reviews" tab with original UI
