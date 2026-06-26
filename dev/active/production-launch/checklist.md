# Production Launch Checklist

**App:** Cannabis Compare (Utah Cannabis Aggregator)  
**Stack:** Next.js 14 (Vercel) + FastAPI (Railway) + Supabase  
**Status:** In progress

Check off each item as it's completed. Add `— done YYYY-MM-DD` after the checkbox when closing it.

---

## Phase 1 — Critical Blockers (Must fix before any public URL)

### Admin Authentication
- [x] `backend/routers/admin_flags.py` — replace placeholder `get_current_user()` with real JWT auth from `routers/auth.py` — done 2026-04-10
- [x] `backend/routers/admin_flags.py` — `verify_admin` added as router-level dependency — done 2026-04-10
- [x] `backend/routers/admin_scrapers.py` — `verify_admin` added as router-level dependency — done 2026-04-10
- [x] `backend/models.py` — added `is_admin: bool = False` column to `User` — done 2026-04-10
- [x] `backend/alembic/versions/20260410_000001_add_is_admin_to_users.py` — migration created — done 2026-04-10
- [ ] Set at least one user as admin in production DB after deploy (`UPDATE users SET is_admin=true WHERE email='your@email.com'`)

### JWT / Secret Key
- [x] `backend/config.py` — `secret_key` default changed to `""` — done 2026-04-10
- [x] `backend/main.py` — startup validation: warns in dev, raises in prod if `SECRET_KEY` unset — done 2026-04-10
- [x] Add `SECRET_KEY=<generated>` to `backend/.env` — done 2026-06-25

### Debug Mode
- [x] `backend/config.py` — changed `debug: bool = True` → `debug: bool = False` — done 2026-04-10
- [x] `DEBUG=true` already present in `backend/.env` — confirmed 2026-06-25

### CORS
- [x] `backend/main.py` — reads `ALLOWED_ORIGINS` env var (comma-separated); falls back to localhost defaults — done 2026-04-10
- [x] `allow_methods` restricted to explicit list — done 2026-04-10
- [x] `allow_headers` restricted to explicit list — done 2026-04-10
- [x] `backend/.env.example` — documented `ALLOWED_ORIGINS` variable — done 2026-04-10

### Docker / Dev vs Prod
- [x] `frontend/Dockerfile` — multi-stage build, production `node server.js` entry — done 2026-04-10
- [x] `docker-compose.yml` — `--reload` kept for dev; `docker-compose.prod.yml` uses `--workers 2` (no reload) — done 2026-06-25
- [x] `docker-compose.prod.yml` created (no volumes, no reload, `DEBUG=false`) — done 2026-06-25
- [x] `POSTGRES_PASSWORD` in `docker-compose.yml` moved to `${POSTGRES_PASSWORD:-cannabis_password}` env var — done 2026-06-25

---

## Phase 2 — Security Hardening (Before launch)

### Rate Limiting
- [x] `slowapi>=0.1.9` added to `backend/requirements.txt` — done 2026-04-10
- [x] `backend/main.py` — Limiter configured (IP-based), wired to app state — done 2026-04-10
- [x] `backend/routers/auth.py` — `/api/auth/login` limited to 10/minute — done 2026-04-10
- [ ] Test: 11 rapid POSTs to `/api/auth/login` → 11th must return 429

### Security Headers (Frontend)
- [x] `frontend/next.config.js` — `headers()` added with X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, CSP — done 2026-04-10

### Error Handling
- [x] `backend/main.py` — `@app.exception_handler(Exception)` returning generic 500 — done 2026-04-10

### Compliance Pages
- [x] `frontend/app/terms/page.tsx` — Terms of Service page created — done 2026-04-10
- [x] `frontend/app/privacy/page.tsx` — Privacy Policy page created — done 2026-04-10
- [x] Terms + privacy links in `frontend/components/Footer.tsx` — confirmed 2026-06-25

### robots.txt
- [x] `frontend/public/robots.txt` — created, disallows `/api/`, `/admin/` — done 2026-04-10

---

## Phase 3 — Railway Backend Deployment

- [x] `railway.json` created at project root (Dockerfile deploy, healthcheck at /health) — done 2026-06-25
- [x] `backend/.env.production.example` created with all required vars + notes — done 2026-06-25
- [ ] Create Railway account / project at railway.app
- [ ] Connect GitHub repo to Railway (auto-deploy on push to master)
- [ ] Set all env vars in Railway dashboard (see `backend/.env.production.example`):
  - [ ] `DATABASE_URL` = `postgresql://postgres:{pw}@{ref}.supabase.co:5432/postgres` (use port 5432, not 6543 — SQLAlchemy needs persistent connections)
  - [ ] `SUPABASE_URL`
  - [ ] `SUPABASE_SERVICE_KEY`
  - [ ] `SECRET_KEY` (copy from backend/.env)
  - [ ] `ALLOWED_ORIGINS` (Vercel URL — set after Phase 4)
  - [ ] `DEBUG=false`
  - [ ] `SENDGRID_API_KEY`
- [ ] Trigger first deploy — watch build logs for Playwright install (takes ~5 min)
- [ ] Run `alembic upgrade head` against production Supabase DB
  - Via Railway CLI: `railway run alembic upgrade head`
  - Or add startup migration (run_server.py already auto-migrates on startup)
- [ ] Set admin user: `UPDATE users SET is_admin=true WHERE email='danworwood@gmail.com'` (in Supabase table editor)
- [ ] Verify `/health` returns 200: `curl https://<railway-url>/health`
- [ ] Verify admin endpoints require auth: `curl https://<railway-url>/api/admin/scrapers` → must be 401

---

## Phase 4 — Vercel Frontend Deployment

- [ ] Import repo to Vercel (vercel.com → Add New Project)
- [ ] Set build settings: Framework = Next.js, Root = `frontend/`
- [ ] Set env vars in Vercel dashboard:
  - [ ] `NEXT_PUBLIC_API_URL` = Railway backend HTTPS URL
  - [ ] `NEXT_PUBLIC_SUPABASE_URL`
  - [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- [ ] Deploy and get preview URL
- [ ] Update `ALLOWED_ORIGINS` in Railway to include Vercel URL
- [ ] Set custom domain (if applicable)

---

## Phase 5 — Verification

- [ ] `/health` returns `{"status":"healthy"}` from Railway URL
- [ ] Auth: POST `/api/auth/login` with bad creds → 401 (not stack trace)
- [ ] Admin: GET `/api/admin/scrapers` without token → 401
- [ ] Rate limit: 11 rapid POSTs to `/api/auth/login` → 429 on 11th
- [ ] Security headers: `curl -I https://<vercel-url>` → see `x-frame-options`, `x-content-type-options`
- [ ] Or use https://securityheaders.com to scan
- [ ] Product search works end-to-end
- [ ] Age gate appears on first visit
- [ ] Compliance disclaimer is visible
- [ ] Admin scraper trigger works (authenticated)
- [ ] Scheduler running (check scraper run history after ~2 hours)

---

## Phase 6 — Medium Priority (Week 2)

- [ ] Add `is_admin` admin panel in frontend (or manage via DB directly initially)
- [ ] Structured JSON logging — `backend/main.py`
- [ ] Scraper failure alerting (email/Slack on repeated failures)
- [ ] Sitemap.xml for SEO
- [ ] Supabase row-level security audit (ensure users can only read their own watchlist/reviews)
- [ ] Rotate Supabase service key if it was ever committed to git history

---

## Notes

**Hosting decision:** Vercel (frontend) + Railway (backend + scrapers) + Supabase (DB/auth — already set up)

**Why Railway for backend:** Playwright requires a Chromium binary — serverless platforms (Lambda, Vercel Functions) can't run it. Railway runs the existing Dockerfile directly.

**Why not Render free tier:** Spins down after 15 min inactivity, which breaks APScheduler.

**Admin access (quick approach):** Until a proper admin UI exists, set `is_admin=true` directly in Supabase table editor for your account after first login.
