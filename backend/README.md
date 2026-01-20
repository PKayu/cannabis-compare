# Backend - Utah Cannabis Aggregator API

FastAPI backend for the Utah Cannabis Aggregator platform. Handles data aggregation, user authentication, and review management.

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL or Supabase account

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database URL and other settings
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Run the server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── database.py          # Database connection and session
├── models.py            # SQLAlchemy ORM models
├── requirements.txt     # Python dependencies
├── alembic.ini          # Alembic configuration
├── alembic/             # Database migrations
│   ├── env.py
│   └── versions/
├── prisma/
│   └── schema.prisma    # Database schema reference
├── routers/             # API route modules
│   ├── auth.py
│   ├── products.py
│   ├── prices.py
│   ├── reviews.py
│   ├── dispensaries.py
│   └── admin.py         # Admin dashboard endpoints
├── schemas/             # Pydantic schemas
├── services/            # Business logic
│   ├── scrapers/        # Web scrapers for dispensaries
│   │   ├── base_scraper.py
│   │   └── wholesome_co_scraper.py
│   ├── normalization/   # Product matching and normalization
│   │   ├── matcher.py
│   │   ├── scorer.py
│   │   └── flag_processor.py
│   └── scheduler.py     # APScheduler for recurring jobs
├── tests/               # Test files
└── README.md            # This file
```

## Database Schema

The database includes the following entities:

- **User**: User accounts with email/password
- **Product**: Cannabis products (strains, vapes, etc.)
- **Brand**: Cannabis cultivators/brands
- **Dispensary**: Physical dispensary locations
- **Price**: Product pricing at each dispensary (with history tracking)
- **Review**: User reviews and ratings
- **ScraperFlag**: Products requiring manual normalization review
- **Promotion**: Recurring and one-time promotional offers

See `prisma/schema.prisma` for detailed schema definition.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user

### Products
- `GET /api/products` - List products with filtering
- `GET /api/products/{id}` - Get product details
- `GET /api/products/search` - Search products

### Prices
- `GET /api/prices/compare` - Compare prices across dispensaries
- `GET /api/prices/{product_id}` - Get prices for a product

### Reviews
- `POST /api/reviews` - Create review
- `GET /api/products/{id}/reviews` - Get reviews for product
- `PUT /api/reviews/{id}` - Update review
- `DELETE /api/reviews/{id}` - Delete review

### Dispensaries
- `GET /api/dispensaries` - List all dispensaries
- `GET /api/dispensaries/{id}` - Get dispensary details

### Admin (ScraperFlags)
- `GET /api/admin/flags` - List pending scraper flags
- `POST /api/admin/flags/{id}/approve` - Approve flag merge
- `POST /api/admin/flags/{id}/reject` - Reject flag and create new product

## Scraper System

### Overview

The scraper system aggregates product and promotion data from Utah dispensary websites. It uses:

- **Confidence-based matching** to normalize products across dispensaries
- **Automatic scheduling** via APScheduler for regular updates
- **Admin review queue** for uncertain matches

### Confidence Thresholds (PRD Section 4.1)

- **>90%**: Auto-merge to existing product
- **60-90%**: Flagged for admin review (ScraperFlag)
- **<60%**: Create new product entry

### Scraper Configuration

Each scraper implements `BaseScraper` and must provide:
- `scrape_products()` - Returns list of current inventory
- `scrape_promotions()` - Returns list of current promotions

### Running Scrapers

**Manually:**
```python
from services.scrapers.wholesome_co_scraper import WholesomeCoScraper

scraper = WholesomeCoScraper("dispensary-id")
result = await scraper.run()
# Or with retries:
result = await scraper.run_with_retries(max_retries=3)
```

**Scheduled (every 2 hours):**
```python
from services.scheduler import ScraperScheduler
from services.scrapers.wholesome_co_scraper import WholesomeCoScraper

scheduler = ScraperScheduler()
scheduler.add_scraper_job(WholesomeCoScraper, "dispensary-id", minutes=120)
await scheduler.start()
```

### Adding a New Scraper

1. Create a new file in `services/scrapers/`:
```python
from services.scrapers.base_scraper import BaseScraper, ScrapedProduct, ScrapedPromotion

class NewDispensaryScraper(BaseScraper):
    BASE_URL = "https://example.com"

    async def scrape_products(self) -> List[ScrapedProduct]:
        # Implement product scraping
        pass

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        # Implement promotion scraping
        pass
```

2. Register with the scheduler in `main.py`:
```python
from services.scheduler import get_scheduler
scheduler = get_scheduler()
scheduler.add_scraper_job(NewDispensaryScraper, "new-dispensary-id")
```

### Normalization Service

The normalization service (`services/normalization/`) handles:

- **ProductMatcher**: Fuzzy matching using RapidFuzz library
- **ConfidenceScorer**: Decision logic for auto-merge/flag/create
- **ScraperFlagProcessor**: Admin approval/rejection workflow

## Database Migrations

Using Alembic for migrations:

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current version
alembic current
```

See `docs/database_rollback.md` for detailed rollback procedures.

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest backend/tests/test_matcher.py -v

# Run with coverage
pytest --cov=backend
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key (change for production)
- `SUPABASE_URL` & `SUPABASE_KEY`: For Supabase integration

## Development Notes

- Use FastAPI's automatic API documentation at `/docs` for testing endpoints
- All user input should be validated using Pydantic schemas
- JWT tokens for authentication
- Scrapers run every 2 hours (configurable) per PRD requirement
- Target >80% auto-merge rate for product normalization
