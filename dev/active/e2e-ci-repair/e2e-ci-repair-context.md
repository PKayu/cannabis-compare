# E2E CI repair context

- Created: 2026-09-26
- Last Updated: 2026-09-26
- Status: Complete

## Confirmed failures

- Recent PR and post-merge E2E jobs stop before Playwright because `.github/workflows/e2e-tests.yml` supplies a JWT secret shorter than the backend's 32-character startup minimum.
- The workflow installs frontend dependencies but invokes `npx playwright` from the repository root, where there is no package manifest. GitHub downloads an unpinned Playwright version instead of using `frontend/package-lock.json`.
- The legacy E2E suite lives at repository root while project documentation and package scripts describe it as frontend-owned.
- Legacy age-gate and homepage assertions target UI that no longer exists.
- Authentication and search scenarios depend on live external or unseeded services, so they are not deterministic.
- The PR comment step reads a `workflow_run` payload field during a `pull_request` event, always labels the run failed, claims artifacts exist when they may not, and creates a new notification comment every run.
- The focused Mountain Bloom UX suite is not run by the GitHub E2E workflow.

## Product and capability scope

- COMP-01: age/compliance treatment and shared public shell.
- DISC-01 through DISC-03: search entry, current query contract, and deterministic result states.
- AUTH-01: signed-out authentication entry without calling real Supabase services.
- No production UI or API contract changes are planned; this task repairs verification infrastructure.

## Working boundary

- Work is isolated in a managed worktree created from `origin/master`.
- The user's existing `feat/mountain-bloom-dispensaries` checkout and uncommitted changes remain untouched.

## Implemented decisions

- Frontend package scripts own both Playwright configurations and all browser tests.
- Journey and UX suites can start their own local server or target the CI production server through `E2E_EXTERNAL_SERVER` and `PLAYWRIGHT_BASE_URL`.
- Browser scenarios mock product and authentication boundaries while still exercising the real application UI and routing.
- CI uses Node 20, Python 3.11, the locked frontend dependencies, a valid test-only JWT secret, and an initialized SQLite database.
- GitHub job summaries and retained artifacts replace the event-incompatible PR-comment step.
- The general CI workflow YAML, stale frontend unit tests, and two stale backend assertions were repaired because they became visible once the workflows could run.

## Validation evidence

- Backend pytest: 213 passed on Python 3.12 using the CI environment contract.
- Backend SQLite schema initialization, application startup, and `/health`: passed.
- Frontend Jest: 39 passed.
- TypeScript type check: passed.
- ESLint: passed with five pre-existing React hook warnings.
- Next.js production build: passed.
- Journey Playwright suite: 14 passed against `next start`.
- UX acceptance Playwright suite: 14 passed against `next start`, covering 390, 768, 1280, and 1440 pixel widths.
- GitHub workflow YAML parse and `git diff --check`: passed.
