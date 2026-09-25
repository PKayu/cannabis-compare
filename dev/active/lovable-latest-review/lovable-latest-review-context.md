# Lovable Latest Review Context

- Created: 2026-09-25
- Last Updated: 2026-09-25
- Status: Complete

## Scope and sources

- Prototype: `C:\Projects\mountain-bloom-sanctuary`, `main` at `cdf0a26`.
- Production truth: this repository's Next.js frontend, FastAPI routers/models, `CLAUDE.md`, `README.md`, and architecture/index documentation.
- Review surfaces: discovery/search, product detail, dispensary detail, watchlist/auth, guidance, notification preferences, reviews, responsive behavior, and migration readiness.

## Key findings

- The product evaluation and external handoff concept is visually strong and largely understandable.
- The prototype brand is `Greenhouse / Far Out Utah`, not the approved Mountain Bloom Sanctuary rebrand.
- Repeated cannabis-leaf wallpaper conflicts with the intended avoidance of literal cannabis visual cliches.
- Several 390px views have severe horizontal clipping/overflow, including compliance, filters, cards, watchlist content, and footer content.
- Dispensary detail omits the inventory browser even though production supports it and the journey requires it.
- Prototype-only capabilities include patient guidance, guest review publishing, SMS preferences, dollar thresholds, combined urgency toggles, low-stock/unknown states, and search-level rating/deal data.
- Search allows an empty query even though production requires at least two characters, and it reduces the production multi-offer result to one price and one dispensary.
- Production routes/capabilities absent from the prototype include profile management, terms, privacy, age verification, review ownership actions, and complete notification parity.
- The prescribed UX knowledge package is not present in the latest prototype checkout, leaving no capability matrix, migration map, workboard, or acceptance evidence.
- Build succeeds. The only test is a placeholder and passes. Lint fails with five errors and seven warnings.

## Validation

- Desktop screenshots: search, product, dispensary detail, watchlist, guidance, and login.
- Mobile screenshots at 390px: search, product, and watchlist.
- `npm run build`: pass, with a 625 kB JavaScript chunk warning and a 2.2 MB hero asset.
- `npm test`: one placeholder test passes.
- `npm run lint`: fails with five errors and seven warnings.

## Decision guidance

- Keep and refine the product comparison interaction, explicit external handoff, auth-intent recovery, freshness labels, and representative-image labels.
- Hide or capability-flag unsupported guidance, guest reviews, SMS, dollar thresholds, and unsupported search metadata before migration.
- Do not import the prototype data models directly; introduce production-shaped fixtures or a documented presentation adapter first.

