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
- Correction: the Mountain Bloom prototype is the visual reference, as requested in the original plan. The old production homepage is not the new design authority.
- The user approved the short public name Mountain Bloom on 2026-09-25.
- Botanical elements may be used as sparse accents, but not as repeating wallpaper behind task-heavy content.
- Public UI work must use the hard gates in `docs/ux/ACCEPTANCE-GATES.md`.
- Prototype-only capabilities must be classified in `docs/ux/CAPABILITY-STATUS.md` before implementation.

## Implemented foundation

- Added one shared responsive compliance banner to the production root layout.
- Removed duplicated route-level compliance banners from home, search, product detail, dispensary directory, and dispensary detail.
- Added focused compliance-copy coverage so future visual changes cannot silently drop the no-sale, external-purchase, or age requirements.

## Validation

The following foundation results predate the pilot. Pilot validation is recorded separately below.

- `cannabis-compare-ui` skill validation: passed.
- Focused compliance-banner test: passed.
- Frontend TypeScript check: passed.
- Frontend lint: passed with nine pre-existing React Hook dependency warnings.
- Frontend production build: passed with the same warnings.

## Source locations

- Production APIs: `backend/routers/`, `backend/models.py`
- Production auth: `frontend/lib/AuthContext.tsx`, `frontend/lib/api.ts`
- Visual reference: `C:/Projects/mountain-bloom-sanctuary/src/index.css` and prototype components. Production tokens adapt these within Next.js.
- Lovable interaction reference: `C:/Projects/mountain-bloom-sanctuary`
- Review findings: `dev/active/lovable-latest-review/`

## Checkpoint and pilot

- `8a46607`: UX documentation, task notes, and reusable skill checkpoint.
- `ddf430a`: shared compliance notice checkpoint.
- User authorized migration and local checkpoint commits; unrelated changes remain untouched.
- Pilot mappings: DISC-01/02/03 -> search, SearchBar, FilterPanel, ResultsTable; EVAL-01/PRICE-01/HANDOFF-01 -> product detail and PriceComparisonTable; PRICE-02 -> PricingChart. Existing reviews, related products, and watchlist actions remain accessible.
- Identified defects: search failures become empty results; deep-linked query is absent from input; missing-weight prices are duplicated into every known weight; advertised best price includes out-of-stock offers. Fix within the pilot.

## Pilot implementation

- Search and filters round-trip URL state, validate ranges, distinguish failed requests from empty results, and ignore stale responses.
- Product details, prices, related products, reviews, and price observations have independent failure boundaries.
- Package selection retains variant IDs; unknown sizes are never merged into known packages. Variants with no price records remain reachable.
- Listed-price comparisons exclude out-of-stock offers from the lowest-price label. Promotion estimates are secondary and explicitly conditional.
- The pricing-history endpoint groups current price records by update date across package sizes. UI now says "Price observations," not a complete historical trend.
- External product links use validated HTTP(S) destinations, explicit website fallbacks, or no external action. No invented product URLs.
- Save/review actions retain production authentication. Signed-out save preserves path and query in returnUrl; pending-action replay and alert-setting lifecycle remain later account-journey work.
- api.ts has a generic post method; ReviewForm's previous call was valid. Switching to api.reviews.create is endpoint centralization, not a backend bug fix.
- Five representative prototype JPG assets total 472,831 bytes. No new runtime dependency or icon library.
- Initial 14 focused Jest tests pass; typecheck and production build pass. Five existing hook warnings remain (admin, dispensary and watchlist code).
- Initial seven browser scenarios passed with fixture API responses. That run used fallback fonts and did not wait for images, so it is not accepted as visual evidence. Production rerun adds loaded-image checks and two additional state/filter scenarios.

## Final pilot validation (2026-09-25)

- Final production build, typecheck and focused 14-test suite pass.
- Final browser suite: 10/10 pass against production build with fixture APIs, including 390/768/1280/1440 screenshots, loaded fonts/images, no page overflow, no main-journey console errors, keyboard interactions and shared-shell regressions.
- Screenshots visually inspected. Mobile price observations use a readable summary and exact-value disclosure instead of a tiny SVG.
- Root layout owns the main landmark; home/terms/privacy wrappers changed to div without content changes to avoid nested main landmarks.
- Full Jest: 36 pass / 11 fail in existing unchanged AgeGate and API tests; stale DOB workflow and automatic-401-signout expectations. No compliance/auth changes made to satisfy those old tests.
- Acceptance is still open: actual screen reader, complete target/focus/zoom audit, authenticated integration and interrupted action replay, baseline test disposition, live-data extremes, Docker smoke test and user visual approval.
- See docs/ux/PILOT-HANDOFF.md for exact commands, mappings, evidence paths and migration boundaries.
- Saved pilot frontend/assets/tests as local commit a73a350. No push or deployment.

## Follow-up: visual convergence and local data (2026-09-25)

- User review found the search pilot had over-corrected away from the approved prototype by replacing the greenhouse header image and leaf page-field texture with a generic navy ring.
- Restoring the prototype hero artwork and low-contrast leaf texture is Frontend-only. The texture remains outside opaque, task-heavy panels so it does not weaken comparison readability.
- The local API at http://127.0.0.1:8000 is healthy, but `/api/products/search?q=blue` and `/api/dispensaries` both returned empty arrays. This is an empty local data store, not a search UI failure. `backend/seed_test_data.py` is the documented local test-data path; do not show fixture results as production results.
