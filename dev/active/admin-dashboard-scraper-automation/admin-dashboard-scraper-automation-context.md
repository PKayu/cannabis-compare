# Context

## Key Files
- `backend/models.py` - All SQLAlchemy models, add ScraperRun here
- `backend/services/scraper_runner.py` - ScraperRunner.run_by_id() is the central execution point
- `backend/services/scheduler.py` - APScheduler with ScraperScheduler class, currently MemoryJobStore
- `backend/main.py` - Scheduler startup commented out at lines 52-66
- `backend/routers/admin_flags.py` - Existing admin routes
- `backend/routers/scrapers.py` - Existing scraper API routes
- `frontend/app/(admin)/admin/cleanup/page.tsx` - Existing cleanup queue UI
- `frontend/lib/api.ts` - Frontend API client

## Decisions
- Using SQLAlchemyJobStore for scheduler persistence
- ScraperRun model logs every execution (scheduled + manual)
- Admin dashboard uses tabbed layout with 4 sections
- Hybrid scheduling: daily at 6am + interval every 2 hours

## Last Updated
2026-01-28
