# E2E CI repair plan

- Created: 2026-09-26
- Last Updated: 2026-09-26
- Status: Complete

## Objective

Restore a deterministic GitHub Actions E2E gate that starts the backend securely, uses the repository-pinned Playwright version, exercises current patient-facing behavior, reports failures truthfully, and avoids duplicate PR-comment notifications.

## Plan

1. Repair CI runtime configuration: Node version, test-only JWT secret, dependency working directory, browser installation, database initialization, and server lifecycle.
2. Consolidate the legacy root Playwright suite into the frontend test tree and align it with the current Mountain Bloom shell, age gate, authentication boundary, and API contracts.
3. Make third-party and API-dependent scenarios deterministic through Playwright route fixtures rather than live Supabase or unseeded database state.
4. Run the legacy journey suite and the focused UX suite in CI with compatible browser settings.
5. Replace misleading repeated PR comments with accurate GitHub job summaries and artifact uploads.
6. Update testing documentation and record validation evidence.

## Validation

- Workflow syntax/load inspection
- Frontend TypeScript type check
- Frontend lint
- Frontend Jest suite
- Production build
- Playwright legacy journey suite
- Playwright focused UX suite
