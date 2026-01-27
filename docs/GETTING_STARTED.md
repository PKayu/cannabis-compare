# Getting Started Guide

## Quick Setup

### Prerequisites
- Git
- Node.js 18+ (for frontend)
- Python 3.10+ (for backend)
- PostgreSQL 14+ or Supabase account

### Step 1: Clone & Initialize

```bash
cd "d:\Projects\cannabis compare"

# Initialize git (already done)
git init

# Create initial commit
git add .
git commit -m "Initial project setup"
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your database URL
# Example for local PostgreSQL:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/cannabis_aggregator

# Run the server
uvicorn main:app --reload
```

Server will be available at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Step 3: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
cp .env.example .env.local

# Edit .env.local if needed
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### Step 4: Verify Everything Works

1. **Backend Health Check**
   - Visit: `http://localhost:8000/health`
   - Should see: `{"status": "healthy", "version": "0.1.0"}`

2. **Frontend Home**
   - Visit: `http://localhost:3000`
   - Should see the home page with compliance banner

3. **API Documentation**
   - Visit: `http://localhost:8000/docs`
   - Interactive Swagger UI for testing endpoints

## Database Setup

### Using Supabase (Recommended)

1. Create account at https://supabase.com
2. Create new project
3. Get connection string from "Settings > Database > Connection String"
4. Add to backend/.env:
   ```
   DATABASE_URL=postgresql://user:password@project.supabase.co:5432/postgres
   ```

### Using Local PostgreSQL

1. Install PostgreSQL
2. Create database:
   ```sql
   CREATE DATABASE cannabis_aggregator;
   ```
3. Add to backend/.env:
   ```
   DATABASE_URL=postgresql://postgres:password@localhost:5432/cannabis_aggregator
   ```

## Project Structure Quick Reference

```
cannabis-compare/
├── frontend/              # Next.js application
│   ├── app/              # Pages and layouts
│   │   ├── layout.tsx    # Root layout (wrapped in Providers)
│   │   └── providers.tsx # Client providers (AuthProvider)
│   ├── components/       # Reusable components
│   ├── lib/              # Utilities
│   │   ├── api.ts        # Axios API client
│   │   ├── AuthContext.tsx # Global auth context
│   │   └── supabase.ts   # Supabase client
│   └── package.json
│
├── backend/              # FastAPI application
│   ├── main.py           # Entry point
│   ├── models.py         # Database models
│   ├── database.py       # Database connection
│   ├── config.py         # Configuration
│   ├── requirements.txt
│   └── prisma/          # Schema reference
│
├── docs/                 # Documentation
│   ├── ARCHITECTURE.md
│   └── GETTING_STARTED.md (this file)
│
└── README.md
```

## Development Workflow

### Making Changes

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** in either frontend or backend

3. **Test your changes**
   ```bash
   # Backend tests
   cd backend
   pytest

   # Frontend type check
   cd frontend
   npm run type-check
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: describe your changes"
   ```

5. **Push to repository**
   ```bash
   git push origin feature/your-feature-name
   ```

### Useful Commands

```bash
# Backend
cd backend
uvicorn main:app --reload        # Start with auto-reload
pytest                            # Run tests
pytest -v                         # Verbose test output
black .                           # Format code (install: pip install black)

# Frontend
cd frontend
npm run dev                       # Start dev server
npm run build                    # Build for production
npm run lint                     # Run ESLint
npm run type-check               # TypeScript type checking
```

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

## Troubleshooting

### "Cannot connect to database"
- Ensure PostgreSQL is running
- Check DATABASE_URL is correct
- Verify credentials
- Try connecting with psql:
  ```bash
  psql postgresql://user:password@localhost/cannabis_aggregator
  ```

### "Frontend can't reach backend"
- Ensure backend is running: `http://localhost:8000/health`
- Check NEXT_PUBLIC_API_URL in frontend/.env.local
- Check CORS settings in backend/main.py

### "Port already in use"
- Backend (8000): `lsof -ti :8000 | xargs kill -9`
- Frontend (3000): `lsof -ti :3000 | xargs kill -9`

### Python virtual environment issues
- Delete venv folder: `rm -r backend/venv`
- Recreate: `python -m venv backend/venv`
- Reactivate and reinstall

### npm issues
- Clear cache: `npm cache clean --force`
- Delete node_modules: `rm -r frontend/node_modules`
- Reinstall: `cd frontend && npm install`

## Next Development Steps

### Short Term (Phase 1-2)
1. [ ] Set up Alembic for database migrations
2. [ ] Create Pydantic schemas for validation
3. [ ] Implement user authentication endpoints
4. [ ] Create product management routers
5. [ ] Build basic web scrapers for dispensaries

### Medium Term (Phase 2-3)
1. [ ] Implement price comparison logic
2. [ ] Create review system API
3. [ ] Build frontend pages (products, search, details)
4. [ ] Add user authentication UI
5. [ ] Implement review submission forms

### Long Term
1. [ ] Optimize performance (caching, indexing)
2. [ ] Add admin dashboard
3. [ ] Implement real-time updates
4. [ ] Mobile app development
5. [ ] Advanced analytics

## Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/)

## Getting Help

- Check existing README files in frontend/ and backend/
- Review docs/ARCHITECTURE.md for system design
- Check FastAPI auto-docs: http://localhost:8000/docs
- Look at code comments and docstrings

## Code Style Guide

### Backend (Python)
- Follow PEP 8
- Use type hints
- Docstrings for functions
- Use SQLAlchemy ORM methods
- Format with black

### Frontend (React/TypeScript)
- Use functional components with hooks
- Props interface definitions
- JSX file extensions (.tsx)
- Use Tailwind classes
- Keep components small and focused

Good luck! 🚀
