# Public product design system

- Status: Active
- Visual reference: Mountain Bloom prototype (`mountain-bloom-sanctuary`, reviewed at `cdf0a26`)
- Approved name: Mountain Bloom (user decision, 2026-09-25)
- Production owns behavior and data; the prototype anchors the visual direction.
- Applies to: public and signed-in patient-facing routes
- Does not apply to: admin tooling unless explicitly requested

## Design intent

The interface should feel warm, candid, optimistic, and distinctly local while remaining credible for medical-cannabis price research. The personality comes from typography, color blocking, illustration, and tactile interaction—not from reducing data clarity.

## Foundations

### Typography

- Display: Lobster for short page titles and the wordmark. Use a readable sans-serif for long product names and numeric comparisons.
- Body: DM Sans for redesigned routes and the shared public shell.
- Existing Fredoka/Nunito utilities remain available to unmigrated routes until their own journey is reviewed.
- Use tabular numerals for prices, potency, counts, and dates.
- Use sentence case by default. Reserve uppercase tracking for short metadata labels.
- Keep explanatory text near 65 characters per line and use balanced wrapping on headings.

### Color

Use the centralized `bloom` tokens in `frontend/tailwind.config.ts` for migrated routes:

- Cream/parchment for readable task surfaces.
- Navy for the shell and strong text contrast.
- Avocado for product identity panels and selected states.
- Orange for primary actions, with dark text to preserve contrast.
- Mustard for restrained graphic accents; blue for section color fields.
- The older `groovy` palette is compatibility styling, not the new visual authority.

Do not introduce page-specific palettes. Status colors must remain distinguishable without relying on color alone.

### Shape and depth

- Use subtle navy borders and restrained offset shadows for actions; avoid heavy borders on every surface.
- Use large radii for outer panels, medium radii for controls, and tighter radii for nested elements.
- Do not turn every content group into an equal rounded card.
- Prefer asymmetric editorial composition for marketing content and structured grids/tables for comparison work.
- Keep shadows, borders, and radii visually subordinate to price and availability information.

### Botanical motifs

- Use the approved Mountain Bloom greenhouse/retro illustration in journey hero bands when it strengthens orientation or emotional tone; it is decorative and must not conceal the task heading.
- Use the prototype's low-contrast cannabis-leaf pattern as a page-field texture around content. Do not put it behind forms, tables, result cards, compliance text, or other task-heavy surfaces.
- Decorative artwork must be hidden from assistive technology and must not create horizontal overflow.

## Interaction rules

- Every interaction needs visible hover, pressed, keyboard-focus, disabled, and busy behavior.
- Motion uses opacity and transforms, respects `prefers-reduced-motion`, and never delays task completion.
- External dispensary actions must say that the user is leaving the application and that purchasing occurs on the licensed dispensary site.
- Search results support evaluation; they must not imply that a single fixture listing is the only available offer.
- Authentication interruptions preserve the user's intended destination and action.

## Responsive rules

- Design from 390px upward; do not treat mobile as a desktop layout that wraps.
- No essential information may require horizontal page scrolling.
- Touch targets are at least 44 by 44 CSS pixels.
- Tables must intentionally collapse, scroll within a labeled region, or become comparison rows.
- Fixed navigation must not obscure content, focus targets, or legal information.
- Verify at 390px, 768px, 1280px, and 1440px.

## Content and trust

- Clearly distinguish unavailable, unknown, stale, and out-of-stock data.
- Display the age/compliance treatment required by production on every route through the shared shell.
- Use plain language. Do not imply clinical advice, personalized recommendations, or in-app purchasing.
- Product imagery must be accurate or clearly labeled representative.

## Anti-patterns

- Repeating cannabis-leaf backgrounds.
- Three identical marketing cards used as the default layout.
- Multiple competing accent colors in one task surface.
- Ratings, discounts, inventory states, or locations not provided by production.
- Unreachable demo states that exist only as conditional markup.
- New localStorage authentication or mock production behavior.
