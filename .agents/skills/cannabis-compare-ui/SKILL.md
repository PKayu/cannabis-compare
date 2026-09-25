---
name: cannabis-compare-ui
description: Design, implement, or review patient-facing UI in the cannabis compare repository using its groovy production theme, real capability contracts, compliance requirements, and responsive acceptance gates. Use for new public components, route redesigns, visual convergence, or importing ideas from prototypes; do not use for backend-only or admin-only work.
---

# Cannabis Compare UI

Create production UI that feels like one system while preserving product truth.

## Required context

Before editing patient-facing UI, read:

1. `docs/ux/DESIGN-SYSTEM.md`
2. `docs/ux/CAPABILITY-STATUS.md`
3. `docs/ux/ACCEPTANCE-GATES.md`

For a full journey or prototype migration, also read `docs/ux/EXECUTION-AND-HANDOFF.md`.

## Decision sequence

1. Identify the user outcome and applicable capability IDs.
2. Verify the production API, auth, compliance, and route behavior before designing around it.
3. Classify new ideas as Supported, Frontend-only, Hidden, or Future.
4. Work within the existing Next.js, Tailwind, `api.ts`, and `useAuth()` architecture.
5. Extend existing tokens and primitives before adding page-local visual systems.
6. Implement all relevant states and make them deterministically reachable.
7. Validate at 390px, 768px, 1280px, and 1440px, then complete the handoff evidence.

## Theme invariants

- Use the Mountain Bloom prototype as the visual anchor, with Lobster for short display headings and DM Sans for readable UI.
- Use centralized bloom cream, navy, avocado, orange, mustard, and blue tokens for migrated routes. Legacy groovy tokens remain for unmigrated routes.
- Use restrained borders and offset shadows; prioritize contrast and task clarity.
- Use varying radii and asymmetric composition; do not default to equal card grids.
- The approved public name is Mountain Bloom. Prefer sparse abstract botanical and landscape accents. Never place repeating leaf wallpaper behind task content.
- Protect the clarity of prices, potency, stock, timestamps, and dispensary comparisons.

## Product invariants

- Purchasing happens only on licensed dispensary sites.
- Reviews require production authentication.
- The search API requires a query of at least two characters.
- Product variants and prices must retain their parent/variant relationship.
- Patient Guidance is a future concept and must not be implemented or linked.
- Do not surface SMS, dollar thresholds, guest reviews, or other Future/Hidden concepts without an approved capability-status change.

## Completion rule

Do not call a journey complete because it looks finished. It is complete only when its production mapping, reachable states, responsive evidence, accessibility walkthrough, focused tests, lint, typecheck, and build satisfy `docs/ux/ACCEPTANCE-GATES.md`.
