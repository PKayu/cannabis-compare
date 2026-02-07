# Workflow 11: Automated Daily Scraping & Enhanced Admin Dashboard

## Status: TESTING COMPLETE ✅ (2026-01-29)

## Context
- PRD Section 4.1: Data normalization and scraper scheduling
- Builds on Workflow 03 (Scraper Foundation) and Workflow 04 (Admin Cleanup Queue)

## Overview
Enable production-ready automated scraping with persistent scheduling, comprehensive run logging, and a full admin dashboard for monitoring scrapers, managing deduplication, and tracking data quality.

---

## Phase 1: Scraper Run Logging (COMPLETED)

### Step 1.1: ScraperRun Model
- **File**: `backend/models.py`
- Added `ScraperRun` model with fields: scraper_id, scraper_name, dispensary_id, started_at, completed_at, duration_seconds, status, products_found, products_processed, flags_created, error_message, error_type, retry_count, triggered_by
- Includes `complete()` helper method to finalize run with results

### Step 1.2: ScraperRunner Integration
- **File**: `backend/services/scraper_runner.py`
- `run_by_id()` now creates a `ScraperRun` record at start of every execution
- The `ScraperRun` entry with status `"running"` is committed immediately (not just flushed) so that other database sessions (e.g., admin dashboard polling) can see it
- Updates run with results on success or error details on failure
- Returns `run_id` in response dict
- Constructor accepts `triggered_by` parameter (default: "manual")

### Verification
```bash
# Trigger a scraper run (returns immediately with {"status": "started"})
curl -X POST http://localhost:8000/api/admin/scrapers/run/wholesomeco

# Poll for completion (check latest run status)
curl "http://localhost:8000/api/admin/scrapers/runs?scraper_id=wholesomeco&limit=1"
# Wait until status changes from "running" to "success", "error", or "warning"

# Query: SELECT * FROM scraper_runs ORDER BY started_at DESC LIMIT 5;
```

---

## Phase 2: Persistent Scheduler (COMPLETED)

### Step 2.1: SQLAlchemyJobStore
- **File**: `backend/services/scheduler.py`
- `ScraperScheduler.__init__()` accepts optional `database_url` parameter
- When provided, uses `SQLAlchemyJobStore` for persistent job storage
- Falls back to `MemoryJobStore` when no URL provided
- `_run_scraper()` now uses `ScraperRunner` with `triggered_by="scheduler"`

### Step 2.2: Enable on Startup
- **File**: `backend/main.py`
- Scheduler starts in `lifespan()` with database URL from settings
- All registered scrapers auto-scheduled via `register_all_scrapers()`
- Graceful shutdown with `scheduler.stop(wait=True)`

### Verification
```bash
# Start the backend and check logs for:
# "Scraper scheduler started with N jobs"
# Restart and verify jobs persist (not re-registered)
```

---

## Phase 3: Admin API Endpoints (COMPLETED)

### Step 3.1: Scraper Admin Router
- **File**: `backend/routers/admin_scrapers.py` (NEW)
- `GET /api/admin/scrapers/runs` - Paginated run history with scraper_id/status filters
- `GET /api/admin/scrapers/health` - 7-day health metrics per scraper
- `GET /api/admin/scrapers/scheduler/status` - Scheduler state and job list
- `POST /api/admin/scrapers/run/{scraper_id}` - **Async** manual trigger (returns `{"status": "started"}` immediately; scraper runs in background via `asyncio.create_task()` with its own `SessionLocal()` database session; disabled scrapers return HTTP 400; poll `/runs` to check progress)
- `POST /api/admin/scrapers/scheduler/pause/{scraper_id}` - Pause scraper
- `POST /api/admin/scrapers/scheduler/resume/{scraper_id}` - Resume scraper
- `GET /api/admin/scrapers/quality/metrics` - Data completeness metrics
- `GET /api/admin/scrapers/dispensaries/freshness` - Data freshness per dispensary

### Verification
```bash
curl http://localhost:8000/api/admin/scrapers/health
curl http://localhost:8000/api/admin/scrapers/runs?limit=10
curl http://localhost:8000/api/admin/scrapers/quality/metrics
curl http://localhost:8000/api/admin/scrapers/dispensaries/freshness
curl http://localhost:8000/api/admin/scrapers/scheduler/status
```

---

## Phase 4: Enhanced Frontend Dashboard (COMPLETED)

### Step 4.1: Admin Layout
- **File**: `frontend/app/(admin)/admin/layout.tsx` (NEW)
- Tab navigation: Dashboard, Cleanup Queue, Scrapers, Data Quality
- Active tab highlighting using `usePathname()`

### Step 4.2: Dashboard Overview
- **File**: `frontend/app/(admin)/admin/page.tsx` (NEW)
- Stats grid: pending flags, healthy scrapers, master products, outliers
- Quick action buttons linking to sub-pages
- Recent scraper activity table (last 10 runs)

### Step 4.3: Scraper Monitoring
- **File**: `frontend/app/(admin)/admin/scrapers/page.tsx` (NEW)
- Health cards per scraper with success rate badges (green/yellow/red)
- "Run Now" button per scraper -- triggers async background run (POST returns `{"status": "started"}` immediately)
- Frontend polls `/api/admin/scrapers/runs?scraper_id=X&limit=1` every 5 seconds after trigger; stops polling and refreshes data when run status changes from `"running"` to a terminal state; polling interval ref is cleaned up on unmount
- "View Runs" filter per scraper
- Full run history table with status, duration, product counts, errors

### Step 4.4: Data Quality
- **File**: `frontend/app/(admin)/admin/quality/page.tsx` (NEW)
- Completeness cards: missing THC%, CBD%, brand (color-coded by severity)
- Category distribution horizontal bar chart
- Dispensary freshness table with status badges
- Price outlier table with severity indicators

### Step 4.5: API Client Update
- **File**: `frontend/lib/api.ts`
- Added `api.admin.scrapers.*`, `api.admin.quality.*`, `api.admin.flags.*` methods

### Step 4.6: Cleanup Queue Update
- **File**: `frontend/app/(admin)/admin/cleanup/page.tsx`
- Removed standalone layout wrapper (now uses shared admin layout)

### Verification
```bash
cd frontend && npm run dev
# Navigate to http://localhost:3000/admin
# Verify all 4 tabs render correctly
# Trigger a manual scraper run from the Scrapers tab
# Check Data Quality tab for metrics
```

---

## Phase 5: Future Enhancements (NOT STARTED)

- [ ] Bulk operations page (bulk approve flags, CSV export)
- [ ] Scraper config management UI (enable/disable, change schedules)
- [ ] Email/Slack alerts for failed scrapers or stale data
- [ ] Historical analytics (price trends, product count charts)
- [ ] Real-time WebSocket updates during manual scraper runs

---

## Success Criteria

- [x] ScraperRun model logs every scraper execution
- [x] Scheduler starts automatically on backend startup
- [x] Jobs persist across application restarts (SQLAlchemyJobStore)
- [x] Admin dashboard overview shows system health at a glance
- [x] Scraper monitoring page displays health metrics and run history
- [x] Manual trigger button runs scraper and creates log entry
- [x] Data quality page shows completeness metrics and freshness
- [x] Tab navigation works across all admin pages
- [x] Database migration run to create scraper_runs table (d61ee6846ddf)
- [x] End-to-end test: scheduler triggers run, logged in DB, visible in dashboard
- [x] Scheduler serialization issue fixed (standalone run_scheduled_scraper function)

## Files Modified/Created

| File | Action |
|------|--------|
| `backend/models.py` | Modified - added ScraperRun model |
| `backend/services/scraper_runner.py` | Modified - added run logging |
| `backend/services/scheduler.py` | Modified - SQLAlchemyJobStore, ScraperRunner integration |
| `backend/main.py` | Modified - enabled scheduler, registered admin_scrapers router |
| `backend/routers/admin_scrapers.py` | Created - all admin scraper endpoints |
| `frontend/app/(admin)/admin/layout.tsx` | Created - admin tab layout |
| `frontend/app/(admin)/admin/page.tsx` | Created - dashboard overview |
| `frontend/app/(admin)/admin/scrapers/page.tsx` | Created - scraper monitoring |
| `frontend/app/(admin)/admin/quality/page.tsx` | Created - data quality |
| `frontend/app/(admin)/admin/cleanup/page.tsx` | Modified - removed standalone layout |
| `frontend/lib/api.ts` | Modified - added admin API methods |
