# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Task Management

When starting a large task (exit plan mode with accepted plan):
1. **Create**: `mkdir -p dev/active/[task-name]/` with `-plan.md`, `-context.md`, `-tasks.md`
2. **Continue**: Check `/dev/active/` first; read all three files before proceeding

Use **MCP Serena** for code exploration — search over guessing file paths. If Serena errors, retry with different parameters.

**MCP Servers**: Context7 (framework docs), Firecrawl (web scraping), Figma (design files), Supabase (DB direct access), Serena (codebase search) — see `docs/guides/MCP_SETUP_GUIDE.md`.

## Project Overview

Utah Cannabis Aggregator — price comparison for Utah Medical Cannabis patients. Monorepo: Next.js frontend + FastAPI backend.

**Status**: MVP complete (all 10 workflows, Jan 2026).
**Compliance**: Every page must display a disclaimer that this is informational only and does not sell controlled substances.

## Environment: Windows 10 Pro

- Use `taskkill` not `kill`; `lsof` doesn't exist
- Reserved filenames (`CON`, `NUL`, `PRN`, `AUX`, `COM1-9`, `LPT1-9`) cause git failures — verify before staging
- Python 3.13+: use `asyncio.WindowsSelectorEventLoopPolicy()` for subprocess-heavy code
- Forward slashes in code; backslashes in batch scripts

## Stack

| Layer | Tech |
|-------|------|
| Frontend | TypeScript, Next.js 14 (App Router), React, Tailwind CSS — port 4002 |
| Backend | Python 3.13, FastAPI, SQLAlchemy ORM — port 8000 |
| Database | Supabase (PostgreSQL managed) |
| Auth | Supabase Auth (frontend) + JWT (backend) |
| Scrapers | Playwright, BeautifulSoup4, APScheduler |
| Testing | pytest (backend), Jest + React Testing Library (frontend) |

**Critical env vars**: `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env` — missing these is the #1 auth failure cause.

## Architecture

### Data Flow
1. **Scrapers** → ConfidenceScorer (fuzzy match) → Variant creation → Price record (with `product_url`) → API → Frontend
2. **Reviews**: User form → Backend validation → DB → Display
3. **Search**: Frontend → `/api/products/search` → rapidfuzz → Filtered results

### Product Parent/Variant Hierarchy ⚠️

**Critical rules** — violations cause data corruption:
- **Parent** (`is_master=True`): canonical product, no weight/price. Reviews + watchlist attach here.
- **Variant** (`is_master=False`): specific weight. **Prices ALWAYS attach to variants, NEVER parents.**
- `master_product_id` links variants to parent. API auto-resolves variant→parent for reviews/watchlist.

### ConfidenceScorer Thresholds

| Score | Action |
|-------|--------|
| >90% | Auto-merge: create/update price + variant |
| 60–90% | Create `ScraperFlag` for admin review; `ScrapedProduct.url` saved to `flag.original_url` |
| <60% | Create new parent product automatically |

On flag resolution: `flag.original_url` flows through `ScraperFlagProcessor` → `Price.product_url`.

### Scraper Self-Registration Pattern

Create class in `backend/services/scrapers/`, decorate, import in `main.py`:

```python
from services.scrapers.base_scraper import BaseScraper, ScrapedProduct, ScrapedPromotion
from services.scrapers.registry import register_scraper

@register_scraper(
    id="newdispensary",
    name="New Dispensary",
    dispensary_name="New Dispensary",
    dispensary_location="City, UT",
    schedule_minutes=120,
    description="Scraper for New Dispensary"
)
class NewDispennaryScraper(BaseScraper):
    async def scrape_products(self) -> List[ScrapedProduct]: ...
    async def scrape_promotions(self) -> List[ScrapedPromotion]: ...
```

```python
# main.py — import triggers self-registration
from services.scrapers.new_dispensary_scraper import NewDispennaryScraper  # noqa: F401
```

**Scraper gotchas**:
- Use `.is_(None)` / `.is_(True)` / `.is_(False)` in SQLAlchemy filters — never `== None`
- Guard against `None` brand names before `.ilike()` calls
- Always populate `weight` AND `url` fields on `ScrapedProduct`
- Never rollback inside the product processing loop — use `continue`
- Admin-triggered runs: fire-and-forget via `asyncio.create_task()`, returns `{"status":"started"}`, frontend polls every 5s
- Multi-location dispensaries: each physical location needs a **unique `dispensary_name`** — `_get_or_create_dispensary()` matches by name only, so two scrapers sharing the same `dispensary_name` write to the same DB record and mix pricing across locations
- Guard `thc_percentage` against values >100: some platforms (Dutchie) mislabel mg totals as `unit="PERCENTAGE"`. Use `if is_pct and v <= 100` before setting `thc_pct`. Note: `scorer.py` uses `scraped.thc_percentage or parent.thc_percentage` — if a corrupted parent value exists, None from the scraper will still inherit the bad value until the parent is manually corrected.
- See `docs/guides/ADDING_NEW_SCRAPERS.md` for the LLM-assisted discovery workflow (manually verify CSS selectors!)

### Authentication: Dual-System

- **Frontend**: Supabase Auth (magic link + Google OAuth) via `lib/AuthContext.tsx`
- **Backend**: JWT via `services/auth_service.py` + `get_current_user()` dependency
- **Bridge**: Axios interceptor in `lib/api.ts` attaches tokens automatically

**Supabase Auth Rules** (learned from a session-destruction bug — follow carefully):

1. **Never `signOut()` in 401 interceptors** — emit `authEvents.emitAuthFailure()` instead. OAuth/magic link has a window where 401s fire before the token is ready.
2. **`onAuthStateChange` is the single source of truth** — don't call `getSession()` alongside it; race conditions overwrite valid state. In Supabase v2, it fires `INITIAL_SESSION` immediately on subscribe.
3. **One `AuthContext` only** — all components use `useAuth()`, never their own listeners.
4. **Check `loading` before auth-gated UI** — `if (loading) return <Skeleton />`
5. **Callback page**: await `useAuth()` to report a user — `detectSessionInUrl` handles URL tokens automatically.
6. **Configure client explicitly**: `persistSession: true, autoRefreshToken: true, detectSessionInUrl: true`
7. **Use context `signOut()`** — never `supabase.auth.signOut()` directly (leaves context stale).

## Development Commands

### Quick Start (Windows Scripts)

```batch
scripts\install-deps.bat    # Install Python + Node deps
scripts\start-dev.bat       # Start backend + frontend
scripts\run-tests.bat       # Run all tests
```

### Backend

```bash
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

python -m uvicorn main:app --reload   # Dev server (port 8000)
pytest                                # All tests
pytest -v -s tests/test_matcher.py   # Specific test

alembic upgrade head                          # Apply migrations
alembic revision --autogenerate -m "desc"     # New migration
python seed_test_data.py                      # Seed DB
```

### Frontend

```bash
cd frontend
npm install
npm run dev          # Dev server (port 4002)
npm run type-check   # TypeScript errors
npm run lint
npm run build
```

### Docker

```bash
docker-compose up --build   # Start all services
docker-compose up -d        # Background
docker-compose down         # Stop
docker-compose down -v      # Stop + wipe DB volume

# After first start:
docker-compose exec backend alembic upgrade head
docker-compose exec backend python seed_test_data.py
```

**Docker DB issue**: Use `"postgres"` not `"localhost"` in `DATABASE_URL`.

### Environment Variables

**Backend** (`backend/.env`): `DATABASE_URL`, `SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SENDGRID_API_KEY` (optional)

**Frontend** (`frontend/.env.local`): `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`

**Local URLs**: Frontend http://localhost:4002 | API http://localhost:8000 | Swagger http://localhost:8000/docs

## Code Style

### Backend (Python)
- Type hints on all parameters/returns; docstrings on all classes and functions
- `HTTPException` for API errors; `async def` for I/O operations
- Models in `models.py` (inherit `Base`); Pydantic schemas in `schemas/`

### Frontend (TypeScript/React)
- Functional components with explicit prop interfaces; no class components
- Tailwind only — no custom CSS unless necessary
- `lib/api.ts` for all API calls — never raw axios
- `useAuth()` from `lib/AuthContext.tsx` for auth state — never independent Supabase calls

```tsx
import { useAuth } from '@/lib/AuthContext'

export function MyComponent() {
  const { user, loading, signOut } = useAuth()
  if (loading) return <Skeleton />
  if (!user) return <LoginLink />
  return <div>Welcome, {user.email}</div>
}
```

### Git Commits
- Conventional prefix: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- Stage specific files — avoid `git add -A` (can capture `.env`, secrets)
- **No interactive commit helper scripts** — they fail in this Windows environment

## File Organization

```
backend/
  main.py              → FastAPI app, router registration, scheduler startup
  models.py            → All 11 SQLAlchemy models (UUID PKs, cascade deletes)
  database.py          → Engine, session factory, get_db()
  config.py            → Settings class (env vars)
  routers/             → admin_scrapers, admin_flags, auth, users, products,
                         dispensaries, search, reviews, watchlist, notifications, scrapers
  services/
    scrapers/          → BaseScraper, registry, individual scraper implementations
    scraper_runner.py  → Executes scrapers, saves to DB
    scheduler.py       → APScheduler + separate alert scheduler
    normalization/     → scorer.py, weight_parser.py, flag_processor.py, matcher.py (legacy)
    alerts/            → stock_detector.py, price_detector.py
    notifications/     → email_service.py (SendGrid)
    auth_service.py    → JWT generation/validation
  tests/               → pytest files

frontend/
  app/
    (admin)/admin/     → dashboard, scrapers/, quality/, cleanup/
    auth/              → login/, callback/
    products/          → search/, [id]/
    dispensaries/      → [id]/
    profile/           → notifications/
    watchlist/
    layout.tsx         → Root layout + Providers
    globals.css        → Tailwind + compliance banner styles
  lib/
    api.ts             → Axios client + JWT interceptor + all endpoint definitions
    AuthContext.tsx    → Global auth context + useAuth() hook
    supabase.ts        → Supabase client config
  components/          → AgeGate, FilterPanel, SearchBar, ReviewForm,
                         WatchlistButton, PriceComparisonTable, Toast, ...
  tailwind.config.ts   → Custom cannabis color palette
```

## Debugging

### Approach
1. **Check `.env` first** — missing `SUPABASE_SERVICE_ROLE_KEY` is the #1 auth failure
2. **Test connectivity**: `curl http://localhost:8000/health`
3. **Read the exact error** before diagnosing root cause
4. **Focus on referenced files** — don't broadly scan the codebase

### Common Issues

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| 401 on API requests | Expired JWT | Interceptor auto-refreshes — check network tab |
| Scraper not running | Not registered | Check import in `main.py` + `@register_scraper` decorator |
| Products not matching | Low similarity | Check ConfidenceScorer thresholds (>90 / 60–90 / <60) |
| Scheduler not running | Bad DATABASE_URL | Check `settings.database_url` in scheduler config |
| Age gate loop | localStorage missing | Check `ageVerified` key in browser localStorage |
| SendGrid failing | Missing API key | Add `SENDGRID_API_KEY` to `backend/.env` |

### Useful Debug Commands

```bash
# Verify DB connection
cd backend && python -c "from database import SessionLocal; from models import User; db = SessionLocal(); print(db.query(User).count())"

# Check prices incorrectly on parent products (should be 0)
python -c "from database import SessionLocal; from models import Product, Price; db = SessionLocal(); print(db.query(Price).join(Product).filter(Product.is_master.is_(True)).count())"

# Test a specific scraper manually
python -c "
import asyncio
from services.scraper_runner import ScraperRunner
from database import SessionLocal
async def test():
    db = SessionLocal()
    result = await ScraperRunner(db, triggered_by='manual').run_by_id('wholesomeco')
    print(result); db.close()
asyncio.run(test())"

# Clear Next.js cache (frontend)
rmdir /s /q frontend\.next
```

## Key References

| File | Purpose |
|------|---------|
| `backend/models.py` | Authoritative schema (11 tables) |
| `docs/ARCHITECTURE.md` | Detailed architecture notes |
| `docs/guides/ADDING_NEW_SCRAPERS.md` | Scraper guide + LLM-assisted discovery workflow |
| `docs/guides/MCP_SETUP_GUIDE.md` | MCP server credential setup |
| `docs/workflows/` | 10 MVP implementation workflows (all complete ✅) |

### API Endpoints

| Router | Prefix | Key Operations |
|--------|--------|----------------|
| `admin_scrapers.py` | `/api/admin/scrapers` | run (async/bg), status, history, pause/resume |
| `admin_flags.py` | `/api/admin/flags` | approve, reject, dismiss, bulk-action |
| `auth.py` | `/api/auth` | register, login, refresh, verify |
| `products.py` | `/api/products` | list, get, prices (with `product_url`), history |
| `search.py` | `/api/products/search` | fuzzy search with filters |
| `reviews.py` | `/api/reviews` | CRUD, upvote, by-product |
| `watchlist.py` | `/api/watchlist` | add, remove, list, check |
| `dispensaries.py` | `/api/dispensaries` | list, get, inventory |
| `notifications.py` | `/api/notifications` | get/update preferences |
| `scrapers.py` | `/api/scrapers` | public scraper info |
