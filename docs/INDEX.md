# Documentation Index - Utah Cannabis Aggregator

**Last Updated**: January 24, 2026
**Current Phase**: Phase 3 - Community Features
**Current Workflow**: 08 - User Authentication (✅ COMPLETE)

---

## Quick Navigation

### 🚀 Just Want to Get Started?
1. **Setup guide**: [GETTING_STARTED.md](./GETTING_STARTED.md)
2. **Run everything**: `scripts\start-dev.bat`
3. **Testing**: [TESTING.md](./TESTING.md)

### 🎯 Project Status
1. **Overview**: [../README.md](../README.md)
2. **Workflows**: [workflows/README.md](./workflows/README.md)
3. **Architecture**: [ARCHITECTURE.md](./ARCHITECTURE.md)

### 🔧 Scripts & Tools
- **Development scripts**: [../scripts/README.md](../scripts/README.md)
- **Topic guides**: [guides/README.md](./guides/README.md)

---

## Workflow Status

```
Phase 1: Foundation (Data Layer)
├── ✅ Workflow 01: Project Initialization
├── ✅ Workflow 02: Database Schema
├── ✅ Workflow 03: Scraper Foundation
└── ✅ Workflow 04: Admin Dashboard

Phase 2: Portal (Frontend MVP)
├── ✅ Workflow 05: Price Comparison Search
├── ✅ Workflow 06: Product Detail Pages
└── ✅ Workflow 07: Dispensary Pages

Phase 3: Community (User System)
├── ✅ Workflow 08: User Authentication
├── ⏳ Workflow 09: Review System
└── ⏳ Workflow 10: Stock Alerts & Notifications
```

---

## Document Library

### 📋 Core Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [../README.md](../README.md) | Project overview | Everyone |
| [GETTING_STARTED.md](./GETTING_STARTED.md) | Setup guide | Developers |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design | Developers |
| [prd.md](./prd.md) | Product requirements | Everyone |
| [../CLAUDE.md](../CLAUDE.md) | Claude Code guidelines | Developers |

### 🧪 Testing Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [TESTING.md](./TESTING.md) | Complete testing guide (unit, E2E, CI) | All developers |
| [WORKFLOW_08_TEST_PLAN.md](./WORKFLOW_08_TEST_PLAN.md) | Auth test procedures | QA |
| [API_TEST_PLAN.md](./API_TEST_PLAN.md) | Backend API tests | QA |

### 📂 Development Guides

| Guide | Purpose | Audience |
|-------|---------|----------|
| [guides/SCRAPING.md](./guides/SCRAPING.md) | Building dispensary scrapers | Backend |
| [guides/API_DISCOVERY.md](./guides/API_DISCOVERY.md) | Finding API endpoints | Backend |
| [guides/BACKEND_TROUBLESHOOTING.md](./guides/BACKEND_TROUBLESHOOTING.md) | Common issues & fixes | All |

### 🔐 Security & Configuration

| Document | Purpose |
|----------|---------|
| [SUPABASE_CREDENTIALS.md](./SUPABASE_CREDENTIALS.md) | Auth setup |
| [../backend/.env.example](../backend/.env.example) | Backend config |
| [../frontend/.env.example](../frontend/.env.example) | Frontend config |

### 📊 Workflow Documentation

| Workflow | Status | Details |
|----------|--------|---------|
| [01 - Project Init](./workflows/01_project_initialization_COMPLETED.md) | ✅ Done | Setup |
| [02 - Database](./workflows/02_database_schema_and_migrations_COMPLETED.md) | ✅ Done | Schema |
| [03 - Scrapers](./workflows/03_scraper_foundation_COMPLETED.md) | ✅ Done | Data collection |
| [04 - Admin](./workflows/04_admin_dashboard_cleanup_queue_COMPLETED.md) | ✅ Done | Admin tools |
| [05 - Search](./workflows/05_price_comparison_search_COMPLETED.md) | ✅ Done | Search UI |
| [06 - Products](./workflows/06_product_detail_pages_COMPLETED.md) | ✅ Done | Product pages |
| [07 - Dispensaries](./workflows/07_dispensary_pages_COMPLETED.md) | ✅ Done | Dispensary pages |
| [08 - Auth](./workflows/08_user_authentication.md) | ✅ Done | Authentication |
| [09 - Reviews](./workflows/09_review_system_dual_track.md) | ⏳ Next | Review system |
| [10 - Alerts](./workflows/10_stock_alerts_and_notifications.md) | ⏳ Next | Notifications |

### UX redesign and handoff

| Document | Purpose |
|----------|---------|
| [UX program](./ux/README.md) | Authority order and active pilot |
| [Design system](./ux/DESIGN-SYSTEM.md) | Production visual and interaction language |
| [Capability status](./ux/CAPABILITY-STATUS.md) | Supported, hidden, and future behavior |
| [Acceptance gates](./ux/ACCEPTANCE-GATES.md) | Required approval evidence |
| [Execution and handoff](./ux/EXECUTION-AND-HANDOFF.md) | Journey delivery workflow |

---

## File Structure

```
cannabis-compare/
├── README.md                     ← Project overview
├── CLAUDE.md                     ← AI assistant guidelines
├── GEMINI.md                     ← AI assistant guidelines
│
├── scripts/                      ← Development scripts
│   ├── README.md                 ← Script documentation
│   ├── start-dev.bat             ← Start both servers
│   ├── start-backend.bat
│   ├── start-frontend.bat
│   ├── install-deps.bat          ← Install dependencies
│   ├── fix-python313.bat
│   └── run-tests.bat
│
├── docs/
│   ├── INDEX.md                  ← This file (navigation hub)
│   ├── GETTING_STARTED.md        ← Setup guide
│   ├── ARCHITECTURE.md           ← System design
│   ├── TESTING.md                ← Complete testing guide
│   ├── prd.md                    ← Product requirements
│   │
│   ├── guides/                   ← Topic-specific guides
│   │   ├── SCRAPING.md
│   │   ├── API_DISCOVERY.md
│   │   └── BACKEND_TROUBLESHOOTING.md
│   │
│   ├── workflows/                ← Implementation guides
│   │   ├── README.md
│   │   └── [01-10 workflow files]
│   │
│   ├── phase-completion/         ← Phase summaries
│   │   └── [completion notes]
│   │
│   └── archive/                  ← Historical documentation
│       ├── workflow-logs/
│       ├── testing-summaries/
│       └── historical/
│
├── frontend/                     ← Next.js application
│   ├── app/
│   ├── components/
│   └── lib/
│
└── backend/                      ← FastAPI application
    ├── routers/
    ├── services/
    └── models.py
```

---

## Quick Links

### 🔗 URLs (Local Development)
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Login: http://localhost:3000/auth/login
- Profile: http://localhost:3000/profile

### ✅ Next Steps
1. Read: [GETTING_STARTED.md](./GETTING_STARTED.md)
2. Start: `scripts\start-dev.bat`
3. Test: [TESTING.md](./TESTING.md)
4. Explore: [workflows/README.md](./workflows/README.md)

---

**Last Updated**: January 24, 2026
**Version**: 2.0 (Reorganized)
