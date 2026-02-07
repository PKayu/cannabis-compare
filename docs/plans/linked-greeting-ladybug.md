# Troubleshooting Plan: Scrapers Not Showing & Data Not Displaying

## Status: IMPLEMENTED (2026-02-07)

The async background execution fix described in Phase 2-3 of this plan has been implemented. See the changes to `backend/routers/admin_scrapers.py` (fire-and-forget via `asyncio.create_task()`), `backend/services/scraper_runner.py` (commit instead of flush for ScraperRun visibility), and `frontend/app/(admin)/admin/scrapers/page.tsx` (polling-based run status).

## Context

This plan analyzes why scrapers are not appearing in the admin dashboard and why data is not showing in the web app, after reviewing previous plans and the current codebase state.

### User-Reported Symptoms
1. Admin dashboard shows no scrapers
2. Web app shows no products
3. **Key finding**: Scrapers previously worked when pulling 12 products, but when increased to pull more products, manual runs via admin dashboard failed - only command-line execution worked

### Likely Root Cause
When scrapers pull more data, the HTTP request timeout is exceeded. The admin dashboard triggers scrapers via HTTP POST (`/api/admin/scrapers/run/{id}`), which has a default timeout. Command-line runs don't have this timeout constraint.

## Previous Plans Analysis

### Plan History Reviewed

1. **tranquil-jingling-map.md** - *Not for this project* (Family Hub Calendar - completely different codebase)

2. **polished-jumping-plum.md** - Phase 1 Completion Plan (Jan 2026)
   - Status: Phase 1 marked as COMPLETED ✅
   - Implemented: 8 tables, 26 indexes, admin API, scraper foundation
   - What was planned: Workflows 02-04 (database, scrapers, admin dashboard)

3. **misty-rolling-fox.md** - Phase 2 Implementation: Price Comparison Search (Workflow 05)
   - Focus: Frontend portal with search, product details, dispensary pages
   - This was the next planned phase

### Active Tasks Found
- `dev/active/phase1-completion/` - Phase 1 marked complete
- `dev/active/admin-dashboard-scraper-automation/` - Admin dashboard with scraper automation

## Root Cause Analysis

### Issue 1: Scrapers Not Appearing in Admin Dashboard

**Finding**: The scrapers ARE properly registered and the code is correct.

**Evidence**:
- [main.py:27-42](backend/main.py) - All scrapers imported correctly
- [registry.py](backend/services/scrapers/registry.py) - Self-registration system working
- [admin_scrapers.py:126-162](backend/routers/admin_scrapers.py) - Health endpoint queries `ScraperRegistry.get_all()`

**Likely Root Causes**:
1. **No ScraperRun records in database** - The health endpoint shows scrapers but if there are no run records, they may appear empty
2. **Backend not running** - The admin dashboard can't connect if backend is down
3. **Scheduler never started** - Scrapers won't run automatically if scheduler isn't initialized
4. **Database connection issue** - Can't query scraper run history

**Verification needed**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check if scheduler has jobs
curl http://localhost:8000/api/admin/scrapers/scheduler/status

# Check registered scrapers
cd backend
python -c "from services.scrapers.registry import ScraperRegistry; print(list(ScraperRegistry.get_all().keys()))"
```

### Issue 2: Data Not Showing in Web App

**Finding**: The API endpoints and frontend code are correctly implemented.

**Evidence**:
- [products.py:13-54](backend/routers/products.py) - Product detail endpoint working
- [search.py:12-149](backend/routers/search.py) - Search endpoint with fuzzy matching
- [api.ts:80-95](frontend/lib/api.ts) - Frontend API client properly configured

**Likely Root Causes**:
1. **No products in database** - Database exists but has no master products
2. **Scrapers never successfully ran** - No data was ever scraped
3. **Database migrations not applied** - Tables might not exist
4. **Environment variables misconfigured** - Frontend can't reach backend

**Verification needed**:
```bash
# Check database for products
cd backend
python -c "
from database import SessionLocal
from models import Product, Price
db = SessionLocal()
print(f'Products: {db.query(Product).count()}')
print(f'Master Products: {db.query(Product).filter(Product.is_master == True).count()}')
print(f'Prices: {db.query(Price).count()}')
db.close()
"

# Check frontend can connect
curl http://localhost:8000/api/products/search?q=test&limit=5
```

## What Went Wrong with Previous Plans

### 1. Scrapers Were Working But Broke at Scale
- **Initial state**: Scrapers pulled 12 products successfully via admin dashboard
- **After expansion**: When increased to pull more products, admin dashboard runs failed
- **Workaround**: Command-line runs still worked
- **Root cause**: HTTP timeout when scraper takes too long

### 2. Plan Disconnect
Previous plans focused on **building features** but didn't address:
- Long-running scraper execution via HTTP
- Background job execution patterns
- Timeout configuration for API endpoints

### 3. Missing "First Run" Procedures
The scraper system was built but:
- No clear instruction to handle long-running scrapers
- No verification that scrapers complete successfully at scale
- No async/background task handling for admin-triggered runs

## Recommended Fix Plan

### Phase 1: Diagnose System State (15 min)

1. **Start Backend Server**
   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

2. **Verify Backend Health**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/api/admin/scrapers/health
   ```

3. **Check Database State**
   - Count products, prices, dispensaries, scraper_runs
   - Verify tables exist and have data

4. **Check Scraper Registration**
   - Verify all scrapers are registered
   - Check scheduler job count

### Phase 2: Fix HTTP Timeout Issue (CRITICAL) -- IMPLEMENTED

**Problem**: The `/api/admin/scrapers/run/{scraper_id}` endpoint runs scrapers synchronously. When scrapers pull many products, they exceed the HTTP request timeout (usually 30-120 seconds).

**Solution Options**:

**Option A: Increase Timeout (Quick Fix)**
- Modify FastAPI/uvicorn timeout settings
- Add `timeout` parameter to endpoint
- Downside: Still has limits, not ideal for long-running tasks

**Option B: Background Tasks (Recommended)**
- Use FastAPI `BackgroundTasks` to run scrapers asynchronously
- Return immediately with a "running" status
- Client polls for completion status

**Option C: Separate Worker Process**
- Run scrapers in separate worker process (Celery, asyncio tasks)
- More robust but requires additional infrastructure

### Phase 3: Implement Background Task Fix -- IMPLEMENTED

**File modified**: [backend/routers/admin_scrapers.py](backend/routers/admin_scrapers.py)

The actual implementation used `asyncio.create_task()` with a helper `_run_scraper_in_background()` function that creates its own `SessionLocal()` database session. The `ScraperRunner` commit (not flush) pattern was also fixed in `scraper_runner.py` so the "running" status is visible to polling sessions. The frontend (`admin/scrapers/page.tsx`) now polls `/runs` every 5 seconds after triggering.

Original plan proposed changing the trigger endpoint from:
```python
@router.post("/run/{scraper_id}")
async def trigger_scraper_run(...):
    runner = ScraperRunner(db, triggered_by="admin-manual")
    result = await runner.run_by_id(scraper_id)  # Blocks until done
    return result
```

To (using BackgroundTasks):
```python
from fastapi import BackgroundTasks

@router.post("/run/{scraper_id}")
async def trigger_scraper_run(
    scraper_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Run scraper in background
    def run_scraper_bg():
        async def _run():
            runner = ScraperRunner(db, triggered_by="admin-manual")
            await runner.run_by_id(scraper_id)
        asyncio.create_task(_run())

    background_tasks.add_task(run_scraper_bg)
    return {"status": "started", "scraper_id": scraper_id}
```

### Phase 4: Initialize Data (30 min)

1. **If database is empty, run seed script**
   ```bash
   cd backend
   python seed_test_data.py
   ```

2. **Run a scraper via command line first** (to verify it works)
   ```bash
   cd backend
   python -c "
import asyncio
from services.scraper_runner import ScraperRunner
from database import SessionLocal

async def run():
    db = SessionLocal()
    runner = ScraperRunner(db, triggered_by='manual')
    result = await runner.run_by_id('wholesomeco')
    print(result)
    db.close()

asyncio.run(run())
"
   ```

3. **Verify data appears**
   - Check admin dashboard for scraper health
   - Check web app for products

## Critical Files to Modify

| File | Purpose | What to Change |
|------|---------|---------------|
| [backend/routers/admin_scrapers.py:180-194](backend/routers/admin_scrapers.py) | **CRITICAL FIX** | Change blocking scraper run to BackgroundTasks |
| [frontend/app/(admin)/admin/scrapers/page.tsx:61-75](frontend/app/(admin)/admin/scrapers/page.tsx) | Update UI | Handle "started" status instead of waiting for completion |

## Critical Files to Check

| File | Purpose | What to Check |
|------|---------|---------------|
| [backend/.env](backend/.env.example) | Environment config | DATABASE_URL, SECRET_KEY |
| [frontend/.env.local](frontend/.env.example) | Frontend config | NEXT_PUBLIC_API_URL |
| [backend/main.py:66-72](backend/main.py) | Scheduler startup | Check for errors on startup |
| [backend/services/scheduler.py](backend/services/scheduler.py) | Scheduler config | Database job store setup |
| [backend/database.py](backend/database.py) | DB connection | Connection string |

## Success Criteria

- [x] Backend health endpoint returns 200
- [x] `/api/admin/scrapers/health` returns 5-6 scrapers
- [x] Scheduler status shows `is_running: true` and `job_count > 0`
- [x] Database has at least 1 master product
- [x] Web app search returns results
- [x] Admin dashboard shows scraper health cards

## Next Steps After This Plan

Once data is flowing:
1. Run all scrapers manually once to populate database
2. Verify scheduler is running automatically
3. Test product search and comparison features
4. Continue with Phase 2 (Workflow 05) if not already complete

---

## Summary

**The core issue**: When you increased the scrapers to pull more products, they started taking too long to complete. The admin dashboard triggers scrapers via HTTP, which times out after ~30-120 seconds. That's why command-line runs still work (no timeout), but admin dashboard runs fail.

**The fix (IMPLEMENTED)**: Converted the `/api/admin/scrapers/run/{id}` endpoint to use `asyncio.create_task()` for background execution:
1. Returns immediately with `{"status": "started"}`
2. Runs the scraper asynchronously in the background with its own `SessionLocal()` database session
3. `ScraperRun` entry committed (not flushed) so polling sessions can see the "running" status
4. Frontend polls `/api/admin/scrapers/runs?scraper_id=X&limit=1` every 5 seconds until completion
5. Disabled scrapers are rejected with HTTP 400

**Files modified**:
1. `backend/routers/admin_scrapers.py` - Added `_run_scraper_in_background()` helper and `asyncio.create_task()` dispatch
2. `backend/services/scraper_runner.py` - Changed `flush()` to `commit()` + `refresh()` for ScraperRun visibility
3. `frontend/app/(admin)/admin/scrapers/page.tsx` - Added polling-based run status with cleanup on unmount
