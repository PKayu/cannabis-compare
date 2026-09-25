# Mountain Bloom homepage handoff

- Created: 2026-09-25
- Last Updated: 2026-09-25
- Status: Implemented; approval gates remain open

## Journey

Start a valid product search from the public entry page, orient to the comparison workflow, or continue to the licensed-dispensary directory.

## Capability coverage

| Capability | Implementation |
|---|---|
| DISC-01 | Shared `SearchBar` validates a two-character query, supplies autocomplete, and routes to `/products/search?q=...`. |
| DISP-01 | Secondary link routes to the existing dispensary directory. |
| COMP-01 | Root-layout age/compliance treatment remains unchanged. |

## Production mapping

- Route: `/`.
- Search uses the existing `SearchBar`, `products.autocomplete`, and search-route contract; no home API or mock data was added.
- Existing public navigation, Supabase behavior, compliance banner, footer, and URLs are preserved.
- `groovy-van-hero.png` is decorative, non-interactive artwork. It is not presented as product or dispensary data.

## States and validation

- Invalid query, autocomplete keyboard selection, URL handoff, landmarks, compliance, loaded artwork, no overflow, and console/page errors are covered at 390, 768, 1280, and 1440 pixels.
- Typecheck, lint, and production build pass; lint retains five existing hook warnings outside this route.
- Development Playwright homepage coverage passes 4/4. The current production `next start` harness is blocked by the known standalone vendor-chunk/Supabase resolution issue.

## Deferred decisions

- No Patient Guidance, guest reviews, SMS alerts, dollar thresholds, blank-query catalog, ratings, deal claims, inventory states, or in-app purchasing.
- Manual screen-reader, complete focus/target-size, and 200% zoom review remain required before approval.

## Migration boundary

- Homepage implementation: `frontend/app/page.tsx`.
- Browser coverage: `frontend/ux-tests/discovery.e2e.ts`.
- Shared Bloom tokens and primitives are reused; no backend/API contracts changed.
