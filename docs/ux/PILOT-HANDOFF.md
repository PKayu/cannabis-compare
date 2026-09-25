# Mountain Bloom discovery pilot

- Created: 2026-09-25
- Last Updated: 2026-09-25
- Status: Implemented; approval gates remain open
- Repository: cannabis compare (production), not mountain-bloom-sanctuary

## Outcome and design authority

Find a product, narrow the results, compare packages and dispensaries, then leave for a valid dispensary destination.

The user approved **Mountain Bloom**. The prototype supplies the visual anchor; production supplies behavior. The repository UI skill guided shared tokens, explicit missing-data states, compliance preservation, and viewport evidence. The old groovy homepage is compatibility UI, not the authority for new designs.

No Guidance page, statewide deals feed, guest reviews, SMS, dollar alert thresholds, or personalized recommendations were added.

## Capability and route mapping

| Capability | Implementation | Production contract |
|---|---|---|
| DISC-01 | SearchBar and search route; query validation, autocomplete, retry | products.search / autocomplete, minimum 2 characters |
| DISC-02 | FilterPanel; apply/reset, sort, URL round-trip | product_type; min/max price, THC, CBD; supported sort_by |
| DISC-03 | ResultsTable cards; weights, price range, dispensary count, missing potency | Search response fields; no search stock/rating claims |
| EVAL-01 | Product header and package radio group | products.get, canonical id and variants |
| PRICE-01 | Variant-specific offer rows | products.getPrices; msrp, conditional promotion estimate, binary stock, timestamps |
| PRICE-02 | Price observations and accessible data table | products.getPricingHistory; current records grouped by update date, all variants |
| HANDOFF-01 | Product URL, explicit website fallback, or no external action | HTTP(S) product_url / dispensary_website only |
| REV-01 | Review display/filter/retry and existing authenticated form | reviews.list / create / upvote; useAuth preserved |
| SAVE-01 / AUTH-01 | Existing save action, canonical id, signed-out return path and query | watchlist and Supabase preserved; action replay not complete |
| COMP-01 | Existing shared notice and age gate remain | No-sale, informational, external purchase and age copy |

Existing URLs are preserved: /products/search and /products/[id]. Variant IDs still resolve through the production endpoint. Search q and filter parameters survive navigation. Product links carry an optional returnTo restricted to the search route. Dispensary links retain /dispensaries/[id]. No aliases or redirects are currently required.

## Important correctness changes

- Unknown-size offers are no longer repeated under every known weight.
- Package selection retains variant identity, including variants without prices.
- Lowest listed in-stock price excludes out-of-stock offers. The comparison is based on listed price, not a possibly ineligible promotion.
- Promotion values are labeled estimates because production applies dispensary promotions without reliable product-specific eligibility.
- Product details remain usable if offers, reviews, observations, or related-product requests fail.
- Missing potency is not zero. Search failure is not an empty result.
- No invented dispensary search URLs or dead "#" purchase links.
- Price observations are not presented as a complete price-change history.

## Implementation boundary

- Shared: layout/fonts, bloom Tailwind tokens/CSS, public navigation, footer, brand constant, compliance name.
- Journey: search and product routes; SearchBar, FilterPanel, ResultsTable, PriceComparisonTable, PricingChart, ReviewsSection.
- Narrow existing-component changes: ReviewForm labels/auth loading/centralized endpoint; WatchlistButton auth loading, signed-out return query, action labels.
- Presentation contracts: frontend/lib/product-contracts.ts and search-state.ts.
- Artwork: five existing prototype JPGs in frontend/public/images/mountain-bloom, 472,831 bytes total, clearly representative. Served directly using per-image unoptimized because standalone optimization lacks sharp. No runtime dependency added.
- api.ts, Supabase, protected routes and backend contracts were not changed.
- Home content, dispensary routes, profile, watchlist and authentication pages have not been visually migrated.

## Reproducible validation

Run from frontend:

    npm run type-check
    npm run lint
    npm test -- --runInBand ux-contracts PriceComparisonTable ComplianceBanner
    npm run build

For a production browser check in PowerShell, stop any test dev server first:

    $env:UX_PRODUCTION='1'
    npx playwright test -c playwright.ux.config.ts

The browser suite uses Edge, port 4010, typed API fixtures and preverified age state. It does not submit to a real account, dispensary or backend. Do not run a development server and build against the same .next directory simultaneously. The local next start harness emits a standalone-output warning; Docker runtime smoke testing remains separate.

Results:

- Focused Jest: 14/14 pass.
- Production browser: 10/10 pass on the final build, including the mobile-observation readability adjustment and home/legal landmark regression check.
- Typecheck and production build pass; lint has five existing hook warnings in admin, dispensary and watchlist code.
- Full Jest: 36 pass, 11 fail across unchanged AgeGate and api tests. AgeGate tests expect the removed DOB/checkbox workflow; the API test expects sign-out on 401, contrary to the current interceptor. Both source/test pairs have no diff from the checkpoint. Do not change compliance or auth behavior merely to satisfy these stale expectations.
- Core palette contrast ratios: ink/cream 13.91, muted/cream 6.08, ink/avocado 6.76, ink/orange 5.43, cream/navy 10.78, mustard/navy 6.57. This is not a complete accessibility certification.

Browser coverage: deep-linked query, filters/range validation/sorting, browser back, package switching, missing sizes/prices, external URL destination, unavailable offerings, loading, no-results, search/price/review/observation failures, retry, product 404, keyboard autocomplete, native radio keys, mobile menu Escape focus return, and signed-out save/review behavior.

Screenshots are generated under:

    frontend/test-results/ux/discovery.e2e.ts-discovery-and-comparison-at-{width}px/
      search-{width}.png
      product-{width}.png

Widths: 390, 768, 1280, 1440. Images/fonts must be loaded before capture. The main journey tests assert no page overflow and no browser console/page errors. Screenshots are ignored generated evidence, not committed product fixtures.

## Remaining approval gates and next work

Screenshots reviewed at all four widths: no clipped essential text or page overflow in the tested states. On mobile, the chart becomes a readable range summary plus expandable exact data rather than tiny axis labels.

1. Actual screen-reader walkthrough, complete focus/target-size audit, and 200% zoom. Keyboard automation and semantic markup alone do not close this gate.
2. Controlled authenticated integration: save/remove, review submit/upvote, expired session, return after login and interrupted-action recovery. No authenticated backend writes were performed.
3. Resolve or explicitly disposition the stale baseline tests; the full suite is not green.
4. Validate real-data extremes, slow loading, long names/locations, and standalone Docker packaging.
5. User visual review before declaring the pilot approved.

Then migrate dispensary exploration and the account/watchlist journey. Account work must address the existing remove/re-add threshold update and pending-action replay; neither should be treated as solved by the current sign-in link.

## Checkpoint / rollback

Earlier local checkpoints: 8a46607 (UX documentation) and ddf430a (shared compliance notice).

Pilot frontend checkpoint: a73a350 (implementation, assets and tests). Nothing pushed or deployed.

Keep pilot frontend changes and documentation logically grouped. Revert the pilot as a coherent commit if necessary; do not reset the repository or remove unrelated user changes. No push or deployment is part of this work.
