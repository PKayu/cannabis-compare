# GEMINI.md

This file provides guidance to Gemini Code Assist when working with code in this repository.

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

### Commit Helper

When invoked with `/commit-helper`:
1. **Analyze Changes**: Review the current git diff or file modifications.
2. **Generate Message**: Create a commit message following Conventional Commits standards:
   - `feat:` New features
   - `fix:` Bug fixes
   - `docs:` Documentation changes
   - `style:` Formatting, missing semi-colons, etc.
   - `refactor:` Code change that neither fixes a bug nor adds a feature
   - `test:` Adding missing tests
   - `chore:` Maintenance tasks
3. **Output**: Provide the git commit command or just the message block.

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
Browser (React/Next.js) ←→ FastAPI Backend ←→ PostgreSQL (Supabase)
  - Port 3000            - Port 8000         - Managed service
  - Next.js App Router   - JWT Auth          - SQLAlchemy ORM
  - Tailwind CSS         - Pydantic validation
```

### Data Flow Pattern

The app follows three main data flows:

1. **Price Aggregation**: Web scrapers → Data normalization → Database → API → Frontend
2. **Reviews**: User form → Backend validation → Database → API queries → Display
3. **Search**: Frontend input → `/api/products/search` → Database → Results with filters

### Database Schema Key Points

Six interconnected models with these critical relationships:

- **Product** ↔ **Dispensary** (M:M junction via **Price** table)
- **Product** → **Review** (1:M, user-generated content)
- **Product** → **Brand** (M:1, cultivators)
- **User** → **Review** (1:M, tracks who posted reviews)

All models use UUID primary keys. Foreign key constraints cascade on delete.

### API Organization (Planned)

Router structure will be modular:
- `routers/auth.py` - Registration, login, JWT tokens
- `routers/products.py` - Browse, search, details
- `routers/prices.py` - Price comparison endpoints
- `routers/reviews.py` - CRUD operations with auth
- `routers/dispensaries.py` - Dispensary information

Frontend uses a centralized Axios wrapper (`lib/api.ts`) with interceptors for auth tokens and error handling.

## Development Commands

### Backend Setup & Running

```bash
# Initial setup (one time)
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with DATABASE_URL and SECRET_KEY

# Development server (auto-reload on changes)
uvicorn main:app --reload

# Run tests (when test suite exists)
pytest
pytest -v -s  # Verbose with print statements

# Type checking
mypy backend  # If mypy is added to requirements.txt
```

### Frontend Setup & Running

```bash
# Initial setup (one time)
cd frontend
npm install
cp .env.example .env.local

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

```bash
# Both .env files must be configured:
# backend/.env requires: DATABASE_URL, SECRET_KEY
# frontend/.env.local requires: NEXT_PUBLIC_API_URL (usually http://localhost:8000)

# Verify backend connectivity
curl http://localhost:8000/health  # Should return {"status": "healthy"}

# Access API docs (auto-generated)
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Git Workflow

```bash
# Create feature branches
git checkout -b feature/scraper-implementation
git checkout -b fix/auth-token-expiry

# Check changes before committing
git status
git diff

# Commit with clear messages
git commit -m "feat: implement iHeartJane scraper"
git commit -m "fix: handle database connection timeout"

# Standard flow
git add .
git commit -m "message"
git push origin branch-name
```

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
- **State Management**: Props/hooks for now (Context API ready in `lib/` if needed)

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
  main.py           → FastAPI app initialization, middleware, root routes
  config.py         → Environment variables and settings
  database.py       → SQLAlchemy engine, session, dependency injection
  models.py         → All SQLAlchemy ORM models (User, Product, etc.)
  routers/          → Modular endpoint groups (to be created)
  schemas/          → Pydantic models for request/response (to be created)
  services/         → Business logic, scrapers, utilities (to be created)
  tests/            → pytest test files (to be created)

frontend/
  app/
    layout.tsx      → Root layout with metadata
    page.tsx        → Home page
    globals.css     → Tailwind directives and global styles
  lib/
    api.ts          → Axios client with all endpoints + interceptors
  components/       → Reusable React components (to be created)
  public/           → Static assets
  tailwind.config.ts → Custom cannabis color palette (cannabis-50 to cannabis-900)
```

## Common Tasks & Patterns

### Adding a New API Endpoint

1. Create schema in `backend/schemas/` if needed (Pydantic model)
2. Create router in `backend/routers/` or add to existing
3. Use `@router.get/post/put/delete` decorator with path
4. Add `response_model=SchemaName` for validation
5. Use `db: Session = Depends(get_db)` to access database
6. Update `frontend/lib/api.ts` with corresponding call
7. Add endpoint to appropriate section in API methods object

### Adding a New Database Model

1. Define class in `backend/models.py` inheriting from `Base`
2. Use UUID for `id`, proper relationships with `relationship()`
3. Add indexes on frequently searched fields (`index=True`)
4. Update `backend/prisma/schema.prisma` for reference
5. Eventually: create Alembic migration

### Creating Frontend Components

1. File in `frontend/components/`, use `.tsx` extension
2. Define props interface at top of file
3. Export named function component (not default)
4. Use `api` from `lib/api.ts` for backend calls
5. Apply Tailwind classes for styling
6. Import and use in pages or other components

## Important Notes

### When Adding Features

- Check compliance: Does it need a disclaimer?
- Frontend must be mobile-responsive (check with DevTools)
- Update both `.env.example` files if new env vars are added
- Backend routes should have descriptive docstrings
- Frontend components should have TypeScript types
- Consider data normalization impact (different dispensaries use different naming)

### Testing Strategy

- Backend tests use pytest with `pytest-asyncio` for async functions. See `backend/tests/`.
- A comprehensive API test plan with 50+ test cases is available in `docs/API_TEST_PLAN.md`.
- Frontend tests will use Jest + React Testing Library (not yet set up).
- Run tests before committing: `pytest` or `npm test`.

A test data seeding script is available at `backend/seed_test_data.py`. To reset the database for a clean test run:
```bash
cd backend
# Clear existing data
python seed_test_data.py --clear
# Seed new data
python seed_test_data.py
```

### Deployment Notes

- Frontend deploys to Vercel (Next.js optimized)
- Backend deploys to cloud provider (AWS/Heroku/DigitalOcean)
- Database is managed Supabase PostgreSQL
- Environment variables differ between dev/prod — always check .env files

## Debugging Tips

### Backend Issues

```bash
# Check if server is running
curl http://localhost:8000/health

# Verify database connection (in Python shell)
from backend.database import SessionLocal
from backend.models import User
db = SessionLocal()
db.query(User).count()

# View all routes
# Visit http://localhost:8000/docs (Swagger UI)

# Enable logging (add to main.py or config.py)
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Frontend Issues

```bash
# Check API connectivity
# Open browser console: api.health() should resolve

# Verify environment variables
# Check frontend/.env.local has NEXT_PUBLIC_API_URL pointing to backend

# Clear Next.js cache if needed
rm -rf .next
npm run dev
```

## Database Migrations (Alembic)

Database migrations are managed with Alembic. Common commands are run from the `backend/` directory.

```bash
# Check current migration version
alembic current

# Show migration history
alembic history

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to a specific version
alembic downgrade <revision_id>
```
For more detailed scenarios like backups and full rollbacks, see `docs/database_rollback.md`.


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
- 02: Database Schema and Migrations (COMPLETED ✅)
- 03: Scraper Foundation (COMPLETED ✅)
- 04: Admin Dashboard Cleanup Queue (COMPLETED ✅)

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

## References

- **Database Schema**: `backend/prisma/schema.prisma` (reference) + `backend/models.py` (authoritative)
- **Architecture Details**: `docs/ARCHITECTURE.md`
- **Setup Guide**: `docs/GETTING_STARTED.md`
- **Project Metadata**: `.projectrc.json`
- **API Blueprint**: `backend/README.md` has full endpoint list
- **Development Workflows**: `docs/workflows/` - Step-by-step implementation guides