# Capability status and traceability

Every new UI behavior must be assigned one of these statuses before implementation:

- **Supported** — production API and behavior exist now.
- **Frontend-only** — uses existing data and requires no new backend promise.
- **Hidden** — prototype concept that must not appear in the current product.
- **Future** — potentially valuable, but requires product, legal, data, or backend work.

## Required current capabilities

| ID | Capability | Status | Production source | Required states |
|---|---|---|---|---|
| DISC-01 | Search by product or brand with a minimum two-character query | Supported | `backend/routers/search.py` | Initial, invalid query, loading, results, empty, error |
| DISC-02 | Filter by product type, price, THC, and CBD ranges | Supported | `backend/routers/search.py` | Defaults, active filters, cleared filters, incomplete potency |
| DISC-03 | Show price range, available weights, and dispensary count | Supported | Search response | Complete and partially missing data |
| EVAL-01 | Evaluate canonical product and weight variants | Supported | Product and variant APIs | Complete, partial, unavailable |
| PRICE-01 | Compare current prices by variant and dispensary | Supported | Product price APIs | In stock, unavailable, stale, no prices, error |
| PRICE-02 | View pricing history | Supported | Pricing-history API | Data, insufficient data, error |
| HANDOFF-01 | Leave for a licensed dispensary product page | Supported | `Price.product_url` | Valid URL and unavailable URL |
| DISP-01 | Browse licensed dispensaries | Supported | Dispensary API | Loading, list, empty, error |
| DISP-02 | View dispensary details and promotions | Supported | Dispensary API | Complete and incomplete details |
| DISP-03 | Browse and filter dispensary inventory | Supported | Dispensary inventory API | Results, empty, unavailable, error |
| SAVE-01 | Save or remove a canonical product | Supported | Watchlist API | Signed in, signed out, pending, saved, error |
| AUTH-01 | Sign in and return to the interrupted action | Frontend-only | Supabase auth plus safe return path | Success, cancellation, failure |
| REV-01 | Create a review while authenticated | Supported | Reviews API | Signed in, signed out, validation, success, error |
| ALERT-01 | Configure supported stock/price email and in-app preferences | Supported | Notifications and watchlist APIs | Loading, saved, validation, error |
| COMP-01 | Display informational-only and no-sale compliance | Supported | Shared production shell | Every route and viewport |

## Prototype decisions

| Concept | Status | Current decision |
|---|---|---|
| Patient Guidance page | Future | Preserve concept notes only. No route, navigation, or current implementation. |
| Guest review publishing | Hidden | Reviews continue to require production authentication. |
| SMS alerts | Future | Requires phone capture, verification, consent, delivery, and opt-out infrastructure. |
| Dollar-based price-drop threshold | Future | Current watchlist threshold is percentage-based. |
| Independent instant plus weekly switches | Hidden | Use the production frequency model. |
| Restock-only master preference | Hidden | Use supported stock and price alert controls. |
| Blank-query statewide catalog | Future | Requires a supported browse/catalog contract or explicit API change. |
| Search-card review aggregates | Future | Requires search response support or an approved aggregation strategy. |
| Search-card original-price deals | Future | Requires reliable promotion-to-product matching in search. |
| Low-stock and unknown stock levels | Future | Current production contract is binary availability. |
| Representative product imagery | Frontend-only | Allowed when labeled and never presented as the exact listing photo. |
| Mobile bottom navigation | Frontend-only | Allowed after route, focus, and content-obscuration testing. |
| Data freshness wording | Frontend-only | Allowed when derived from production timestamps. |

## Change rule

Changing a Hidden or Future capability to Supported requires:

1. Named product owner approval.
2. A production data/API source.
3. Authentication and compliance review where relevant.
4. Required state definitions.
5. Tests and updated migration/handoff notes.

