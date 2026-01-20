# Utah Cannabis Aggregator - Project Overview

## 🎯 Mission
Build a web platform to help Utah Medical Cannabis patients find the best prices across dispensaries and access community-driven reviews for strains and brands.

## 📊 Project Status
**Status**: Initial Setup Complete ✅
**Phase**: MVP - Phase 1 (Data Aggregation)
**Version**: 0.1.0
**Last Updated**: 2026-01-19

---

## 🏗️ Project Structure

```
cannabis-compare/
│
├── 📂 frontend/                 # Next.js React Application (Port 3000)
│   ├── 📂 app/                  # Next.js App Router pages
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Home page
│   │   └── globals.css          # Global styles
│   ├── 📂 components/           # Reusable components (to be built)
│   ├── 📂 lib/
│   │   └── api.ts               # Axios API client
│   ├── 📂 public/               # Static assets
│   ├── tailwind.config.ts       # Tailwind configuration
│   ├── tsconfig.json            # TypeScript config
│   ├── package.json             # Dependencies
│   ├── next.config.js           # Next.js config
│   ├── postcss.config.js        # PostCSS config
│   ├── .env.example             # Environment template
│   └── README.md                # Frontend guide
│
├── 📂 backend/                  # FastAPI Python Application (Port 8000)
│   ├── main.py                  # FastAPI entry point
│   ├── models.py                # SQLAlchemy ORM models
│   ├── database.py              # Database connection
│   ├── config.py                # Configuration
│   ├── requirements.txt          # Python dependencies
│   ├── 📂 prisma/
│   │   └── schema.prisma        # Database schema reference
│   ├── 📂 routers/              # API routers (to be built)
│   ├── 📂 services/             # Business logic (to be built)
│   ├── 📂 tests/                # Unit tests (to be built)
│   ├── .env.example             # Environment template
│   └── README.md                # Backend guide
│
├── 📂 docs/                     # Documentation
│   ├── ARCHITECTURE.md          # System design & data flow
│   ├── GETTING_STARTED.md       # Setup & development guide
│   └── prd.md                   # Original PRD
│
├── 📄 README.md                 # Project overview
├── 📄 WORKSPACE_SETUP.md        # Setup summary (THIS WAS DONE)
├── 📄 SETUP_CHECKLIST.md        # Development checklist
├── 📄 PROJECT_OVERVIEW.md       # This file
├── .projectrc.json              # Project metadata
├── .eslintrc.json               # ESLint config
├── .gitignore                   # Git ignore rules
└── .git/                        # Git repository

```

---

## 🛠️ Technology Stack

### Frontend Layer
```
┌─────────────────────────────────────────┐
│          React Components               │
│    TypeScript, Tailwind CSS             │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│        Next.js 14 (App Router)          │
│   SSR, Static Generation, SEO           │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  HTTP Client (Axios API Wrapper)        │
└────────────┬────────────────────────────┘
             │
         [Internet]
```

### Backend Layer
```
┌─────────────────────────────────────────┐
│          FastAPI Routes                 │
│  (REST Endpoints, WebSocket ready)      │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│     Pydantic Validation Schemas         │
│    (Request/Response validation)        │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│    SQLAlchemy ORM Layer                 │
│  (Database abstraction & queries)       │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│       PostgreSQL Database               │
│  (Supabase managed or self-hosted)      │
└─────────────────────────────────────────┘
```

---

## 📦 Dependencies

### Frontend (npm)
- **next**: 14.0+
- **react**: 18.2+
- **typescript**: 5.3+
- **tailwindcss**: 3.3+
- **axios**: 1.6+
- **@supabase/supabase-js**: 2.38+

### Backend (pip)
- **fastapi**: 0.104+
- **uvicorn**: 0.24+
- **sqlalchemy**: 2.0+
- **psycopg2-binary**: 2.9+
- **pydantic**: 2.5+
- **python-jose**: 3.3+
- **bcrypt**: 4.1+
- **requests**: 2.31+
- **beautifulsoup4**: 4.12+

---

## 💾 Database Schema

### 6 Core Models

```
┌─────────────┐
│    User     │  id, email, username, hashed_password
└──────┬──────┘
       │ (1:M)
       ├──────────────────────┐
       │                      │
   ┌───▼──────┐      ┌────────▼─────┐
   │ Review   │      │  Dispensary  │
   │(1-5 star)│      │  (Location)  │
   └──────────┘      └────────┬─────┘
                              │
        ┌─────────────────────┤
        │ (M:M via Price)     │
        │                     │
    ┌───▼──────┐      ┌───────▼──────┐
    │ Product  │◄─────┤    Brand     │
    │(Strains) │(1:M) │(Cultivator)  │
    └──────────┘      └──────────────┘
        ▲
        │
        │ (1:M)
        │
    ┌───┴──────┐
    │  Price   │  (product_id, dispensary_id, amount)
    │(Junction)│
    └──────────┘
```

### Key Relationships
- **User** → Reviews (1:M)
- **Product** → Reviews (1:M)
- **Brand** → Products (1:M)
- **Product** ↔ Dispensary via Price (M:M)

---

## 🚀 Development Phases

### Phase 1: Data Ingestion & Backend API
**Duration**: Foundation phase
**Focus**: Data aggregation and API

**Tasks**:
- [ ] Set up database migrations (Alembic)
- [ ] Implement user authentication
- [ ] Create web scrapers (3 dispensaries)
- [ ] Build data normalization engine
- [ ] Implement price aggregation API
- [ ] Create product search endpoints

**Deliverables**: Working backend API with data

---

### Phase 2: Frontend MVP
**Duration**: MVP UI phase
**Focus**: User interface and basic features

**Tasks**:
- [ ] Build product search/browse pages
- [ ] Implement price comparison UI
- [ ] Create dispensary listing
- [ ] Add filtering and sorting
- [ ] Mobile optimization (80% users)
- [ ] Performance optimization

**Deliverables**: Functional UI for price comparison

---

### Phase 3: User System & Reviews
**Duration**: Community features phase
**Focus**: Authentication and social features

**Tasks**:
- [ ] User registration/login UI
- [ ] Create user profile pages
- [ ] Build review submission system
- [ ] Implement rating system
- [ ] Add upvoting functionality
- [ ] Moderation tools

**Deliverables**: Complete user system with reviews

---

## 📊 Data Flow Examples

### Example 1: Search for Products
```
User enters "Gorilla Glue" in search bar
    ↓
Frontend sends: GET /api/products/search?q=Gorilla+Glue
    ↓
Backend queries PostgreSQL database
    ↓
Returns matching products (list)
    ↓
Frontend displays results with filters
    ↓
User clicks product → Shows price comparison
```

### Example 2: Price Aggregation
```
Scraper runs (scheduled job)
    ↓
Fetches data from Dispensary A, B, C
    ↓
Normalizes product names
    ↓
Updates Price table with latest data
    ↓
Frontend queries GET /api/prices/compare?product_id=123
    ↓
Backend joins Product → Price ← Dispensary
    ↓
Returns prices from all dispensaries
    ↓
Frontend displays comparison (sorted by price)
```

### Example 3: User Review
```
User writes review and submits
    ↓
Frontend sends: POST /api/reviews
    ↓
Backend validates with Pydantic
    ↓
Stores in database (Review table)
    ↓
GET /api/products/{id}/reviews fetches reviews
    ↓
Frontend displays reviews with ratings
    ↓
User can upvote helpful reviews
```

---

## 🎨 Design Features

### Compliance
- ✅ Disclaimer on every page
- ✅ Age verification gate (future)
- ✅ Non-commercial (informational)
- ✅ Clear disclaimers

### Performance
- ⏱️ Target: <200ms search response
- 📱 Mobile-first design (80% mobile)
- 🔍 SEO optimized (Next.js SSR)
- ⚡ Async backend processing

### Customization
- 🎨 Custom cannabis color palette
  - Primary: `#52c952` (cannabis-500)
  - Dark: `#1f4620` (cannabis-900)
- 📱 Responsive Tailwind grid system
- 🌙 Ready for dark mode (future)

---

## 🔐 Security Features

### Authentication
- ✅ JWT-based auth tokens
- ✅ bcrypt password hashing
- ✅ Token expiration (30 minutes)
- ✅ Refresh token strategy (future)

### Data Validation
- ✅ Pydantic request validation
- ✅ SQLAlchemy SQL injection prevention
- ✅ CORS configured
- ✅ Input sanitization (future)

### Compliance & Privacy
- ✅ HTTPS-only in production
- ✅ No sensitive data in logs
- ✅ Environment variables for secrets
- ✅ Privacy policy (to be written)

---

## 📈 Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Search Response | <200ms | ⏳ To be tested |
| Page Load Time | <2s | ⏳ To be tested |
| Mobile Score | >80 | ⏳ To be tested |
| SEO Score | >90 | ⏳ To be tested |
| API Uptime | 99.9% | ⏳ To be tested |

---

## 🚀 Quick Start

### 1. Install & Setup (5 min)
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

### 2. Configure (5 min)
```bash
# Backend
cp .env.example .env
# Edit .env with your PostgreSQL URL

# Frontend
cp .env.example .env.local
```

### 3. Run (2 min)
```bash
# Terminal 1
cd backend && uvicorn main:app --reload

# Terminal 2
cd frontend && npm run dev
```

### 4. Verify (2 min)
- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

**Total Setup Time**: ~14 minutes ⏱️

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview |
| [WORKSPACE_SETUP.md](WORKSPACE_SETUP.md) | What was set up |
| [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md) | Development checklist |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design details |
| [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) | Development guide |
| [frontend/README.md](frontend/README.md) | Frontend guide |
| [backend/README.md](backend/README.md) | Backend guide |

---

## ✅ What's Ready

### Infrastructure
- ✅ Git repository
- ✅ Project directories
- ✅ Package managers (npm + pip)
- ✅ Configuration files

### Backend
- ✅ FastAPI server
- ✅ SQLAlchemy models
- ✅ Database connection
- ✅ Health check endpoint
- ✅ Configuration management

### Frontend
- ✅ Next.js project
- ✅ Tailwind CSS
- ✅ TypeScript setup
- ✅ API client library
- ✅ Home page template

### Documentation
- ✅ 7 comprehensive guides
- ✅ Architecture documentation
- ✅ Getting started guide
- ✅ Development checklist

---

## ⏳ What's Next

### Immediate (Week 1)
1. Install all dependencies
2. Create PostgreSQL database
3. Test setup with health checks
4. Make first commits

### Short Term (Weeks 2-4)
1. Set up database migrations
2. Create first web scraper
3. Build authentication system
4. Implement product search

### Medium Term (Weeks 5-8)
1. Build frontend pages
2. Implement price comparison
3. Create review system
4. Add user profiles

### Long Term (Weeks 9+)
1. Performance optimization
2. Advanced features
3. Mobile app (React Native)
4. Multi-state expansion

---

## 🎯 Success Criteria

### MVP Completion
- [ ] 3 dispensaries scraped successfully
- [ ] Product search working (<200ms)
- [ ] Price comparison UI functional
- [ ] User reviews system active
- [ ] Mobile responsive (80%+ score)
- [ ] Zero critical bugs

### Launch Readiness
- [ ] All compliance disclaimers in place
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Security audit completed
- [ ] Performance tested
- [ ] Load testing passed

---

## 👥 Team Coordination

### Git Workflow
1. Create feature branch: `feature/name`
2. Make changes and test
3. Commit with clear messages
4. Push to repository
5. Create pull request for review

### Branch Naming
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring

### Commit Messages
```
feat: add product search endpoint
fix: handle database connection errors
docs: update API documentation
refactor: simplify price comparison logic
```

---

## 📞 Support & Resources

### Getting Help
- 📖 Check **docs/** directory
- 🔍 Review README files in each directory
- 🐛 Check for similar issues in git history
- 📝 Read code comments and docstrings

### External Resources
- [Next.js Docs](https://nextjs.org/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [PostgreSQL](https://www.postgresql.org/)

---

## 📊 Project Statistics

| Metric | Count |
|--------|-------|
| **Total Files Created** | 25+ |
| **Lines of Code** | 2000+ |
| **Configuration Files** | 8 |
| **Documentation Files** | 7 |
| **Database Models** | 6 |
| **API Endpoints (Base)** | 1 |
| **Frontend Components (Base)** | 1 |
| **Development Hours Invested** | ~2h initial setup |

---

## 🎉 Conclusion

Your Utah Cannabis Aggregator workspace is fully initialized and ready for development!

**Current Status**: ✅ Ready to Code
**Next Step**: Follow [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md) to begin development
**Questions**: Review [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)

---

**Project Created**: 2026-01-19
**Last Updated**: 2026-01-19
**Status**: MVP Phase 1 Ready 🚀
