---
description: Create the initial Next.js + FastAPI + PostgreSQL workspace for Utah Cannabis Aggregator with Git, environment setup, and health checks.
auto_execution_mode: 1
---

## Steps

1. **Read Project Documentation**
   - Read `README.md`, `WORKSPACE_SETUP.md`, and `docs/ARCHITECTURE.md` to understand the project structure and tech stack.

2. **Initialize Git Repository**
   - Confirm git has been initialized: `git init`
   - Verify `.gitignore` exists and includes: `node_modules/`, `__pycache__/`, `.venv/`, `.env`, `.env.local`
   - Create initial commit documenting the workspace setup

3. **Backend Setup - FastAPI + SQLAlchemy**
   - Verify Python 3.10+ is installed
   - Virtual environment created: `python -m venv venv`
   - Dependencies installed from `backend/requirements.txt`
   - Verify `backend/main.py`, `backend/config.py`, `backend/models.py`, `backend/database.py` exist
   - Confirm Uvicorn server can start: `uvicorn main:app --reload` (should run on port 8000)

4. **Frontend Setup - Next.js + TypeScript + Tailwind**
   - Verify Node.js 18+ is installed
   - Dependencies installed: `npm install` in `frontend/` directory
   - Verify `frontend/next.config.js`, `frontend/tsconfig.json`, `frontend/tailwind.config.ts` exist
   - Verify Next.js app structure: `frontend/app/layout.tsx`, `frontend/app/page.tsx`, `frontend/app/globals.css`
   - Confirm dev server can start: `npm run dev` (should run on port 3000)

5. **Environment Configuration**
   - Backend `.env.example` exists with all required variables
   - Frontend `.env.example` exists with all required variables
   - Users copy `.env.example` to `.env` / `.env.local` and configure before running

6. **Verify Health Checks**
   - Backend health check: `curl http://localhost:8000/health` returns `{"status": "healthy", "version": "0.1.0"}`
   - Frontend loads without TypeScript errors: `npm run type-check` passes
   - Root API endpoint accessible: `http://localhost:8000/` returns API info

7. **Documentation Updates**
   - `README.md` contains quick start instructions
   - `backend/README.md` documents API setup
   - `frontend/README.md` documents frontend setup
   - `docs/ARCHITECTURE.md` explains system design

8. **Verify No Build Errors**
   - Backend starts without errors: `uvicorn main:app --reload`
   - Frontend starts without errors: `npm run dev`
   - No TypeScript errors in frontend: `npm run type-check`
   - API documentation accessible at `http://localhost:8000/docs`

## Success Criteria

- [x] Git repository initialized
- [x] Backend environment configured and running
- [x] Frontend environment configured and running
- [x] Health check endpoints responding correctly
- [x] Environment configuration templates created
- [x] Documentation up to date
- [x] No startup errors or TypeScript issues
