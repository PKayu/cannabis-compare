# UX acceptance gates

A redesigned journey is not complete until every gate passes at mobile and desktop widths.

## Gate 1: product truth

- Every displayed value maps to a production field or a documented derived value.
- No fixture-only behavior is presented as available.
- Existing auth, API, and URL contracts remain intact.
- The capability IDs implemented by the journey are recorded in the handoff.

## Gate 2: task completion

- A user can complete the primary journey without a dead end.
- The next action is clear at each decision point.
- External handoffs disclose their destination and purpose.
- Authentication interruptions preserve safe return intent.

## Gate 3: state completeness

- Loading, initial, success, empty, incomplete, unavailable, error, and recovery states are implemented where applicable.
- Each state is reachable through a test, fixture, or deterministic development control.
- Unknown data is not displayed as zero or false.

## Gate 4: responsive behavior

- Evidence is captured at 390px, 768px, 1280px, and 1440px.
- No horizontal page overflow occurs.
- Essential labels, values, actions, and legal text are visible.
- Fixed elements do not cover content or focused controls.

## Gate 5: accessibility

- The complete journey works by keyboard.
- Focus order and visible focus are correct.
- Headings, landmarks, labels, live regions, and error associations are meaningful.
- Color contrast meets WCAG AA and meaning is not communicated by color alone.
- Motion respects reduced-motion preferences.

## Gate 6: brand consistency

- The work uses the production tokens and component decisions in `DESIGN-SYSTEM.md`.
- Botanical decoration remains sparse and non-interfering.
- Data-heavy content prioritizes legibility over decoration.
- Copy uses the approved product name and avoids unsupported medical claims.

## Gate 7: quality

- Type checking, lint, focused tests, and production build pass.
- The journey has behavior-focused tests, not placeholder-only coverage.
- New large assets and bundle growth are reviewed.
- No console errors, unsafe return URLs, or unsafe external handoffs remain.

## Required handoff evidence

- Capability IDs satisfied.
- Routes and files changed.
- Production fields/endpoints used.
- Screenshots at required widths.
- Keyboard walkthrough result.
- Automated commands and outcomes.
- Deferred or future concepts encountered.
- Known risks and rollback boundary.

