# Cleanup Dashboard Improvements — Context

## Key Files

### Backend
- `backend/services/normalization/name_cleaner.py` — NEW utility
- `backend/services/normalization/matcher.py` — weights at lines 26-28
- `backend/services/normalization/scorer.py` — auto-merge at lines 160-171; wire name_cleaner
- `backend/services/normalization/flag_processor.py` — approve_flag(); new merge_duplicate_flag()
- `backend/services/scrapers/base_scraper.py` — ScrapedProduct dataclass (add thc_content/cbd_content)
- `backend/models.py` — Product + ScraperFlag models
- `backend/routers/admin_flags.py` — endpoints + schema
- `backend/alembic/versions/` — new migration

### Frontend
- `frontend/app/(admin)/admin/cleanup/components/FlagCard.tsx` — approve button + edit-both-products
- `frontend/app/(admin)/admin/cleanup/components/FilterTabs.tsx` — tab definitions
- `frontend/app/(admin)/admin/cleanup/page.tsx` — tab logic

## Key Decisions
- THC/CBD stored as plain text (e.g., "15.4%" or "396mg") in new `thc_content` column
- Keep `thc_percentage` float for backward compat (set to null when source is mg)
- Auto-merges create ScraperFlag with status="auto_merged" for auditing
- Fuzzy matching: Name 75%, Brand 25%, THC 0%
- Duplicate merge: move Price/Review/Watchlist to winner, soft-delete loser (is_active=False)
- Approve button fix: check `matched_product_id || matched_product?.id`

## Root Causes Found
- Approve button: `disabled={!flag.matched_product_id}` but API may not return bare FK even when nested object is populated
- THC "396.96%": mg value stored as float in thc_percentage with no unit tracking
- Name junk: scraper HTML composition leaves "Fruit of mg mg Add 800mg to cart" artifacts
