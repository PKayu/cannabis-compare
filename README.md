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

## Roadmap

### Phase 1: Data Ingestion
- Build scrapers for 3 major Utah dispensaries (iHeartJane/Dutchie)
- Implement data normalization logic

### Phase 2: Frontend MVP
- Display aggregated pricing
- Search and filter functionality
- Read-only product catalog

### Phase 3: User System
- Authentication system
- Review and rating system
- User profiles

## Contributing

Please ensure all code follows project conventions and includes appropriate tests.

## License

TBD
