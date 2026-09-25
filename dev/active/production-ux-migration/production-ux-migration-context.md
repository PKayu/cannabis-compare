# Production UX migration context

- Created: 2026-09-25
- Last Updated: 2026-09-25
- Status: In Progress

## Current state

- Production is a Next.js 14 application using Tailwind, Supabase authentication, and FastAPI APIs.
- The production homepage already establishes a warm, groovy visual direction using Fredoka, Nunito, cream, amber, teal, sun yellow, dark green, outlined surfaces, and hard offset shadows.
- Most non-home public routes still use older styling and require convergence.
- The Lovable prototype is an interaction reference, not portable application code.
- Its strongest ideas are product decision hierarchy, explicit external handoff, freshness language, auth-intent recovery, and approachable empty states.
- Its unsupported additions and simplified data models must not enter production silently.

## Decisions

- Production remains the source of truth for data, routes, auth, compliance, and state behavior.
- Patient Guidance is future-only and must not be linked, routed, or implemented in the current redesign.
- The current production homepage is the visual source of truth until a separate naming/rebrand decision is approved.
- Botanical elements may be used as sparse accents, but not as repeating wallpaper behind task-heavy content.
- Public UI work must use the hard gates in `docs/ux/ACCEPTANCE-GATES.md`.
- Prototype-only capabilities must be classified in `docs/ux/CAPABILITY-STATUS.md` before implementation.

## Implemented foundation

- Added one shared responsive compliance banner to the production root layout.
- Removed duplicated route-level compliance banners from home, search, product detail, dispensary directory, and dispensary detail.
- Added focused compliance-copy coverage so future visual changes cannot silently drop the no-sale, external-purchase, or age requirements.

## Validation

- `cannabis-compare-ui` skill validation: passed.
- Focused compliance-banner test: passed.
- Frontend TypeScript check: passed.
- Frontend lint: passed with nine pre-existing React Hook dependency warnings.
- Frontend production build: passed with the same warnings.

## Source locations

- Production APIs: `backend/routers/`, `backend/models.py`
- Production auth: `frontend/lib/AuthContext.tsx`, `frontend/lib/api.ts`
- Current visual anchor: `frontend/app/page.tsx`, `frontend/app/globals.css`, `frontend/tailwind.config.ts`
- Lovable interaction reference: `C:/Projects/mountain-bloom-sanctuary`
- Review findings: `dev/active/lovable-latest-review/`
