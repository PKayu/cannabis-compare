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

### 🎯 Phase 2: Frontend Portal (In Progress)
- [ ] Price comparison search UI
- [ ] Product detail pages
- [ ] Dispensary listing and details
- [ ] Map integration

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
