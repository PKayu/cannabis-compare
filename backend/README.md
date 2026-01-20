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

4. Run the server:
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
├── prisma/
│   └── schema.prisma    # Database schema reference
├── routers/             # API route modules (to be created)
│   ├── auth.py
│   ├── products.py
│   ├── prices.py
│   ├── reviews.py
│   └── dispensaries.py
├── schemas/             # Pydantic schemas (to be created)
├── services/            # Business logic (to be created)
│   └── scrapers/        # Web scrapers for dispensaries
├── tests/               # Test files (to be created)
└── README.md            # This file
```

## Database Schema

The database is modeled with the following main entities:

- **User**: User accounts with email/password
- **Product**: Cannabis products (strains, vapes, etc.)
- **Brand**: Cannabis cultivators/brands
- **Dispensary**: Physical dispensary locations
- **Price**: Product pricing at each dispensary
- **Review**: User reviews and ratings

See `prisma/schema.prisma` for detailed schema definition.

## API Endpoints (Planned)

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

## Data Scraping

Scrapers for dispensary data will be located in `services/scrapers/`:
- `iheartjane_scraper.py` - iHeartJane menu scraper
- `dutchie_scraper.py` - Dutchie menu scraper
- Data normalization logic for merging products

## Running Tests

```bash
pytest
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key (change for production)
- `SUPABASE_URL` & `SUPABASE_KEY`: For Supabase integration

## Development Notes

- Use FastAPI's automatic API documentation at `/docs` for testing endpoints
- Database migrations will use Alembic (to be set up)
- All user input should be validated using Pydantic schemas
- JWT tokens for authentication

## Next Steps

1. Set up Alembic for database migrations
2. Create Pydantic schemas for request/response validation
3. Implement authentication routers
4. Build product and pricing routers
5. Implement web scrapers for dispensaries
6. Add comprehensive tests
