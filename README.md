# Utah Cannabis Aggregator

A web-based platform for Utah Medical Cannabis patients to compare prices across dispensaries and access community-driven reviews for strains and brands.

## Project Structure

```
.
├── frontend/          # Next.js React application
├── backend/           # Python FastAPI backend
├── docs/              # Project documentation
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

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
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

- [ ] **Workflow 07**: Dispensary listing and details (NEXT)

**Current Status**: Workflows 05-06 complete. Starting Workflow 07 (Dispensary Pages).

**Running Services:**
- Backend: http://127.0.0.1:8000 ✅
- Frontend: http://localhost:3000 ✅
- **Search Page**: http://localhost:3000/products/search
- **Product Detail**: http://localhost:3000/products/prod-002 (example)

**Tested Endpoints:**
- ✅ `GET /api/products/search?q=dream` - Returns Blue Dream
- ✅ `GET /api/products/search?q=gorilla` - Returns Gorilla Glue #4
- ✅ `GET /api/products/{id}` - Product details
- ✅ `GET /api/products/{id}/prices` - Price comparison across dispensaries
- ✅ `GET /api/products/{id}/pricing-history` - Historical pricing data
- ✅ `GET /api/products/autocomplete?q=gor` - Returns suggestions
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
