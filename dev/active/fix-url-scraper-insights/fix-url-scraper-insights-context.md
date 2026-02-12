# Context: Fix URL Extraction & Scraper Insights

## Key Files Modified
- `backend/services/scrapers/playwright_scraper.py` - WholesomeCo URL extraction (3 edits)
- `frontend/app/(admin)/admin/scraper-insights/page.tsx` - New insights page

## Key Decisions
- Used broad `a[href]` selector for WholesomeCo URL extraction (scoped to .productListItem)
- Built insights page from 3 existing endpoints (no backend changes needed)
- Confirmed all existing uncommitted URL propagation code is correct

## Last Updated
2026-02-08
