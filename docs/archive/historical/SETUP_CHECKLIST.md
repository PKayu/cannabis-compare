# Setup Checklist

## ✅ Workspace Initialization Complete

Use this checklist to verify your setup and track next steps.

### Core Setup (COMPLETE)

- [x] Git repository initialized
- [x] Project directory structure created
- [x] Root-level documentation created
- [x] Backend project initialized
- [x] Frontend project initialized
- [x] Database schema defined

### Backend Setup (READY)

- [x] FastAPI project structure
- [x] SQLAlchemy models defined (User, Product, Brand, Dispensary, Price, Review)
- [x] Database connection setup
- [x] Configuration management (config.py)
- [x] Environment template (.env.example)
- [x] Requirements.txt with all dependencies
- [x] Health check endpoint
- [x] Documentation (README.md + ARCHITECTURE.md)
- [ ] **TODO**: Database migrations (Alembic)
- [ ] **TODO**: Authentication endpoints
- [ ] **TODO**: Product routers
- [ ] **TODO**: Review system routers
- [ ] **TODO**: Web scrapers

### Frontend Setup (READY)

- [x] Next.js project scaffolded
- [x] TypeScript configured
- [x] Tailwind CSS setup with custom cannabis theme
- [x] API client library (Axios wrapper)
- [x] Home page template with compliance banner
- [x] Global styles and layout
- [x] Environment template (.env.example)
- [x] ESLint configuration
- [x] Documentation (README.md + ARCHITECTURE.md)
- [ ] **TODO**: Products page
- [ ] **TODO**: Product details page
- [ ] **TODO**: Search and filtering
- [ ] **TODO**: Authentication pages
- [ ] **TODO**: Review system UI

### Documentation (COMPLETE)

- [x] README.md - Project overview
- [x] WORKSPACE_SETUP.md - Initialization summary
- [x] docs/ARCHITECTURE.md - System design
- [x] docs/GETTING_STARTED.md - Development guide
- [x] frontend/README.md - Frontend guide
- [x] backend/README.md - Backend guide
- [x] .projectrc.json - Project configuration

---

## 🚀 Before You Start Coding

### Step 1: Install Dependencies
```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Step 2: Configure Environment
```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your DATABASE_URL

# Frontend
cd frontend
cp .env.example .env.local
# Update if using Supabase
```

### Step 3: Database Setup
- [ ] Create PostgreSQL database (local or Supabase)
- [ ] Get connection string
- [ ] Add to backend/.env as DATABASE_URL
- [ ] Test connection from backend

### Step 4: Verify Installation
```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload
# Visit http://localhost:8000/health

# Terminal 2: Frontend
cd frontend
npm run dev
# Visit http://localhost:3000
```

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Health endpoint responding
- [ ] Home page loads without errors

---

## 📋 Development Phases

### Phase 1: Data Ingestion & Backend (Next)

**Objectives**: Set up data scraping pipeline

**Tasks**:
- [ ] Set up Alembic for migrations
- [ ] Create initial database schema
- [ ] Implement authentication endpoints
- [ ] Build first web scraper (1 dispensary)
- [ ] Create data normalization logic
- [ ] Set up price aggregation

**Deliverables**:
- [ ] Scrapers for 3 major Utah dispensaries
- [ ] Normalized product database
- [ ] Price comparison endpoints
- [ ] Authentication API

---

### Phase 2: Frontend MVP

**Objectives**: Build basic UI for price comparison

**Tasks**:
- [ ] Create product browse page
- [ ] Implement search functionality
- [ ] Build price comparison view
- [ ] Add filtering and sorting
- [ ] Dispensary listing page
- [ ] Mobile optimization

**Deliverables**:
- [ ] Functional product search
- [ ] Price comparison interface
- [ ] Mobile-responsive design
- [ ] Real-time price updates

---

### Phase 3: User System & Reviews

**Objectives**: Add community features

**Tasks**:
- [ ] Create authentication pages (login/register)
- [ ] Build review submission form
- [ ] Create user profile page
- [ ] Implement upvoting system
- [ ] Add moderation tools
- [ ] User email notifications

**Deliverables**:
- [ ] Full authentication system
- [ ] Review and rating system
- [ ] User profiles
- [ ] Community features

---

## 📁 Key Files Reference

| File/Directory | Purpose |
|---|---|
| `backend/main.py` | FastAPI entry point |
| `backend/models.py` | Database ORM models |
| `backend/config.py` | Configuration management |
| `backend/database.py` | Database connection |
| `frontend/app/page.tsx` | Home page |
| `frontend/lib/api.ts` | API client |
| `docs/ARCHITECTURE.md` | System design |
| `docs/GETTING_STARTED.md` | Setup guide |

---

## 🛠️ Common Commands

### Backend
```bash
cd backend
source venv/bin/activate          # Activate venv (Windows: venv\Scripts\activate)
uvicorn main:app --reload         # Start dev server
pytest                            # Run tests
pip freeze > requirements.txt     # Update dependencies
```

### Frontend
```bash
cd frontend
npm run dev                        # Start dev server
npm run build                      # Build for production
npm run type-check                 # Check TypeScript types
npm run lint                       # Run ESLint
```

### Git
```bash
git status                         # Check changes
git add .                          # Stage all changes
git commit -m "message"            # Create commit
git branch feature/name            # Create feature branch
git push origin feature/name       # Push to remote
```

---

## 🔍 Testing & Verification

### Backend API Testing
- [ ] Visit http://localhost:8000/docs for Swagger UI
- [ ] Test health endpoint: http://localhost:8000/health
- [ ] Verify database connection in logs

### Frontend Testing
- [ ] Home page loads
- [ ] Compliance banner visible
- [ ] Responsive on mobile (F12 DevTools)
- [ ] API client can reach backend

### Database Testing
- [ ] Connect with PostgreSQL client
- [ ] Verify tables created (once migrations run)
- [ ] Check connection pooling works

---

## 📞 Troubleshooting

### Port Already in Use
```bash
# macOS/Linux
lsof -ti :8000 | xargs kill -9    # Kill port 8000
lsof -ti :3000 | xargs kill -9    # Kill port 3000

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Database Connection Failed
- [ ] Verify PostgreSQL is running
- [ ] Check DATABASE_URL format
- [ ] Test with psql: `psql postgresql://user:pass@localhost/db`

### npm/pip Package Issues
```bash
# Frontend
rm -rf node_modules package-lock.json
npm install

# Backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📚 Additional Resources

- **Next.js**: https://nextjs.org/docs
- **FastAPI**: https://fastapi.tiangolo.com/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Pydantic**: https://docs.pydantic.dev/

---

## ✨ Next Immediate Actions

1. **Install dependencies** (backend + frontend)
2. **Set up database** (create PostgreSQL database)
3. **Configure .env files** (with database URL)
4. **Run development servers** (backend + frontend)
5. **Verify everything works** (health check + home page)
6. **Make first commit** (`git commit -m "Initial setup complete"`)
7. **Start Phase 1**: Begin building first web scraper

---

**Status**: Ready for Development 🚀

You now have a complete, modern workspace for the Utah Cannabis Aggregator project!
Begin with the setup instructions above, then proceed to Phase 1 (Data Ingestion).

Happy coding! 🎉
