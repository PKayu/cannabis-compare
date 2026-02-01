# Known Issues

## WholesomeCo Scraper - API Returns 0 Products (✅ RESOLVED)

**Status:** ✅ Resolved
**Priority:** High
**Date Reported:** 2026-01-31
**Date Resolved:** 2026-02-01

### Root Cause
The `PlaywrightScraper.scrape_promotions()` method was missing its return type annotation (`-> List[ScrapedPromotion]`). Python's Abstract Base Class (ABC) system requires the **exact same method signature** (including return types) to recognize an abstract method as implemented. Without the matching return type, the class was still considered abstract and could not be instantiated, causing a `NotImplementedError`.

### Description
The WholesomeCo scraper works correctly when run directly (757 products with THC data), but when triggered through the admin UI (API endpoint `/api/admin/scrapers/run/wholesomeco`), it returns:
- Status: `error` (with `NotImplementedError`)
- Products Found: `0`
- Duration: ~0.009 seconds (too short for actual scraping)

### What Works
- Direct script execution: 757 products, success status
- Test via `backend\venv\Scripts\python.exe`: 757 products
- Test via system `C:\Python313\python.exe`: 756 products

### What Doesn't Work
- API endpoint call: 0 products, NotImplementedError (before fix)
- Admin UI "Run" button: 0 products, NotImplementedError (before fix)

### Fix Applied

**File: `backend/services/scrapers/playwright_scraper.py`**

1. **Added missing import** (line 12):
```python
from .base_scraper import BaseScraper, ScrapedProduct, ScrapedPromotion
```

2. **Added return type annotation** (line 222):
```python
async def scrape_promotions(self) -> List[ScrapedPromotion]:
    """
    Scrape promotional information from the page

    Currently not implemented for Playwright scraper
    """
    return []
```

### Applying the Fix

To apply this fix, you must **restart the backend server** to pick up the code changes:

1. **Stop all Python processes**:
   - Open Task Manager (Ctrl+Shift+Esc)
   - Go to "Details" tab
   - End all `python.exe` tasks

2. **Restart the server**:
   ```cmd
   cd "D:\Projects\cannabis compare\backend"
   venv\Scripts\python.exe -m uvicorn main:app --port 8000
   ```

   Or use the provided script:
   ```cmd
   backend\restart_server.bat
   ```

3. **Test the scraper**:
   - Via API: `curl -X POST "http://localhost:8000/api/admin/scrapers/run/wholesomeco"`
   - Via Admin UI: `http://localhost:3000/admin/scrapers`

### Verification
After applying the fix and restarting the server:
- Scraper should instantiate without errors
- API calls should return 750+ products
- Duration should be 30-60 seconds (not 0.009 seconds)

### Files Involved
- `backend/services/scrapers/playwright_scraper.py` (Fixed - added return type annotation and import)
- `backend/services/scraper_runner.py` (Added debug logging)
- `backend/restart_server.bat` (New - helper script for clean server restart)
