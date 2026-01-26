# Utah Cannabis Aggregator

A web-based platform for Utah Medical Cannabis patients to compare prices across dispensaries and access community-driven reviews for strains and brands.

## Project Structure

```
.
├── frontend/          # Next.js React application
├── backend/           # Python FastAPI backend
├── scripts/           # Development scripts (start, install, test)
├── docs/              # Project documentation
│   ├── INDEX.md       # Documentation navigation hub
│   ├── guides/        # Topic-specific guides
│   └── workflows/     # Implementation workflows
└── README.md          # This file
```

## Tech Stack

- **Frontend**: Next.js (React), TypeScript, Tailwind CSS
- **Backend**: Python, FastAPI, Pydantic
- **Database**: PostgreSQL (via Supabase)
- **ORM**: SQLAlchemy (Python) & Prisma (for schema definition)
- **Deployment**: Vercel (Frontend) + Supabase (Backend/DB)

## Getting Started

### Prerequisites
- Node.js 18+ (for frontend development)
- Python 3.10+ (for backend development)
- PostgreSQL or Supabase account

### Quick Start (Recommended)

```bash
# Install all dependencies
scripts\install-deps.bat

# Start both servers
scripts\start-dev.bat
```

### Manual Setup

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Environment Variables

See `.env.example` files in each directory for required environment variables.

## Core Features (MVP)

- **User Authentication**: Email/Password or OAuth verification (21+)
- **Price Aggregation**: Real-time pricing across Utah dispensaries
- **Product Catalog**: Strain names, brands, THC/CBD %, formats
- **Review System**: 5-star ratings for effects, taste, and value
- **Search & Filtering**: By strain, brand, dispensary, price, THC %

## Database Schema

See `backend/prisma/schema.prisma` for the complete database schema.

## Development Status

### ✅ Phase 1: Foundation (COMPLETED - January 2026)
- [x] Database schema with 8 tables and 26 indexes
- [x] Alembic migrations configured
- [x] Admin API endpoints (10 routes)
- [x] Scraper foundation with fuzzy matching
- [x] ScraperFlag cleanup queue
- [x] Outlier detection algorithm
- [x] Test data and API test plan

**See**: `docs/API_TEST_PLAN.md` for testing instructions

### 🎯 Phase 2: Frontend Portal (In Progress - January 2026)
- [x] **Workflow 05**: Price comparison search UI ✅ COMPLETED
  - [x] Backend search router with fuzzy matching (rapidfuzz)
  - [x] Backend products router with price comparison endpoint
  - [x] Routers registered in main.py (20 total routes)
  - [x] Frontend search page component (`app/products/search/page.tsx`)
  - [x] Frontend filter and results components (FilterPanel, ResultsTable, SearchBar, DealBadge)
  - [x] API client integration (`lib/api.ts` updated)
  - [x] All endpoints tested and working
  - [x] Search performance verified (<200ms)
  - [x] Test data in database (5 products)
  - **Known Issue**: Autocomplete dropdown not triggering (deferred to future phase)

- [x] **Workflow 06**: Product detail pages ✅ COMPLETED
  - [x] Dynamic route `/products/[id]` page
  - [x] PriceComparisonTable component with dispensary deep-linking
  - [x] PricingChart component with min/max/avg visualization
  - [x] ReviewsSection placeholder (full implementation in Workflow 09)
  - [x] Pricing history endpoint (`/api/products/{id}/pricing-history`)
  - [x] Mobile responsive design
  - [x] Stock status indicators
  - [x] Promotion/deal badges

- [x] **Workflow 07**: Dispensary listing and details ✅ COMPLETED
  - [x] Dispensary listing page with product counts
  - [x] Dispensary detail page with promotions
  - [x] Inventory browser with filters and sorting
  - [x] CurrentPromotions component with weekly calendar
  - [x] Mobile responsive design

### 🔐 Phase 3: Community Features (In Progress - January 2026)

- [x] **Workflow 08**: User Authentication ✅ COMPLETED
  - [x] Supabase Auth setup (magic links + Google OAuth)
  - [x] Age gate verification component (21+ validation)
  - [x] Backend auth router (register, login, refresh, verify)
  - [x] User profile router (profile, reviews, public profile)
  - [x] JWT token generation and validation
  - [x] Frontend login page with email and OAuth options
  - [x] User profile page with review history
  - [x] Protected route wrapper component
  - [x] API client JWT interceptor
  - [x] User navigation menu with dropdown
  - [x] Comprehensive test plan (14 scenarios)
  - [x] 12 new files created, 3 files modified
  - [x] Zero TypeScript/Python type errors

- [x] **Workflow 09**: Review System Dual-Track ✅ COMPLETED (January 2026)
  - [x] Dual-track intention tags (Medical: pain/insomnia/anxiety/nausea/spasms | Mood: socializing/creativity/focus/deep_relaxation/post_workout)
  - [x] Intention tag enums in backend/model_enums/enums.py
  - [x] Review model with intention_type and intention_tag fields
  - [x] 1-5 star ratings (Effects, Taste, Value)
  - [x] Review submission endpoint with validation
  - [x] Review filtering by intention (type and tag)
  - [x] Review sorting (recent, helpful, rating_high)
  - [x] ReviewForm component with dual-track UI
  - [x] ReviewsSection component with filtering
  - [x] Batch tracking (batch_number, cultivation_date)
  - [x] Review upvoting functionality
  - [x] Update/delete endpoints with ownership checks
  - [x] Integration into product detail pages
  - [x] Zero TypeScript errors

- [x] **Workflow 10**: Stock Alerts and Notifications ✅ COMPLETED (January 2026)
  - [x] Watchlist database models (Watchlist, PriceAlert, NotificationPreference)
  - [x] Stock availability detection (24-hour deduplication)
  - [x] Price drop detection with configurable thresholds
  - [x] SendGrid email integration with HTML templates
  - [x] User notification preferences (immediate/daily/weekly)
  - [x] WatchlistButton component with threshold configuration
  - [x] Watchlist page at /watchlist with management UI
  - [x] Notification preferences page at /profile/notifications
  - [x] Product pages include WatchlistButton
  - [x] Top-level navigation with watchlist link and badge
  - [x] Alert scheduler (runs every 1-2 hours)
  - [x] 4 watchlist API endpoints, 2 notification endpoints

**Current Status**: Phase 3 COMPLETE ✅ - All 10 Workflows COMPLETE! 🎉

**Running Services:**
- Backend: http://127.0.0.1:8000 ✅
- Frontend: http://localhost:3000 ✅
- **Authentication**: http://localhost:3000/auth/login
- **Profile Page**: http://localhost:3000/profile
- **Watchlist**: http://localhost:3000/watchlist
- **Notification Settings**: http://localhost:3000/profile/notifications
- **Search Page**: http://localhost:3000/products/search
- **Product Detail**: http://localhost:3000/products/prod-002
- **Dispensaries**: http://localhost:3000/dispensaries

**Tested Endpoints:**
- ✅ `POST /api/auth/register` - User registration
- ✅ `POST /api/auth/login` - Email/password login
- ✅ `GET /api/users/me` - Current user profile (protected)
- ✅ `GET /api/products/search?q=gorilla` - Returns Gorilla Glue #4
- ✅ `GET /api/products/{id}` - Product details
- ✅ `GET /api/products/{id}/prices` - Price comparison
- ✅ `GET /api/dispensaries` - List all dispensaries
- ✅ `GET /api/dispensaries/{id}` - Dispensary details with promotions
- ✅ `GET /api/dispensaries/{id}/inventory` - Products at dispensary
- ✅ `POST /api/reviews/` - Submit product review (protected)
- ✅ `GET /api/reviews/product/{id}` - Get reviews with filtering/sorting
- ✅ `PUT /api/reviews/{id}` - Update own review (protected)
- ✅ `DELETE /api/reviews/{id}` - Delete own review (protected)
- ✅ `POST /api/reviews/{id}/upvote` - Upvote review (protected)
- ✅ `POST /api/watchlist/add` - Add product to watchlist (protected)
- ✅ `DELETE /api/watchlist/remove/{id}` - Remove from watchlist (protected)
- ✅ `GET /api/watchlist/` - Get user's watchlist (protected)
- ✅ `GET /api/watchlist/check/{id}` - Check if product is watched (protected)
- ✅ `GET /api/notifications/preferences` - Get notification settings (protected)
- ✅ `PUT /api/notifications/preferences` - Update notification settings (protected)
- ✅ `GET /health` - API is healthy

**Test Data Available:**
- Blue Dream (Flower) - 22.5% THC - $45-$120
- Gorilla Glue #4 (Flower) - 28% THC - $55
- Wedding Cake (Flower) - $50-$52
- OG Kush Vape Cart (Vape) - 85% THC - $5-$38
- CBD Relief Tincture (Tincture) - 20% CBD - $62-$65

**To Start Development:**
```bash
# Terminal 1: Backend
cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

**Open Browser**: http://localhost:3000/products/search
4. Try searching for "gorilla", "dream", "flower", "vape", etc.

**See**: `docs/workflows/05-07` for implementation guides

### 📋 Phase 3: Community Features (Planned)
- [ ] User authentication (Supabase)
- [ ] Review system with dual-track tags
- [ ] Stock alerts and notifications
- [ ] User profiles

**See**: `docs/workflows/08-10` for implementation guides

## Quick Start

### Run Backend Server
```bash
cd backend
uvicorn main:app --reload
# Server: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Seed Test Data
```bash
cd backend
python seed_test_data.py
# Creates: 3 dispensaries, 6 products, 13 prices, 5 flags, etc.
```

### Run Frontend (Coming in Phase 2)
```bash
cd frontend
npm run dev
# App: http://localhost:3000
```

## Contributing

Please ensure all code follows project conventions and includes appropriate tests.

## License

TBD
