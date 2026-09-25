# UX execution and handoff

## Delivery model

Work one complete journey at a time in production. Do not merge the Lovable repository or transplant its router, mock session, fixture types, or shadcn layer.

### Journey order

1. Discover and compare products.
2. Evaluate a product and select an offering.
3. Explore dispensaries and inventory.
4. Save products and recover through authentication.
5. Manage profile, reviews, and supported alert preferences.
6. Converge shared navigation, mobile behavior, and accessibility.

The first two items form the active pilot and may share primitives, but each must remain reviewable.

### Migration status

- The shared public shell and homepage are implemented; their manual accessibility and environment-specific validation gates remain open.
- Discovery and product evaluation are implemented as the first pilot; see `PILOT-HANDOFF.md`.
- Dispensary exploration and inventory is the next implementation journey.

## Before implementation

1. Read the production route, components, API client calls, and matching backend router.
2. List the capability IDs being changed.
3. Classify every proposed addition using `CAPABILITY-STATUS.md`.
4. Record route compatibility and shared-component impact in the active task context.
5. Define reachable test scenarios before styling.

## During implementation

- Preserve `frontend/lib/api.ts`, `useAuth()`, Supabase session behavior, protected routes, and API payloads.
- Use production data directly or create a narrowly scoped presentation adapter with explicit null handling.
- Keep shared tokens and public primitives centralized.
- Make desktop and mobile changes together; mobile is not a cleanup phase.
- Do not introduce a new component library solely to match the prototype.

## Handoff template

Each completed journey records:

```md
## Journey
Name and user outcome

## Capability coverage
IDs and where each is satisfied

## Production mapping
Routes, endpoints, fields, auth behavior, and external URLs

## States
How to reach loading, empty, incomplete, unavailable, error, success, and auth states

## Validation
390/768/1280/1440 screenshots, keyboard pass, tests, lint, typecheck, build

## Deferred decisions
Future concepts, unsupported ideas, and known limitations

## Migration boundary
Files changed, shared dependencies, and safe rollback point
```

## Review ownership

- Journey implementer: interaction, responsive behavior, production mapping, and focused tests.
- Design steward: shared tokens, primitives, brand consistency, and cross-journey pattern decisions.
- Reviewer: capability traceability, accessibility, regression risk, and unsupported-feature detection.

One person may fill multiple roles, but the handoff must address each responsibility explicitly.
