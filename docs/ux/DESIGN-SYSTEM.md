# Public product design system

- Status: Active
- Visual source of truth: current production homepage
- Applies to: public and signed-in patient-facing routes
- Does not apply to: admin tooling unless explicitly requested

## Design intent

The interface should feel warm, candid, optimistic, and distinctly local while remaining credible for medical-cannabis price research. The personality comes from typography, color blocking, illustration, and tactile interaction—not from reducing data clarity.

## Foundations

### Typography

- Display: Fredoka, using 600–700 for primary headings and high-value labels.
- Body: Nunito, using 400–700 for readable UI and supporting copy.
- Use tabular numerals for prices, potency, counts, and dates.
- Use sentence case by default. Reserve uppercase tracking for short metadata labels.
- Keep explanatory text near 65 characters per line and use balanced wrapping on headings.

### Color

Use the tokens already defined in `frontend/tailwind.config.ts`:

- Cream `groovy-cream` for the primary canvas.
- Ink `groovy-ink` for text and hard outlines.
- Teal/dark green for navigation, major bands, and primary product structure.
- Amber/orange for action and emphasis.
- Sun yellow for price highlights and selective calls to action.
- Cobalt only when a distinct informational role requires it; it is not a general-purpose accent.

Do not introduce page-specific palettes. Status colors must remain distinguishable without relying on color alone.

### Shape and depth

- Use 2px ink outlines and hard offset shadows on important interactive surfaces.
- Use large radii for outer panels, medium radii for controls, and tighter radii for nested elements.
- Do not turn every content group into an equal rounded card.
- Prefer asymmetric editorial composition for marketing content and structured grids/tables for comparison work.
- Keep shadows, borders, and radii visually subordinate to price and availability information.

### Botanical motifs

- Use the existing `CannabisLeaf` artwork as an occasional brand accent.
- Never use repeating leaf wallpaper behind forms, tables, result grids, compliance text, or other task-heavy content.
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
