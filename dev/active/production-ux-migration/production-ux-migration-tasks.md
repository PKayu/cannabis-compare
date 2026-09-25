# Production UX migration tasks

- Created: 2026-09-25
- Last Updated: 2026-09-25
- Status: In Progress

## Foundation

- [x] Review production primers, architecture, and current visual implementation.
- [x] Establish the UX documentation package.
- [x] Record supported, hidden, and future-only capabilities.
- [x] Define hard acceptance gates and required evidence.
- [x] Define journey-by-journey execution and handoff rules.
- [x] Create and validate a project-specific UI design skill.
- [x] Link the UX package from repository instructions and documentation index.
- [x] Centralize compliance messaging in the production shell with focused test coverage.

## Journey 1: discovery and product evaluation

- [ ] Inventory the existing search and product-detail components against capability IDs.
- [ ] Establish shared public-page primitives without disrupting the homepage.
- [ ] Restyle search while preserving the production search contract and URL parameters.
- [ ] Cover loading, initial, no-results, incomplete-data, and API-error states.
- [ ] Restyle product detail, variant comparison, price history, reviews, and related products.
- [ ] Validate external dispensary handoff behavior.
- [ ] Pass desktop, 768px, and 390px acceptance gates.

## Later journeys

- [ ] Migrate dispensary directory, detail, promotions, and inventory.
- [ ] Migrate watchlist and signed-out recovery.
- [ ] Migrate profile and notification preferences using production-supported settings only.
- [ ] Complete end-to-end accessibility and route compatibility review.
