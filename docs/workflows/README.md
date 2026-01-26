# Utah Cannabis Aggregator - Development Workflows

This directory contains step-by-step workflow documentation for implementing the Utah Cannabis Aggregator project. Each workflow breaks down a major feature or phase into actionable, executable steps.

## Overview

All 10 workflows are organized in sequential order across 3 phases:

### Phase 1: Foundation (Data Aggregation) - Workflows 01-04
Focus: Building the data infrastructure and admin tools

- **Workflow 01**: Project Initialization (COMPLETED) ✅
- **Workflow 02**: Database Schema and Migrations (COMPLETED) ✅
- **Workflow 03**: Scraper Foundation (COMPLETED) ✅
- **Workflow 04**: Admin Dashboard Cleanup Queue (COMPLETED) ✅

### Phase 2: Portal (Frontend MVP) - Workflows 05-07
Focus: Building the public-facing search and product pages

- **Workflow 05**: Price Comparison Search (COMPLETED) ✅
- **Workflow 06**: Product Detail Pages (COMPLETED) ✅
- **Workflow 07**: Dispensary Pages (COMPLETED) ✅

### Phase 3: Community (User System & Reviews) - Workflows 08-10
Focus: Enabling user engagement and community features

- **Workflow 08**: User Authentication (COMPLETED) ✅
- **Workflow 09**: Review System Dual-Track (COMPLETED) ✅
  - [x] Intention tag enums (Medical + Mood/Wellness)
  - [x] Review model with dual-track fields
  - [x] Review submission/update/delete endpoints
  - [x] Review filtering by intention (type and tag)
  - [x] Review sorting (recent, helpful, rating_high)
  - [x] ReviewForm and ReviewsSection components
  - [x] Star ratings (Effects, Taste, Value)
  - [x] Batch tracking
  - [x] Review upvoting
  - [x] Integration into product pages
- **Workflow 10**: Stock Alerts and Notifications (COMPLETED) ✅
  - [x] 3 database models (Watchlist, PriceAlert, NotificationPreference)
  - [x] Watchlist API endpoints (add, remove, list, check)
  - [x] Notification preferences endpoints (get, update)
  - [x] Stock detector service with 24-hour deduplication
  - [x] Price detector service with configurable thresholds
  - [x] SendGrid email service with HTML templates
  - [x] Alert scheduler (runs every 1-2 hours)
  - [x] WatchlistButton component
  - [x] Watchlist page at /watchlist
  - [x] Notification preferences page
  - [x] Navigation with watchlist link and badge
  - [x] Product page integration

## How to Use These Workflows

### 1. Start with Workflow 01
Review the initialization workflow to understand the project structure and how to get the development environment running.

### 2. Read the PRD
Each workflow references sections of the PRD (`docs/prd.md`). Read the relevant sections before starting a workflow.

### 3. Follow Steps Sequentially
Each workflow is broken into numbered steps. Follow them in order:
- **Steps with code**: Copy provided code examples into your codebase
- **Steps with commands**: Run provided bash commands
- **Verification steps**: Test using provided verification commands

### 4. Reference the Architecture
Before working on a workflow, review `docs/ARCHITECTURE.md` to understand:
- How the feature fits into the system
- Key data flows
- Database relationships
- API contract patterns

### 5. Mark Completion
After completing each workflow's success criteria, move on to the next workflow.

## Workflow Structure

Each workflow contains:

```
---
description: One-line summary
auto_execution_mode: 1
---

## Context
Background on the feature, PRD references, requirements

## Steps
1. Numbered, action-oriented steps
2. Code examples where needed
3. Verification commands
4. ...

## Success Criteria
- [ ] Checklist of acceptance criteria
```

## Key Patterns Across Workflows

### Backend (Python/FastAPI)
All backend workflows follow this pattern:

1. **Models**: Add SQLAlchemy model to `backend/models.py`
2. **Routers**: Create API endpoints in `backend/routers/`
3. **Services**: Add business logic in `backend/services/`
4. **Database**: Update migrations or schema
5. **Tests**: Add tests in `backend/tests/`

### Frontend (Next.js/TypeScript)
All frontend workflows follow this pattern:

1. **Pages**: Create page components in `frontend/app/`
2. **Components**: Create reusable components in `frontend/components/`
3. **API Calls**: Use `frontend/lib/api.ts` client
4. **Styling**: Use Tailwind CSS utilities
5. **Types**: Define TypeScript interfaces for API responses

## Development Environment Checklist

Before starting workflows, ensure:

- [ ] Backend running: `uvicorn main:app --reload` (port 8000)
- [ ] Frontend running: `npm run dev` (port 3000)
- [ ] Database configured: PostgreSQL with DATABASE_URL in `.env`
- [ ] Environment variables: `.env` and `.env.local` configured
- [ ] Git initialized and `.gitignore` in place
- [ ] CLAUDE.md reviewed for architecture overview

## Time Estimates

Approximate time per workflow (experienced developer):

| Workflow | Task | Estimate |
|----------|------|----------|
| 01 | Project Init (Already Complete) | ✅ Done |
| 02 | Database Schema | 1-2 days |
| 03 | Scraper Foundation | 3-4 days |
| 04 | Admin Dashboard | 2-3 days |
| 05 | Search/Comparison | 2-3 days |
| 06 | Product Details | 1-2 days |
| 07 | Dispensary Pages | 1-2 days |
| 08 | Authentication | 2-3 days |
| 09 | Review System | 3-4 days |
| 10 | Alerts/Notifications | 1-2 days |
| **Total** | **All Phases** | **16-25 days** |

## Important Notes

### Compliance
- **Every page must display a compliance disclaimer**
- See `frontend/app/globals.css` for banner styling
- All functionality is informational only - no transactions

### Performance Targets
- Search endpoint: <200ms response time
- Frontend load: <2 seconds
- Database queries: Use proper indexing
- Mobile: 80%+ responsive design score

### Data Quality
- Scrapers must achieve >80% auto-merge rate
- Confidence-based normalization (>90%/60-90%/<60%)
- Admin dashboard for manual resolution
- Outlier detection for price anomalies

### Mobile First
- 80% of users access via mobile at dispensaries
- Responsive design required on all pages
- Touch-friendly buttons (min 44px)
- Fast load times critical

## Troubleshooting

### If a workflow fails midway:

1. **Check success criteria**: Have all earlier steps been completed?
2. **Review code examples**: Are code snippets correctly placed?
3. **Test the API**: Use Swagger UI at `http://localhost:8000/docs`
4. **Check logs**: Look for error messages in terminal
5. **Database issues**: Verify migrations ran with `alembic current`

### Common Issues

| Issue | Solution |
|-------|----------|
| Import errors | Ensure models are imported in `__init__.py` |
| Port already in use | Kill process: `lsof -ti :8000 \| xargs kill -9` |
| Database connection failed | Check DATABASE_URL in `.env` |
| TypeScript errors | Run `npm run type-check` to see all errors |
| Authentication failing | Verify Supabase credentials in `.env.local` |

## Next Steps After Workflows

Once all 10 workflows are complete:

1. **Testing**: Add comprehensive test coverage
2. **Documentation**: Update API docs and deployment guides
3. **Performance**: Optimize database queries and frontend
4. **Monitoring**: Set up logging and error tracking
5. **Deployment**: Deploy to staging then production

## Resources

- [Project README](../README.md) - Project overview
- [Architecture](../ARCHITECTURE.md) - System design
- [PRD](../prd.md) - Product requirements
- [Getting Started](../GETTING_STARTED.md) - Setup guide
- [CLAUDE.md](../../CLAUDE.md) - Claude Code guidance

## Questions?

Refer to the appropriate workflow document or the main architecture documentation. Each workflow is designed to be self-contained with all necessary information included.

---

**Current Status**: ALL PHASES COMPLETE ✅ - All 10 Workflows DONE! 🎉
**Last Updated**: January 25, 2026
**Version**: 2.0 (MVP Complete)
