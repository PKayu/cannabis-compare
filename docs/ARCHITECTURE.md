# System Architecture

## Overview

Utah Cannabis Aggregator is a full-stack web application designed to help Utah Medical Cannabis patients find the best prices across dispensaries and access community reviews.

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Browser       │         │   Next.js        │         │   FastAPI       │
│   (React)       │◄───────►│   Frontend       │◄───────►│   Backend       │
│                 │         │   (Vercel)       │         │   (AWS/Heroku)  │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                                                   │
                                                                   ▼
                                                         ┌─────────────────┐
                                                         │  PostgreSQL     │
                                                         │  (Supabase)     │
                                                         └─────────────────┘
```

## Technology Stack

### Frontend
- **Framework**: Next.js 14 (React 18)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Deployment**: Vercel
- **Authentication**: Supabase Auth with global AuthContext provider
- **State Management**: React Context for auth state (`lib/AuthContext.tsx`)

### Backend
- **Framework**: FastAPI (Python)
- **ASGI Server**: Uvicorn
- **ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Authentication**: JWT + bcrypt
- **Web Scraping**: BeautifulSoup4, Selenium (for dynamic content)
- **Async**: aiohttp for concurrent requests
- **Testing**: pytest, pytest-asyncio

### Database
- **Primary DB**: PostgreSQL (via Supabase)
- **ORM**: SQLAlchemy (Python)
- **Schema Definition**: Prisma (reference)
- **Migrations**: Alembic (planned)

### Infrastructure
- **Frontend Hosting**: Vercel
- **Backend Hosting**: AWS, Heroku, or DigitalOcean
- **Database Hosting**: Supabase (managed PostgreSQL)
- **Version Control**: Git

## Data Flow

### 1. Price Aggregation Flow
```
Dispensary Website/API
        ↓
   Scraper Service
        ↓
Data Normalization
        ↓
Database (prices table)
        ↓
API Endpoint
        ↓
Frontend (Price Comparison)
        ↓
User Browser
```

### 2. Review Flow
```
User Submit Review
        ↓
Frontend Form
        ↓
POST /api/reviews
        ↓
Backend Validation
        ↓
Database (reviews table)
        ↓
GET /api/products/{id}/reviews
        ↓
Frontend Display
```

### 3. Search Flow
```
User Input Search Query
        ↓
Frontend Search Bar
        ↓
GET /api/products/search?q=...
        ↓
Backend Query Processing
        ↓
Database Query
        ↓
Result Filtering/Sorting
        ↓
Response with Products
        ↓
Frontend Display Results
```

## Database Schema

### Core Entities

**User**
- id (UUID, Primary Key)
- email (String, Unique)
- username (String, Unique)
- hashed_password (String)
- created_at (DateTime)

**Product**
- id (UUID, Primary Key)
- name (String) - Strain name
- product_type (String) - lowercase values: flower, vaporizer, tincture, edible, topical, concentrate
- thc_percentage (Float) - Optional
- cbd_percentage (Float) - Optional
- brand_id (UUID, Foreign Key)

**Product Type Standards**: All product types must use lowercase values to ensure consistency between scrapers, seed data, and frontend filters. Valid types: `flower`, `vaporizer`, `tincture`, `edible`, `topical`, `concentrate`.

**Brand**
- id (UUID, Primary Key)
- name (String, Unique)

**Dispensary**
- id (UUID, Primary Key)
- name (String)
- website (String, Optional)
- location (String, Optional)

**Price**
- id (UUID, Primary Key)
- amount (Float) - Price in USD
- in_stock (Boolean)
- last_updated (DateTime)
- product_id (UUID, Foreign Key)
- dispensary_id (UUID, Foreign Key)
- **Unique Constraint**: (product_id, dispensary_id)

**Review**
- id (UUID, Primary Key)
- rating (Integer) - 1-5 overall
- effects_rating (Integer) - 1-5 optional
- taste_rating (Integer) - 1-5 optional
- value_rating (Integer) - 1-5 optional
- comment (Text, Optional)
- upvotes (Integer, Default: 0)
- user_id (UUID, Foreign Key)
- product_id (UUID, Foreign Key)
- created_at (DateTime)

## API Architecture

### Authentication Routes
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Get JWT token
- `POST /api/auth/logout` - Invalidate token
- `POST /api/auth/refresh` - Refresh JWT token

### Product Routes
- `GET /api/products` - List with filtering/pagination
- `GET /api/products/{id}` - Get product details
- `GET /api/products/search?q=...` - Search functionality
- `POST /api/products` - Admin only: Create product
- `PUT /api/products/{id}` - Admin only: Update product

### Price Routes
- `GET /api/prices/compare?product_id=...` - Compare across dispensaries
- `GET /api/prices/{product_id}` - Get all prices for product
- `POST /api/prices` - Admin/Scraper only: Add/update price

### Review Routes
- `POST /api/reviews` - Create review (requires auth)
- `GET /api/products/{id}/reviews` - Get reviews for product
- `PUT /api/reviews/{id}` - Update own review (requires auth)
- `DELETE /api/reviews/{id}` - Delete own review (requires auth)
- `POST /api/reviews/{id}/upvote` - Upvote review

### Dispensary Routes
- `GET /api/dispensaries` - List all dispensaries
- `GET /api/dispensaries/{id}` - Get dispensary details

### Admin Scraper Routes (Implemented)
- `POST /api/admin/scrapers/run/{scraper_id}` - Trigger scraper run (async/background -- returns `{"status": "started"}` immediately; poll `/runs` for progress)
- `GET /api/admin/scrapers/runs` - Paginated run history with scraper_id/status filters
- `GET /api/admin/scrapers/health` - 7-day health metrics per scraper
- `GET /api/admin/scrapers/scheduler/status` - Scheduler state and job list
- `POST /api/admin/scrapers/scheduler/pause/{scraper_id}` - Pause scheduled scraper
- `POST /api/admin/scrapers/scheduler/resume/{scraper_id}` - Resume scheduled scraper
- `GET /api/admin/scrapers/quality/metrics` - Data completeness metrics
- `GET /api/admin/scrapers/dispensaries/freshness` - Data freshness per dispensary

### Admin Flag Routes (Implemented)
- `GET /api/admin/flags/pending` - Get pending ScraperFlags for review
- `GET /api/admin/flags/stats` - Flag statistics (pending/approved/rejected)
- `GET /api/admin/flags/{flag_id}` - Get specific flag detail
- `POST /api/admin/flags/approve/{flag_id}` - Approve merge of flagged product
- `POST /api/admin/flags/reject/{flag_id}` - Reject flag and create new product

## Request/Response Format

### Standard Response
```json
{
  "status": "success",
  "data": {...},
  "timestamp": "2024-01-19T12:00:00Z"
}
```

### Error Response
```json
{
  "status": "error",
  "error": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-19T12:00:00Z"
}
```

## Authentication & Authorization

### Supabase Auth Integration
The application uses Supabase Auth for user authentication with a centralized React Context provider.

**Frontend Authentication Flow:**
1. `AuthProvider` wraps the entire app in `layout.tsx` via `providers.tsx`
2. On mount, `AuthContext` fetches initial session and subscribes to auth state changes
3. Components use the `useAuth()` hook to access: `user`, `session`, `loading`, `signOut`
4. Auth state is automatically synchronized across all components via React Context
5. JWT tokens from Supabase are automatically included in API requests via Axios interceptors

**Key Files:**
- `frontend/lib/AuthContext.tsx` - Global auth context with `useAuth()` hook
- `frontend/app/providers.tsx` - Client-side providers wrapper
- `frontend/lib/supabase.ts` - Supabase client configuration

**Important:** Always use the `useAuth()` hook instead of making independent Supabase calls. This ensures auth state consistency and prevents issues with state not persisting across page reloads or tab switches.

### Backend Auth Verification
- Protected endpoints use `Depends(get_current_user)` to verify JWT tokens
- The dependency returns the full `User` object, not just the user ID
- Queries should use `current_user.id` to access the authenticated user's ID

### Role-Based Access Control (Planned)
- User: Can post reviews, view products
- Moderator: Can edit/delete reviews
- Admin: Can create products, trigger scrapers

## Data Scraping Strategy

### Phase 1: Manual Data Entry
- Manually enter initial dispensaries and products
- Focus on 3 major Utah dispensaries

### Phase 2: API Integration
- iHeartJane API integration (if available)
- Dutchie API integration (if available)

### Phase 3: Web Scraping
- BeautifulSoup for static HTML
- Selenium for JavaScript-heavy sites
- Scheduled jobs to refresh prices daily

### Data Normalization
- Duplicate product detection (e.g., "GG#4" vs "Gorilla Glue 4")
- Brand name standardization
- Price format normalization (handle discounts, bulk pricing)

## Performance Considerations

### Frontend
- Next.js SSR for SEO
- Image optimization with next/image
- Code splitting per route
- Caching headers for static assets
- Target: <200ms search results

### Backend
- Database indexing on frequently queried columns
  - products.name
  - products.brand_id
  - prices.product_id
  - prices.dispensary_id
- Connection pooling
- Async request handling
- Caching for price comparisons (5-minute TTL)

### Database
- Proper indexing strategy
- Query optimization
- Connection pooling
- Regular VACUUM maintenance

## Security Considerations

1. **Authentication**
   - Passwords hashed with bcrypt (cost: 10+)
   - JWT tokens with expiration
   - Refresh token rotation

2. **Authorization**
   - Role-based access control
   - User can only edit/delete own reviews

3. **Input Validation**
   - Pydantic models validate all requests
   - SQLAlchemy prevents SQL injection
   - CORS configured for trusted origins

4. **Data Protection**
   - HTTPS only in production
   - No sensitive data in logs
   - Environment variables for secrets
   - Rate limiting on auth endpoints

5. **Compliance**
   - Clear disclaimer on every page
   - No actual product transactions
   - User data privacy policy

## Deployment Strategy

### Development
```
Local: Frontend (3000) + Backend (8000) + Local DB
```

### Production
```
Frontend: Vercel
Backend: Cloud Provider (AWS/Heroku/DigitalOcean)
Database: Supabase (managed PostgreSQL)
```

### CI/CD Pipeline (Planned)
- GitHub Actions for automated testing
- Pre-deployment checks (linting, tests)
- Automated deployments on push to main
- Rollback capability

## Scalability & Future Enhancements

### Short Term
- More dispensary integrations
- Advanced filtering options
- Notification system for price drops

### Medium Term
- Mobile app (React Native)
- Real-time price updates (WebSockets)
- Strain recommendations based on user history
- Integration with loyalty programs

### Long Term
- Multi-state expansion
- Machine learning for price prediction
- Retailer dashboard for inventory management
- Supply chain analytics for stakeholders
