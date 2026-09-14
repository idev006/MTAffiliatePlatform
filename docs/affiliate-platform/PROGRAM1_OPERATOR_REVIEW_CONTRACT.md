# P1-UI-READ — Operator product evidence review

Date: 2026-09-09. Status: READY. User authorized completing usable Program 1.

## Scope and priority amendment

Amend CURRENT_STATE non-priority of bigger UI only for a small read-only product evidence screen. Operators currently need SQL or Swagger to inspect collected products; closing this gap serves the existing evidence-review use case. No campaign designer or business transition buttons are introduced.

## Contract

- GET /api/v1/program1/products returns latest observations, sorted deterministically by platform/shop/item, bounded limit 1..100 default 50 and offset >=0. Response includes items, total and image reference as data. Uses existing repository latest_observations through Program1Service; bounded response is not DB-level pagination.
- Read-only daisyUI page served by Program1 runtime at /program1/ui/backoffice.html, same origin API. Latest product table includes identity/name/source link, recorded price/rating where available, observation timestamp and image evidence status. Missing values are unknown, not zero.
- Operator may select a product to read newest-first history using P1-IMG-1 API. No remote image fetching by default; show valid HTTP(S) reference link with noreferrer/noopener. No v-html or arbitrary URI rendering.
- Show loading, empty, failure/retry and paging explicitly. Table uses bounded horizontal overflow at narrow widths; full page must not overflow. Failed reads must not imply zero stored data or retain unlabeled stale results.
- Vue/daisyUI shares the existing frontend build pipeline but has its own entrypoint; it must not import extension chrome APIs. Runtime serves only when assets exist; API remains usable without UI build. No Program2/3 route exposure.
- UI is optional read shell; no DB access or mutation/business policy in event handlers.

## Sequence

```mermaid
sequenceDiagram
  actor OP as Operator
  participant UI as Product Review
  participant API as Program1 API
  participant APP as Program1Service
  participant REP as Product Repository
  OP->>UI: Open or change page
  UI->>API: GET products with bounded page
  API->>APP: Read latest evidence page
  APP->>REP: latest_observations
  REP-->>APP: Stored facts
  APP-->>UI: Deterministic page and total via API
  alt Read failed
    UI-->>OP: Error and retry; no invented empty result
  else Read succeeded
    UI-->>OP: Evidence table or explicit empty state
    OP->>UI: Select product
    UI->>API: Read product history (D26)
    API-->>UI: Stored history and optional image URLs
  end
```

Acceptance: bounded/order/API tests, frontend build/suites, runtime static mount separation, browser read-only review of actual stored data when available, standard gates and explicit remaining evidence. CRITICAL/HIGH open design issues: zero for this read-only scope.

## P1-UI-FIND — 2026-09-14

Add bounded query q (maximum 200 characters) to latest-product evidence. Trim and Unicode-casefold; literal substring match against latest product_name, platform, shop_id or item_id only. Filter before counting/paging; total means matching product keys, not observations or new products. Empty query retains existing behavior. No wildcard interpretation or scoring. UI applies search explicitly, resets offset to zero and retains applied query across paging/refresh; failed reads remain errors. Existing memory-backed repository query limitation remains documented.

Sequence: Operator submits text -> UI sends q and offset=0 -> API validates bounds -> application filters latest observations -> repository facts remain unchanged -> UI presents matching count and rows/empty/error. Tests must cover case/Thai text, identity, latest-only matching, literal wildcard characters and count/page consistency.
