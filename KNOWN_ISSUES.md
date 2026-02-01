# Known Issues

## WholesomeCo Scraper - API Returns 0 Products (Blocking)

**Status:** Open
**Priority:** High
**Date Reported:** 2026-01-31

### Description
The WholesomeCo scraper works correctly when run directly (757 products with THC data), but when triggered through the admin UI (API endpoint `/api/admin/scrapers/run/wholesomeco`), it returns:
- Status: `warning`
- Products Found: `0`
- Duration: ~0.009 seconds (too short for actual scraping)

### What Works
- Direct script execution: 757 products, success status
- Test via `backend\venv\Scripts\python.exe`: 757 products
- Test via system `C:\Python313\python.exe`: 756 products
- All scraper code is correct (infinite scroll, THC extraction)

### What Doesn't Work
- API endpoint call: 0 products, warning status
- Admin UI "Run" button: 0 products, warning status

### Investigation Notes
1. Both Python environments (system and venv) have FastAPI and Playwright installed
2. The scraper code in `playwright_scraper.py` is correct
3. Cache has been cleared (`__pycache__`, `*.pyc` files)
4. Multiple server restarts attempted
5. Server may be caching old modules despite `--reload` flag

### Possible Causes
- Module import caching in the running server process
- The server imports modules at startup before code changes are detected
- Async context differences between direct script and FastAPI endpoint
- Playwright browser context issues in server environment

### Next Steps to Investigate
1. Complete server restart (stop all Python processes, not just uvicorn)
2. Check if there's a difference in `sys.path` between direct script and API context
3. Add detailed logging to the scraper to see where it fails in API context
4. Consider using a fresh virtual environment
5. Check for multiple main.py files or import conflicts
6. Verify Playwright browser can launch in the server's async context

### Files Involved
- `backend/services/scrapers/playwright_scraper.py` (WholesomeCoScraper)
- `backend/services/scraper_runner.py` (run_by_id method)
- `backend/routers/admin_scrapers.py` (trigger_scraper_run endpoint)
- `backend/main.py` (scraper imports)
