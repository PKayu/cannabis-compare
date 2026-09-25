# Mountain Bloom homepage migration plan

- Created: 2026-09-25
- Last Updated: 2026-09-25
- Status: Implemented; approval gates remain open

## Objective

Replace the legacy groovy homepage with a Mountain Bloom landing page that starts a valid product search while preserving production routes, authentication, compliance, and shared navigation.

## Implementation

1. Use the existing `SearchBar` to take a two-character minimum query to `/products/search?q=...`.
2. Rebuild the page around the approved camper-van artwork, Bloom typography/tokens, patterned blue shell, parchment task surface, asymmetric information panels, dispensary teaser, and final product-search CTA.
3. Keep all claims capability-safe: no invented catalog, inventory, ratings, deals, discounts, purchasing, or future concepts.
4. Extend the browser UX suite with home-route search, responsive, image, landmark, compliance, and console-error coverage.

## Validation

- `npm run type-check`
- `npm run lint`
- `npm run build`
- `UX_PRODUCTION=1 npx playwright test -c playwright.ux.config.ts`

## Results

- `npm run type-check`: pass.
- `npm run lint`: pass with five pre-existing hook warnings outside the homepage.
- `npm run build`: pass with the same warnings.
- Development browser harness: 4/4 homepage scenarios pass at 390, 768, 1280, and 1440 pixels.
- Production browser harness remains blocked by the known standalone-output `next start` issue: the generated server cannot resolve `vendor-chunks/@supabase.js`. This is a packaging/harness limitation, not a homepage assertion failure.
