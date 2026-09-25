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

- [x] Inventory the existing search and product-detail components against capability IDs.
- [x] Create focused local checkpoint commits without including unrelated changes.
- [x] Confirm public name: Mountain Bloom. Correct the visual reference to the prototype.
- [x] Establish shared public-page primitives; preserve homepage content.
- [x] Restyle search while preserving the production search contract and URL parameters.
- [x] Cover loading, initial, no-results, incomplete-data, and API-error states.
- [x] Restyle product detail, variant comparison, price observations, reviews, and related products.
- [x] Validate external dispensary URL selection and unavailable-offer behavior with focused tests.
- [ ] Pass desktop, 768px, and 390px acceptance gates.
- [x] Review loaded-image/font screenshots at all four widths and pass 10 production-browser scenarios.
- [x] Record capability mapping, validation limitations, and next-owner instructions in docs/ux/PILOT-HANDOFF.md.
- [ ] Resolve or disposition 11 pre-existing full-suite test failures before approval.
- [ ] Complete assistive-technology and authenticated live integration verification before pilot approval.

## Later journeys

- [ ] Migrate dispensary directory, detail, promotions, and inventory.
- [ ] Migrate watchlist and signed-out recovery.
- [ ] Migrate profile and notification preferences using production-supported settings only.
- [ ] Complete end-to-end accessibility and route compatibility review.
