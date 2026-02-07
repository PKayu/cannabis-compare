# Plan: Fix Frontend-Backend Integration Issues

## Context

The user reports that the scrapers and search still don't appear to be working on the website at http://localhost:4002. Backend API testing shows:

**Backend APIs are working correctly:**
- `/api/admin/scrapers/health` returns 6 scrapers with health data
- `/api/products/search?q=lemon` returns products (Lemon OG, Lemon Up, etc.)
- Database has 2,035 products, 2 dispensaries, 87 scraper runs

**Root Cause Analysis:**
1. **CORS was missing port 4002** - Already fixed in main.py but may need server restart
2. **Frontend may not be connecting to backend** - Need to verify API client configuration
3. **Browser may have cached responses** - Hard refresh may be needed

## Investigation Findings

### Scrapers Status (from API):
| Scraper | Status | Success Rate | Last Run |
|---------|--------|--------------|----------|
| iHeartJane API | ❌ Error (0%) | Last run: 2026-01-31 | 2 failed runs |
| WholesomeCo | ⚠️ 34.7% | Last run: 2026-02-07 | 17 success, 15 failed |
| Beehive Playwright | ❌ Error (0%) | Last run: 2026-01-31 | 1 failed run |
| Curaleaf Lehi | ✅ 42.9% | Last run: 2026-02-01 | 355 products |
| Curaleaf Provo | ✅ 50% | Last run: 2026-02-01 | 387 products |
| Curaleaf Springville | ✅ 66.7% | Last run: 2026-02-01 | 385 products |

### Data in Database:
- **2,035 products** exist with `is_master=True`
- Products include: "Lemon OG", "Banana Blast", "Strawberry Cough", "Banana Runtz"
- **2 dispensaries** in database
- **87 scraper runs** recorded

## Implementation Plan

### Step 1: Verify CORS Configuration is Loaded

The backend `main.py` was updated to include port 4002 in CORS origins, but uvicorn may need to reload.

**Action**: Restart backend to ensure CORS changes take effect

### Step 2: Verify Frontend API Configuration

Check that frontend is pointing to correct backend URL.

**Files to check:**
- `frontend/.env.local` - Should have `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`
- `frontend/lib/api.ts` - API client configuration

**Test from frontend's perspective:**
```bash
curl -H "Origin: http://localhost:4002" "http://127.0.0.1:8000/api/admin/scrapers/health"
curl -H "Origin: http://localhost:4002" "http://127.0.0.1:8000/api/products/search?q=lemon&limit=2"
```

### Step 3: Check Browser Console for Errors

The frontend may have JavaScript errors preventing data display.

**Common issues to check:**
1. CORS errors in browser console
2. Network requests failing (check Network tab)
3. React errors preventing render
4. Axios interceptor errors

### Step 4: Fix Scraper Display Issues (if data loads but doesn't show)

If API returns data but UI shows nothing, check:
1. Admin scrapers page state management
2. Search page filtering logic
3. Loading states getting stuck

### Step 5: Fix Scraper Execution Issues

Several scrapers are failing (WholesomeCo Python 3.13 issue, Beehive Playwright issues).

**Already implemented:** WindowsProactorEventLoopPolicy fix in main.py and playwright_scraper.py

**Alternative solution:** If Playwright still fails on Python 3.13, may need to switch to Python 3.12 venv.

## Critical Files

| File | Purpose |
|------|---------|
| `backend/main.py` | CORS configuration, event loop policy |
| `frontend/.env.local` | API URL configuration |
| `frontend/lib/api.ts` | Axios client with auth interceptors |
| `frontend/app/(admin)/admin/scrapers/page.tsx` | Admin scrapers UI |
| `frontend/app/products/search/page.tsx` | Search UI |

## Verification

1. **Frontend loads scrapers:** Visit http://localhost:4002/admin/scrapers and see 6 scraper cards
2. **Search returns results:** Search for "lemon" at http://localhost:4002/products/search and see products
3. **No CORS errors:** Browser console shows no CORS errors
4. **Manual scraper run:** Click "Run Now" button on admin scrapers page
5. **Products display:** Click on a product to see details page

## Notes

- **Backend APIs work** - confirmed via curl
- **Database has data** - 2,035 products confirmed
- **Issue is likely frontend-backend connection** or browser caching
- **Hard refresh** (Ctrl+Shift+R or Ctrl+F5) may be required after CORS fix
