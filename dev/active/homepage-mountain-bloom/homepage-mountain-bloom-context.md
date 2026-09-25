# Mountain Bloom homepage migration context

- Created: 2026-09-25
- Last Updated: 2026-09-25
- Status: Implemented; approval gates remain open

## Current state

- `/` is legacy groovy UI using Fredoka/Nunito, a gradient, repeated leaf SVGs, and equal feature cards.
- The shared public shell already supplies Mountain Bloom navigation, compliance, footer, DM Sans, Lobster, Bloom tokens, tactile controls, and reduced-motion rules.
- `SearchBar` already owns autocomplete, invalid-query messaging, keyboard support, and the two-character query contract.
- `groovy-van-hero.png` is the approved camper-van homepage hero visual. It is decorative; text is kept on a solid, high-contrast task surface.

## Capability mapping

- DISC-01: the homepage passes a valid query to the existing production search route.
- DISP-01: the secondary route is the existing licensed-dispensary directory.
- COMP-01: root-layout compliance content remains visible and unchanged.

## Constraints

- No new API or backend work.
- No Patient Guidance, guest reviews, SMS alerts, dollar thresholds, blank-query statewide catalog, product ratings, deal claims, inventory states, or in-app purchasing.
- The generated visual references were preview-only; no generated asset is added to the project. Existing approved artwork remains the production asset.

## Implementation and evidence

- `/` is now a client route which passes valid `SearchBar` submissions to the existing search URL.
- Hero media is explicitly non-interactive after mobile browser testing found that its decorative image could otherwise intercept a search-button click.
- Browser coverage verifies invalid input, autocomplete keyboard selection, URL handoff, one main landmark, compliance, no Guidance link, image readiness, page-width containment, and browser console/page errors at the four required viewport widths.
- Visual screenshots were inspected at 390 and 1280 pixels. Google fonts fall back in the sandbox because external font downloads are blocked.
- Manual screen-reader, complete focus/target-size, and 200% zoom review are still required before approval.
