# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

### Starting Large Tasks

When exiting plan mode with an accepted plan:
1. **Create Task Directory**: `mkdir -p dev/active/[task-name]/`
2. **Create Documents**:
   - `[task-name]-plan.md` - The accepted plan
   - `[task-name]-context.md` - Key files, decisions
   - `[task-name]-tasks.md` - Checklist of work
3. **Update Regularly**: Mark tasks complete immediately

### Continuing Tasks

- Check `/dev/active/` for existing tasks
- Read all three files before proceeding
- Update "Last Updated" timestamps

### Code Exploration & Context

- **Leverage MCP Serena**: When browsing or trying to understand code, explicitly use MCP Serena tools to search and gather context
- **Search Strategy**: Prioritize searching over guessing file paths. If Serena errors occur, retry with different parameters

## Project Overview

Utah Cannabis Aggregator is a full-stack web application for Utah Medical Cannabis patients to compare prices across dispensaries and access community-driven reviews. It's a monorepo with separate frontend (Next.js) and backend (FastAPI) applications.

**Current Status**: All 10 MVP Workflows Complete ✅ (January 2026)
- Phase 1: Foundation ✅
- Phase 2: Frontend Portal ✅
- Phase 3: Community Features ✅

**Compliance**: All pages must display a disclaimer that this is informational only and does not sell controlled substances.

## Architecture & Design Decisions

### High-Level System Architecture

```
Browser (React/Next.js) ←→ FastAPI Backend ←→ PostgreSQL (Docker/Supabase)
  - Port 4001            - Port 8000         - Docker container or
  - Next.js App Router   - Internal only     - Supabase managed
  - Tailwind CSS         - JWT Auth          - SQLAlchemy ORM
```

### Data Flow Pattern

The app follows three main data flows:

1. **Price Aggregation**: Web scrapers (capture product URL) → Data normalization (fuzzy match + weight parsing) → Variant creation → Price storage on variants (with product_url) → API (grouped by weight with URLs) → Frontend (direct product links)
2. **Reviews**: User form → Backend validation → Database → API queries → Display
3. **Search**: Frontend input → `/api/products/search` → Database → Results with filters

### Database Schema Key Points

Eleven interconnected models with these critical relationships:

- **Product** ↔ **Dispensary** (M:M junction via **Price** table)
- **Product** → **Product** (self-referential parent/variant hierarchy, see below)
- **Product** → **Review** (1:M, user-generated content with dual-track intention tags)
- **Product** → **Brand** (M:1, cultivators)
- **User** → **Review** (1:M, tracks who posted reviews)
- **User** → **Watchlist** (1:M, products user is tracking)
- **User** → **PriceAlert** (1:M, price drop thresholds)
- **User** → **NotificationPreference** (1:1, email frequency settings)
- **Dispensary** → **Promotion** (1:M, weekly deals)
- **ScraperFlag** → Data quality issues (orphaned products, outliers); includes `original_weight`, `original_price`, `original_category`, and `original_url` fields for variant context and source verification
- **ScraperRun** → Execution history and monitoring

All models use UUID primary keys. Foreign key constraints cascade on delete.

#### Product Parent/Variant Hierarchy

Products follow a parent/variant model for representing the same strain at different weights:

- **Parent products** (`is_master=True`): Represent the canonical strain/product. Have no `weight` or `weight_grams`. Reviews and watchlist entries attach to parent products.
- **Variant products** (`is_master=False`): Represent a specific weight of a parent product. Have `master_product_id` pointing to the parent, plus `weight` (display string like "3.5g") and `weight_grams` (normalized float like 3.5). Prices always attach to variant products.

Self-referential relationship fields on the Product model:
- `Product.variants` - List of variant products (from parent)
- `Product.master_product` - Parent product reference (from variant)

**Critical rule**: Prices are always stored on variant products, never on parents. Reviews are always stored on parent products, never on variants. The API layer handles resolution automatically (e.g., posting a review on a variant ID resolves to the parent).

#### Product URLs on Price Records

The `Price` model includes a `product_url` field for direct links to product pages at dispensaries:

- **Storage**: URLs are stored on `Price` records (product-dispensary junction) since the same product has different URLs at different dispensaries
- **Capture**: Scrapers extract product page URLs during scraping and pass them to `ScraperRunner._update_price()`
- **Frontend Usage**:
  - Product detail pages use `product_url` for "Buy Now" buttons (direct to product page instead of search)
- **Fallback**: If `product_url` is null, frontend falls back to dispensary homepage or search patterns
- **Format**: Should be absolute URLs (e.g., `https://wholesomeco.com/products/blue-dream-3-5g`)

#### URL Preservation for Flagged Products

When the `ConfidenceScorer` flags a product (60-90% confidence), no Price record is created, so the product URL would be lost. To prevent this, the URL is captured on the `ScraperFlag` itself:

- **Flow**: Scraper -> `ScrapedProduct.url` -> `ConfidenceScorer` -> `ScraperFlag.original_url` -> API response -> Frontend "View Source Product Page" link
- **On resolution**: When a flag is approved or rejected, `ScraperFlagProcessor` passes `flag.original_url` through to `update_or_create_price()`, ensuring the URL reaches the resulting Price record
- **Frontend**: The cleanup queue FlagCard component reads `flag.original_url` directly (no async fetching from Price records needed)
- **Key insight**: Previously URLs were lost for flagged items because the scraper pipeline skips Price creation for 60-90% matches. The `original_url` field on ScraperFlag bridges that gap

### Scraper Architecture (Self-Registration Pattern)

The scraper system uses a decorator-based self-registration pattern:

1. **ScraperRegistry** ([`services/scrapers/registry.py`](backend/services/scrapers/registry.py)) - Central registry storing scraper metadata
2. **BaseScraper** ([`services/scrapers/base_scraper.py`](backend/services/scrapers/base_scraper.py)) - Abstract base class all scrapers inherit from
3. **ScraperScheduler** ([`services/scheduler.py`](backend/services/scheduler.py)) - APScheduler integration with auto-registration
4. **ScraperRunner** ([`services/scraper_runner.py`](backend/services/scraper_runner.py)) - Executes scrapers and saves results to database

**Adding a new scraper:**

```python
from services.scrapers.base_scraper import BaseScraper
from services.scrapers.registry import register_scraper

@register_scraper(
    id="beehive",
    name="Beehive Farmacy",
    dispensary_name="Beehive Farmacy",
    dispensary_location="Salt Lake City, UT",
    schedule_minutes=120,
    description="Direct scraping from Beehive Farmacy website"
)
class BeehiveScraper(BaseScraper):
    async def scrape_products(self) -> List[ScrapedProduct]:
        # Implementation here
        pass

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        # Implementation here
        pass
```

Then import in `main.py` to trigger registration:
```python
from services.scrapers.beehive_scraper import BeehiveScraper  # noqa: F401
```

The scheduler automatically discovers and schedules all registered scrapers at startup.

### Fuzzy Matching & Product Normalization

The scraper pipeline uses `ConfidenceScorer` (from `services/normalization/scorer.py`) for intelligent product matching. This replaced the earlier exact-match `ProductMatcher` approach.

**How it works:**
1. When a scraper run begins, all master (parent) products are pre-loaded into a candidate cache for the duration of the run
2. Each scraped product is scored against cached candidates using fuzzy string matching (rapidfuzz)
3. Based on the confidence score, one of three actions is taken:
   - **>90% match**: Auto-merge -- the scraped product is linked to the existing product and a price/variant is created or updated
   - **60-90% match**: A `ScraperFlag` is created for admin review in the cleanup queue, with the match candidate, confidence score, and `original_url` (from `ScrapedProduct.url`) attached for source verification
   - **<60% match**: A new parent product is created automatically
4. Weight parsing (`services/normalization/weight_parser.py`) extracts weight from product names (e.g., "Blue Dream - 3.5g" produces `weight="3.5g"`, `weight_grams=3.5`) and creates appropriate variant products
5. The scorer uses `db.flush()` instead of `db.commit()` for transaction control, allowing the caller (`ScraperRunner`) to commit the entire batch atomically

**Key files:**
- `services/normalization/scorer.py` - `ConfidenceScorer` with `find_or_create_variant()` for variant-aware product creation
- `services/normalization/weight_parser.py` - Parses weight strings ("3.5g", "1oz", "1/8 oz") to normalized labels and gram values
- `services/normalization/matcher.py` - Legacy `ProductMatcher` (retained for reference)
- `services/normalization/flag_processor.py` - Variant-aware flag approve/reject logic; passes `original_url` through to Price records on resolution
- `services/scraper_runner.py` - Orchestrates scraper execution, imports `ConfidenceScorer`

### Alert & Notification System

The alert system runs on a separate scheduler (see `services/scheduler.py:start_alert_scheduler()`):

- **StockDetector** ([`services/alerts/stock_detector.py`](backend/services/alerts/stock_detector.py)) - Detects when out-of-stock products become available (24-hour deduplication)
- **PriceDetector** ([`services/alerts/price_detector.py`](backend/services/alerts/price_detector.py)) - Detects price drops exceeding user thresholds
- **EmailNotificationService** ([`services/notifications/email_service.py`](backend/services/notifications/email_service.py)) - SendGrid integration with HTML templates

Users configure notification preferences via `/profile/notifications`:
- Email frequency: immediate, daily, weekly
- Alert types: stock alerts, price drops (individually toggleable)

### Admin Dashboard

Located at `/admin` (frontend) with corresponding backend API routers:

- **Admin Scrapers** ([`routers/admin_scrapers.py`](backend/routers/admin_scrapers.py)) - View scraper status, trigger manual runs (async/background), view execution history
- **Admin Flags** ([`routers/admin_flags.py`](backend/routers/admin_flags.py)) - Review and resolve data quality issues; returns `original_url` on flag responses for "View Source" links to dispensary product pages
- **Admin Quality** ([`services/quality/outlier_detection.py`](backend/services/quality/outlier_detection.py)) - Statistical analysis to identify price outliers

**Async Scraper Execution:** The `POST /api/admin/scrapers/run/{scraper_id}` endpoint uses fire-and-forget background execution via `asyncio.create_task()`. It returns immediately with `{"status": "started"}` instead of blocking until the scraper completes. The scraper runs in the background with its own database session (created via `SessionLocal()`) to avoid the request-scoped session being closed. The `ScraperRun` entry is committed immediately with status `"running"` so other sessions (e.g., frontend polling) can see it. The frontend polls `/api/admin/scrapers/runs?scraper_id=X&limit=1` every 5 seconds until the run status changes from `"running"` to a terminal state (`"success"`, `"error"`, or `"warning"`). Disabled scrapers are rejected with HTTP 400.

Frontend uses Next.js App Router with route group `(admin)` for admin-specific pages:
- [`/admin/page.tsx`](frontend/app/(admin)/admin/page.tsx) - Main dashboard
- [`/admin/scrapers/page.tsx`](frontend/app/(admin)/admin/scrapers/page.tsx) - Scraper management with polling-based run status
- [`/admin/quality/page.tsx`](frontend/app/(admin)/admin/quality/page.tsx) - Quality metrics
- [`/admin/cleanup/page.tsx`](frontend/app/(admin)/admin/cleanup/page.tsx) - Flagged items with "View Source Product Page" links using `flag.original_url` directly

### Authentication Architecture (Dual-System)

The app uses a dual authentication system:

1. **Frontend (Supabase Auth)** - User-facing authentication
   - Magic link email authentication
   - Google OAuth integration
   - Managed via `lib/SupabaseClient.ts` and `lib/AuthContext.tsx`
   - Age gate component (`components/AgeGate.tsx`) enforces 21+ requirement

2. **Backend (JWT Tokens)** - API authentication
   - Supabase validates frontend tokens via `services/supabase_client.py`
   - Backend generates its own JWT tokens for API access
   - Protected routes use `get_current_user()` dependency
   - Token validation in `routers/auth.py` and `services/auth_service.py`

**Why dual authentication?**
- Supabase handles user management and OAuth providers on frontend
- Backend JWT enables stateless API authentication without depending on Supabase on every request
- Frontend axios interceptor (`lib/api.ts`) automatically attaches tokens to requests

### Supabase + Next.js Authentication Rules (CRITICAL)

These rules were learned from debugging a session-destruction bug. **Follow them in ALL projects using Supabase Auth with Next.js/React.**

#### Rule 1: NEVER call `signOut()` in API 401 interceptors

```typescript
// ❌ WRONG - Destroys valid sessions during establishment
apiClient.interceptors.response.use(null, async (error) => {
  if (error.response?.status === 401) {
    await supabase.auth.signOut()  // KILLS THE SESSION
  }
})

// ✅ CORRECT - Emit event, let components handle it
apiClient.interceptors.response.use(null, async (error) => {
  if (error.response?.status === 401) {
    authEvents.emitAuthFailure()  // Components decide what to do
  }
})
```

**Why:** After OAuth/magic link login, there's a brief window where the session exists but the token isn't ready for API requests. A 401 during this window doesn't mean the session is invalid - calling `signOut()` destroys a valid session that was just established.

#### Rule 2: Use `onAuthStateChange` as the SINGLE source of truth

```typescript
// ❌ WRONG - Race conditions between getSession() and onAuthStateChange
useEffect(() => {
  supabase.auth.getSession().then(...)  // Can overwrite valid state
  supabase.auth.onAuthStateChange(...)  // Fires separately
  setTimeout(...)                        // Adds more timing issues
}, [])

// ✅ CORRECT - Single source of truth
useEffect(() => {
  const { data: { subscription } } = supabase.auth.onAuthStateChange(
    (event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    }
  )
  return () => subscription.unsubscribe()
}, [])
```

**Why:** In Supabase v2, `onAuthStateChange` fires `INITIAL_SESSION` immediately on subscribe. No need for `getSession()`. Multiple async sources setting the same state creates race conditions where a stale null overwrites a valid session.

#### Rule 3: One AuthContext, zero independent auth state

```typescript
// ❌ WRONG - Component maintains its own auth state
function UserNav() {
  const [user, setUser] = useState(null)
  useEffect(() => {
    supabase.auth.getSession().then(...)
    supabase.auth.onAuthStateChange(...)  // Second listener!
  }, [])
}

// ✅ CORRECT - All components use the shared context
function UserNav() {
  const { user, loading, signOut } = useAuth()
}
```

**Why:** Multiple components checking auth independently creates timing inconsistencies. One component may show "logged in" while another shows "logged out."

#### Rule 4: Components MUST check `loading` before showing auth-dependent UI

```typescript
// ❌ WRONG - Shows "Login" during auth initialization
const { user } = useAuth()
return user ? <Profile /> : <LoginLink />

// ✅ CORRECT - Shows placeholder while loading
const { user, loading } = useAuth()
if (loading) return <Skeleton />
return user ? <Profile /> : <LoginLink />
```

#### Rule 5: Callback pages should use AuthContext, not direct Supabase calls

The callback page just waits for `useAuth()` to report a user, then redirects. The Supabase client automatically processes URL tokens via `detectSessionInUrl`. No need to check `window.location.hash` or call `getSession()` directly.

#### Rule 6: Always configure the Supabase client explicitly

```typescript
export const supabase = createClient(url, key, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
})
```

#### Rule 7: Use context `signOut()` everywhere, never call `supabase.auth.signOut()` directly

Direct calls bypass the context, leaving it in a stale state where it still thinks the user is logged in.

### API Organization

The app has 12 modular routers (all implemented):

- `routers/admin_scrapers.py` - Admin scraper management
- `routers/admin_flags.py` - Admin flag resolution and quality management
- `routers/auth.py` - Registration, login, JWT tokens
- `routers/users.py` - User profiles and public profiles
- `routers/products.py` - Product browsing, search, details, pricing history
- `routers/dispensaries.py` - Dispensary information and inventory
- `routers/search.py` - Product search with fuzzy matching
- `routers/reviews.py` - Review CRUD with intention tags
- `routers/watchlist.py` - Watchlist management
- `routers/notifications.py` - Notification preferences
- `routers/scrapers.py` - Public scraper information

Frontend uses a centralized Axios wrapper ([`lib/api.ts`](frontend/lib/api.ts)) with interceptors for auth tokens and error handling.

## Development Commands

### Quick Start (Windows Scripts)

The `scripts/` directory contains convenience scripts for common development tasks:

```batch
# Install all dependencies (Python + Node)
scripts\install-deps.bat

# Start both backend and frontend
scripts\start-dev.bat

# Start individual servers
scripts\start-backend.bat
scripts\start-frontend.bat

# Run all tests
scripts\run-tests.bat

# Fix Python 3.13 compatibility issues
scripts\fix-python313.bat
```

### Backend Setup & Running

```bash
# Initial setup (one time)
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with DATABASE_URL, SECRET_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY

# Development server (auto-reload on changes)
python -m uvicorn main:app --reload

# Run tests
pytest                          # Run all tests
pytest -v -s                    # Verbose with print statements
pytest tests/test_matcher.py    # Run specific test file

# Database migrations
alembic upgrade head            # Apply all migrations
alembic revision --autogenerate -m "description"  # Create new migration

# Seed test data
python seed_test_data.py        # Populate database with test products
```

### Frontend Setup & Running

```bash
# Initial setup (one time)
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with NEXT_PUBLIC_API_URL (usually http://localhost:8000)

# Development server (Next.js with fast refresh)
npm run dev

# Type checking (TypeScript)
npm run type-check

# Linting
npm run lint

# Build for production
npm run build

# Start production server
npm run start
```

### Database & Environment

**Backend `.env` required variables:**
- `DATABASE_URL` - PostgreSQL connection string (Supabase)
- `SECRET_KEY` - JWT signing key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `SENDGRID_API_KEY` - (Optional) For email notifications
- `alert_check_interval_hours` - Alert scheduler frequency (default: 1)

**Frontend `.env.local` required variables:**
- `NEXT_PUBLIC_API_URL` - Backend API URL (usually `http://localhost:8000`)
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key

### Verification

```bash
# Verify backend connectivity
curl http://localhost:8000/health  # Should return {"status": "healthy"}

# Access API docs (auto-generated)
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

## Docker Development (Recommended)

The project includes Docker configuration for easy development setup without installing Python, Node.js, or PostgreSQL locally.

### Quick Start with Docker

```bash
# Start all services (postgres, backend, frontend)
docker-compose up --build

# Services will be available at:
# - Frontend: http://localhost:4001
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Database: localhost:5433 (direct access if needed)
```

### Docker Scripts

```batch
# Start Docker environment
scripts\start-docker.bat

# Initialize database with migrations
scripts\docker-init-db.bat

# Seed test data
scripts\docker-seed-data.bat

# Stop all containers
scripts\docker-cleanup.bat
```

### Docker Commands

```bash
# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Restart specific service
docker-compose restart backend

# Run backend command in container
docker-compose exec backend alembic upgrade head
docker-compose exec backend pytest

# Stop all services
docker-compose down

# Stop and remove all data (including database)
docker-compose down -v

# Rebuild containers (after dependency changes)
docker-compose up --build

# Remove all Docker data (fresh start)
docker-compose down -v
docker system prune -a
```

### Database Initialization in Docker

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Seed test data
docker-compose exec backend python seed_test_data.py
```

### Docker Troubleshooting

**Issue: Containers can't connect to database**
- Ensure postgres container is healthy: `docker-compose ps`
- Check DATABASE_URL in backend/.env uses "postgres" not "localhost"
- Verify network: `docker network ls`

**Issue: Hot reload not working**
- Ensure volume mounts are correct in docker-compose.yml
- Check file permissions on Linux/Mac
- Restart container: `docker-compose restart backend`

**Issue: Port already in use**
- Change port mapping in docker-compose.yml (e.g., "4002:3000")
- Stop other services using the port

**Issue: Database lost after restart**
- Data persists in postgres_data volume
- Only lost if you run `docker-compose down -v`

## Code Style & Patterns

### Backend (Python)

- **Imports**: Follow PEP 8 grouping (stdlib, third-party, local)
- **Type Hints**: Always use them for function parameters and returns
- **Docstrings**: Use triple quotes for all functions and classes
- **Database Models**: Located in `models.py`, inherit from `Base`
- **Pydantic Schemas**: Create in `schemas/` directory for request/response validation
- **Error Handling**: Use FastAPI's `HTTPException` for API errors
- **Async**: Use `async def` for I/O operations, `await` for concurrency

Example pattern for new endpoints:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import ProductResponse

router = APIRouter(prefix="/api/products", tags=["products"])

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: Session = Depends(get_db)):
    """Fetch product details by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
```

### Frontend (TypeScript/React)

- **Components**: Use functional components with hooks, no class components
- **Props**: Define explicit interface/type for all component props
- **Files**: `.tsx` for components, `.ts` for utilities
- **Styling**: Use Tailwind utility classes, no custom CSS unless necessary
- **API Calls**: Use `lib/api.ts` wrapper, not raw axios
- **State Management**: Props/hooks for local state; use `useAuth()` hook from `lib/AuthContext.tsx` for authentication state
- **Authentication**: Always use the `useAuth()` hook instead of independent Supabase calls to ensure consistent auth state across components

Example component pattern:
```tsx
interface ProductProps {
  productId: string
  onSelect?: (id: string) => void
}

export function ProductCard({ productId, onSelect }: ProductProps) {
  const [product, setProduct] = React.useState(null)

  React.useEffect(() => {
    api.products.get(productId).then(r => setProduct(r.data))
  }, [productId])

  return (
    <div className="border rounded p-4">
      {product && <h2>{product.name}</h2>}
    </div>
  )
}
```

## Key Project Constraints

### Compliance & Legal

- Every page must display a compliance banner (see `frontend/app/globals.css` for styling)
- Site is informational only — no product transactions
- Target audience: Utah Medical Cannabis Cardholders 21+
- All data is for reference purposes

### Performance Targets

- Search response: <200ms (requires database indexing on `products.name`, `products.brand_id`)
- Page load: <2 seconds
- Mobile responsiveness: 80% of users access via mobile (Tailwind mobile-first built-in)

### Database Configuration

- PostgreSQL required (local or Supabase)
- SQLAlchemy ORM handles all queries — no raw SQL
- Migrations managed with Alembic (to be set up)
- Connection pooling enabled in `database.py`

## File Organization Reference

```
backend/
  main.py           → FastAPI app, CORS, router registration, lifespan with scheduler startup
  config.py         → Environment variables and settings (Settings class)
  database.py       → SQLAlchemy engine, session factory, get_db() dependency
  models.py         → All SQLAlchemy ORM models (11 tables: User, Product, Price, etc.)
  routers/          → Modular endpoint groups
    admin_scrapers.py   → Admin scraper management (run, status, history)
    admin_flags.py      → Admin flag resolution and quality management
    auth.py            → Registration, login, JWT token endpoints
    users.py           → User profile and public profile endpoints
    products.py        → Product details, pricing history, related products
    dispensaries.py    → Dispensary info, inventory, promotions
    search.py          → Product search with fuzzy matching (rapidfuzz)
    reviews.py         → Review CRUD with intention tags
    watchlist.py       → Watchlist management (add, remove, check)
    notifications.py   → Notification preferences endpoints
    scrapers.py        → Public scraper info endpoint
  services/
    scrapers/
      base_scraper.py      → Abstract BaseScraper class
      registry.py          → ScraperRegistry + @register_scraper decorator
      wholesome_co_scraper.py
      iheartjane_scraper.py
      playwright_scraper.py
    scraper_runner.py       → Executes scrapers and saves to DB
    scheduler.py            → APScheduler integration + alert scheduler
    normalization/
      matcher.py            → Legacy ProductMatcher (retained for reference)
      scorer.py             → ConfidenceScorer with variant-aware product creation
      flag_processor.py     → Variant-aware flag approve/reject processing
      weight_parser.py      → Parses weight strings to normalized labels and gram values
    quality/
      outlier_detection.py  → Statistical outlier detection (z-score)
    alerts/
      stock_detector.py     → Stock availability changes
      price_detector.py     → Price drop detection
    notifications/
      email_service.py      → SendGrid email templates
    auth_service.py         → JWT token generation/validation
    supabase_client.py      → Supabase admin client
  scripts/
    migrate_to_variants.py  → Three-phase data migration (create variants, deduplicate, parse weights)
  tests/                 → pytest test files
    test_matcher.py
    test_scraper.py
    test_weight_parser.py   → Weight parser unit tests
    test_variant_creation.py → Variant creation logic tests

frontend/
  app/
    (admin)/           → Route group for admin pages (shared layout)
      admin/
        page.tsx           → Admin dashboard
        scrapers/page.tsx  → Scraper management UI
        quality/page.tsx   → Quality metrics
        cleanup/page.tsx   → Flagged items queue
    auth/
      login/page.tsx       → Login page (email + OAuth)
      callback/page.tsx    → OAuth callback handler
    dispensaries/
      page.tsx             → Dispensary listing
      [id]/page.tsx        → Dispensary detail with inventory
    products/
      search/page.tsx      → Price comparison search
      [id]/page.tsx        → Product detail with reviews
    profile/
      page.tsx             → User profile with review history
      notifications/page.tsx → Notification preferences
    watchlist/
      page.tsx             → Watchlist management
    layout.tsx            → Root layout with Providers wrapper
    page.tsx              → Home page
    providers.tsx         → Client-side providers (AuthProvider)
    globals.css           → Tailwind + compliance banner styles
  lib/
    api.ts                → Axios client with all endpoints + JWT interceptor
    AuthContext.tsx       → Global auth context with useAuth() hook
    supabase.ts           → Supabase client configuration
  components/
    AgeGate.tsx           → 21+ age verification
    FilterPanel.tsx       → Search filters (category, price, THC, etc.)
    SearchBar.tsx         → Search input with autocomplete
    ReviewForm.tsx        → Review submission with dual-track tags
    WatchlistButton.tsx   → Add/remove from watchlist
    PriceComparisonTable.tsx → Price display with direct product links (uses product_url)
    Toast.tsx             → Toast notifications
    ... (additional UI components)
  tailwind.config.ts     → Custom cannabis color palette
```

## Common Tasks & Patterns

### Adding a New Scraper

1. Create scraper class inheriting from `BaseScraper` in `backend/services/scrapers/`
2. Implement `scrape_products()` and `scrape_promotions()` async methods
3. Populate `weight` and `url` fields on `ScrapedProduct`:
   - `weight`: For proper variant creation (e.g., "3.5g", "1oz")
   - `url`: Direct link to product page for user purchases and admin verification
4. Add `@register_scraper` decorator with metadata (id, name, schedule_minutes, etc.)
5. Import in `main.py` to trigger self-registration
6. Scheduler automatically discovers and schedules it at startup
7. The `ConfidenceScorer` handles matching, variant creation, and flagging automatically

Example:
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
class NewDispensaryScraper(BaseScraper):
    async def scrape_products(self) -> List[ScrapedProduct]:
        # Scrape products and return list
        products = []
        # ... scraping logic ...
        return products

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        # Scrape promotions and return list
        promotions = []
        # ... scraping logic ...
        return promotions
```

### Adding a New API Endpoint

1. Create router in `backend/routers/` or add to existing router file
2. Use `@router.get/post/put/delete` decorator with path
3. Add `response_model=SchemaName` for validation if using Pydantic schemas
4. Use `db: Session = Depends(get_db)` to access database
5. For protected endpoints, add `current_user: User = Depends(get_current_user)`
6. Update `frontend/lib/api.ts` with corresponding call
7. Register router in `main.py` with `app.include_router()`

### Adding a New Database Model

1. Define class in `backend/models.py` inheriting from `Base`
2. Use UUID for `id`, proper relationships with `relationship()`
3. Add indexes on frequently searched fields (`index=True`)
4. Create Alembic migration: `alembic revision --autogenerate -m "description"`
5. Apply migration: `alembic upgrade head`

### Creating Frontend Components

1. File in `frontend/components/`, use `.tsx` extension
2. Define props interface at top of file
3. Export named function component (not default)
4. Use `api` from `lib/api.ts` for backend calls
5. Apply Tailwind classes for styling
6. Import and use in pages or other components
7. For auth-aware components, use `useAuth()` hook from `lib/AuthContext.tsx`

### Using Authentication in Components

```tsx
import { useAuth } from '@/lib/AuthContext'

export function MyComponent() {
  const { user, session, loading, signOut } = useAuth()

  if (loading) return <div>Loading...</div>
  if (!user) return <div>Please sign in</div>

  return <div>Welcome, {user.email}</div>
}
```

### Protected Routes (Frontend)

Use `ProtectedRoute` wrapper for pages requiring authentication:

```tsx
import { ProtectedRoute } from '@/components/ProtectedRoute'

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  )
}
```

### Running Tests

```bash
# Backend tests only
cd backend
pytest                    # Run all backend tests
pytest -v                 # Verbose output
pytest tests/test_matcher.py::test_specific_function  # Run specific test

# Frontend tests
cd frontend
npm test                  # Run jest tests
npm test -- --watchAll=false  # Run once and exit

# All tests via script
scripts\run-tests.bat
```

## Important Notes

### When Adding Features

- **Compliance**: Every page must display a disclaimer (handled globally in `app/globals.css`)
- **Mobile responsiveness**: 80% of users are mobile - test with DevTools
- **Environment variables**: Update both `.env.example` files if adding new vars
- **TypeScript**: Frontend components must have explicit types for props
- **Data normalization**: Different dispensaries use different naming - the `ConfidenceScorer` handles fuzzy matching automatically during scraper runs
- **Product variants**: When creating products manually or in seed data, follow the parent/variant pattern. Prices must link to variant products (with `weight` and `weight_grams`), reviews must link to parent products (`is_master=True`). The API handles variant-to-parent resolution for reviews and watchlist operations

### Scraper Considerations

- **Rate limiting**: Be respectful - use the configured `schedule_minutes` (default: 120 per PRD)
- **Error handling**: Scrapers should use `run_with_retries()` for resilience
- **Logging**: Use `self.logger` for all scraper-specific logging
- **Data quality**: Products are automatically matched via `ConfidenceScorer` fuzzy matching (>90% auto-merge, 60-90% flagged for review, <60% new product) - check quality dashboard
- **Weight field**: Scrapers should populate the `weight` field on `ScrapedProduct` for proper variant creation. The weight parser handles formats like "3.5g", "1oz", "1/8 oz", "1000mg"
- **URL field**: Scrapers should capture the `url` field (direct link to product page) for user purchases and admin verification. For auto-merged products (>90%), URLs are stored on Price records. For flagged products (60-90%), URLs are preserved on `ScraperFlag.original_url` and flow to Price records when the flag is resolved
- **Testing**: Run scrapers manually via admin dashboard before relying on scheduler
- **Async execution**: Admin-triggered scraper runs execute in the background via `asyncio.create_task()`. The API returns immediately with `{"status": "started"}` and the frontend polls for completion. The background task creates its own database session via `SessionLocal()` to avoid session lifecycle issues.
- **Run visibility**: `ScraperRun` entries are committed (not just flushed) with status `"running"` so polling from other sessions can see them immediately

### Authentication Gotchas

- **JWT vs Supabase tokens**: Backend uses JWT, frontend uses Supabase - don't mix them
- **Token refresh**: Axios interceptor automatically handles token refresh
- **Protected routes**: Always use `get_current_user()` dependency on backend
- **Age gate**: All users must pass 21+ verification before accessing app features

### Testing Strategy

- **Backend**: pytest with `pytest-asyncio` for async functions
- **Frontend**: Jest + React Testing Library (configured in `frontend/jest.config.js`)
- **Run tests**: `scripts\run-tests.bat` for both backends
- **Test data**: Use `backend/seed_test_data.py` to populate test database

### Deployment Notes

- **Frontend**: Vercel (Next.js optimized)
- **Backend**: Cloud provider (AWS/Heroku/DigitalOcean) - requires database URL
- **Database**: Supabase managed PostgreSQL
- **Environment**: Production `.env` differs from development - always verify vars
- **Scheduler**: APScheduler with SQLAlchemy job store persists scheduled runs across restarts

## Debugging Tips

### Backend Issues

```bash
# Check if server is running
curl http://localhost:8000/health

# Verify database connection
cd backend
python -c "from database import SessionLocal; from models import User; db = SessionLocal(); print(db.query(User).count())"

# View all routes (Swagger UI)
# Visit http://localhost:8000/docs

# Enable debug logging
# Edit config.py: set debug = True and log_level = "DEBUG"

# Test specific scraper
cd backend
python -c "
import asyncio
from services.scraper_runner import ScraperRunner
from database import SessionLocal

async def test():
    db = SessionLocal()
    runner = ScraperRunner(db, triggered_by='manual')
    result = await runner.run_by_id('wholesomeco')
    print(result)
    db.close()

asyncio.run(test())
"

# Check scheduler status
# Visit admin dashboard: http://localhost:4002/admin/scrapers
```

### Product Variant Issues

```bash
# Check for prices incorrectly attached to parent products (should be on variants)
cd backend
python -c "
from database import SessionLocal
from models import Product, Price
db = SessionLocal()
bad = db.query(Price).join(Product).filter(Product.is_master == True).count()
print(f'Prices on parent products (should be 0): {bad}')
db.close()
"

# Count variants per parent product
python -c "
from database import SessionLocal
from models import Product
from sqlalchemy import func
db = SessionLocal()
results = db.query(Product.name, func.count(Product.id)).filter(
    Product.is_master == False
).group_by(Product.master_product_id, Product.name).all()
for name, count in results[:10]:
    print(f'{name}: {count} variants')
db.close()
"

# Find orphaned variants (no parent)
python -c "
from database import SessionLocal
from models import Product
db = SessionLocal()
orphans = db.query(Product).filter(
    Product.is_master == False,
    Product.master_product_id == None
).count()
print(f'Orphaned variants (should be 0): {orphans}')
db.close()
"

# List all parent products and their variant weights
python -c "
from database import SessionLocal
from models import Product
db = SessionLocal()
parents = db.query(Product).filter(Product.is_master == True).all()
for p in parents[:10]:
    weights = [v.weight for v in p.variants if v.weight]
    print(f'{p.name}: {weights or \"no variants\"}')
db.close()
"
```

### Frontend Issues

```bash
# Check API connectivity
# Open browser console and run:
import { api } from '@/lib/api'
api.health().then(r => console.log(r.data))

# Verify environment variables
# Check frontend/.env.local has NEXT_PUBLIC_API_URL pointing to backend

# Clear Next.js cache
rm -rf .next  # macOS/Linux
rmdir /s /q .next  # Windows

# Check Supabase auth
# Open browser console:
import { supabase } from '@/lib/supabase'
supabase.auth.getSession().then(console.log)

# TypeScript errors
npm run type-check  # List all type errors
```

### Common Issues

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| 401 on API requests | Expired JWT token | Axios interceptor auto-refreshes - check network tab |
| Scraper not running | Not registered | Check import in `main.py` and decorator |
| Products not matching | Low similarity score | Check `ConfidenceScorer` thresholds (>90% auto-merge, 60-90% flag, <60% new product) |
| Scheduler not running | Database URL issue | Check `settings.database_url` in scheduler config |
| Age gate loop | Age not stored in localStorage | Check browser localStorage for `ageVerified` |
| SendGrid emails failing | Missing API key | Add `SENDGRID_API_KEY` to backend `.env` |

## Development Workflows

The project includes 10 comprehensive workflow documents that guide development through all three phases of the MVP. These workflows are self-contained with code examples, verification steps, and success criteria.

**Location**: `docs/workflows/` (read the README for overview)

### Workflow Structure

Each workflow follows a consistent pattern:
1. **Context**: PRD references and requirements
2. **Steps**: Sequential, action-oriented steps with code examples
3. **Verification**: Commands to test completion
4. **Success Criteria**: Checklist for acceptance

### Workflow Organization

**Phase 1 - Foundation (Workflows 01-04)**
- 01: Project Initialization (COMPLETED ✅)
- 02: Database Schema and Migrations
- 03: Scraper Foundation
- 04: Admin Dashboard Cleanup Queue

**Phase 2 - Portal (Workflows 05-07)**
- 05: Price Comparison Search
- 06: Product Detail Pages
- 07: Dispensary Pages

**Phase 3 - Community (Workflows 08-10)**
- 08: User Authentication
- 09: Review System Dual-Track
- 10: Stock Alerts and Notifications

### Using Workflows

1. Read `docs/workflows/README.md` for overview
2. Start with the next incomplete workflow in sequence
3. Read the PRD sections referenced in the workflow
4. Follow all steps in order
5. Verify completion using success criteria
6. Move to next workflow

### Key Points for Following Workflows

- Code examples are production-ready and reference actual file paths
- Commands are designed to run in the project root or subdirectories
- Each workflow is self-contained but builds on previous workflows
- Success criteria must be fully met before moving to next workflow
- Workflows reference ARCHITECTURE.md for design context
### notes from insights
Add as a top-level section: ## Platform & Environment\n\nThis project runs on Windows. Avoid Unix-specific commands (e.g., `kill`, `lsof`), watch for reserved filenames (e.g., `nul`, `con`, `aux`), and use `taskkill` or PowerShell equivalents for process management. For Python asyncio, prefer `asyncio.WindowsSelectorEventLoopPolicy()` or test subprocess approaches carefully on Windows/Python 3.13+.
Add under a new section: ## Git & Version Control\n\nWhen committing changes, do NOT use interactive commit helper scripts. Instead, manually stage and commit files using `git add` and `git commit` commands directly. Organize commits into logical groups (e.g., backend, frontend, tests, docs).
Add under a new section: ## Debugging Guidelines\n\nWhen debugging connection or configuration issues, check .env files and actual service availability FIRST before attempting code-level fixes. For Supabase, verify the service role key, anon key, and URL are correct and the service is reachable.
Add as a top-level section: ## Project Architecture\n\nThis project uses: Python (backend/scrapers), TypeScript (frontend), Supabase (database/auth). The scraper pipeline writes to Supabase. Products have weight variants with fuzzy matching. Always check existing database schema and migrations before making data model assumptions.
Add under a new section: ## Working Style Preferences\n\nWhen the user references specific files or plans, focus on those FIRST before doing broad searches across the codebase. Ask for clarification rather than scanning everything.

## References

### Key Documentation Files

| File | Purpose |
|------|---------|
| `backend/models.py` | Authoritative database schema (11 tables) |
| `backend/prisma/schema.prisma` | Reference schema visualization |
| `docs/ARCHITECTURE.md` | Detailed system architecture |
| `docs/GETTING_STARTED.md` | Initial setup guide |
| `docs/API_TEST_PLAN.md` | API testing scenarios |
| `docs/workflows/README.md` | All 10 MVP implementation workflows |
| `scripts/README.md` | Development scripts reference |
| `.projectrc.json` | Project metadata and configuration |

### Important URL Locations

**Local Development:**
- Frontend: http://localhost:4002 (use ports 4001-4009 range)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs (Swagger UI)
- Admin Dashboard: http://localhost:4002/admin
- Search: http://localhost:4002/products/search

**Admin Pages:**
- Main Dashboard: `/admin`
- Scraper Management: `/admin/scrapers`
- Quality Metrics: `/admin/quality`
- Cleanup Queue: `/admin/cleanup`

**User Pages:**
- Login: `/auth/login`
- Profile: `/profile`
- Watchlist: `/watchlist`
- Notification Settings: `/profile/notifications`

### Router Endpoints Summary

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| `admin_scrapers.py` | `/api/admin/scrapers` | List, run (async/background), status, history, health, pause, resume |
| `admin_flags.py` | `/api/admin/flags` | List, resolve, bulk resolve |
| `auth.py` | `/api/auth` | Register, login, refresh, verify |
| `users.py` | `/api/users` | Profile, reviews, public profile |
| `products.py` | `/api/products` | List, get, search, prices (with product_url), history |
| `dispensaries.py` | `/api/dispensaries` | List, get, inventory |
| `search.py` | `/api/products/search` | Fuzzy search with filters |
| `reviews.py` | `/api/reviews` | CRUD, upvote, product filtering |
| `watchlist.py` | `/api/watchlist` | Add, remove, list, check |
| `notifications.py` | `/api/notifications` | Preferences (get, update) |
| `scrapers.py` | `/api/scrapers` | Public scraper info |
