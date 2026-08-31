# Product Discovery Browser Worker Specification

**Status:** IMPLEMENTATION HANDOFF BASELINE
**Domain:** Product Intelligence
**Role:** Browser Extension Worker / Data Acquisition Adapter
**Migrated to authoritative repo:** 2026-08-31
**Governing rule:** Project must follow the document.

> Engine-first addendum: this Worker is an adapter/execution component. Product Intelligence rules remain in Back Office engines. Parser/outbox/message behavior must be contract-testable using saved sanitized fixtures/fakes; the Side Panel is operational UI only.

## 1. Purpose

Build a browser extension that acts as a **Product Discovery Worker** for Shopee product discovery. The worker gathers structured product observations from user-accessible Shopee pages and reports them to the Python Back Office for normalization, deduplication, historical snapshots, scoring, ranking and shortlist generation.

The extension is **not** the Product Intelligence Engine. It does not decide which product should be marketed. It observes and reports facts.

## 2. Core Responsibility Boundary

**Extension owns:**
- page recognition;
- extracting currently visible/available product facts;
- controlled traversal of supported result pages;
- batching observations;
- local durable outbox;
- job progress;
- error reporting;
- heartbeat.

**Back Office owns:**
- discovery strategy;
- keyword/category job creation;
- hard filters;
- canonical normalization;
- deduplication;
- scoring;
- trend calculations;
- product ranking;
- historical analytics;
- business decisions.

## 3. Worker Modes

- `DISCOVER_SEARCH`
- `DISCOVER_CATEGORY`
- `DISCOVER_SHOP`
- `CAPTURE_CURRENT_PAGE`
- `REFRESH_QUERY`
- `PAUSE_JOB`
- `RESUME_JOB`
- `CANCEL_JOB`

Search/category/shop traversal limits are supplied by Back Office configuration/job contracts.

## 4. Minimum Observation Contract

Each product observation should include when available:

```text
observation_id
worker_id
job_id
source_platform
source_surface
source_url
source_query
source_category
source_shop
collected_at
item_id
shop_id
product_name
product_url
image_url
price_current
price_original
discount_percent
sold_signal
rating
review_count
seller_name
seller_location
seller_badges
voucher_signal
promotion_signal
shipping_signal
stock_signal
raw_payload_version
extractor_version
```

Unavailable fields are `null`/unknown, never fabricated or coerced to zero.

## 5. Product Identity

Preferred candidate external identity is `(shop_id, item_id)`, represented canonically with platform context as `(platform, shop_id, item_id)` pending real Shopee validation.

URLs and product names are not primary unique keys.

## 6. Snapshot Principle

Observations are append-oriented. Repeated observations of the same product are intentionally retained so Back Office can derive velocity, price movement, promotion periods, momentum and stability.

## 7. Extension UI

Use browser Side Panel or another isolated extension surface rather than injecting management UI into Shopee's main page DOM.

Minimum operator information:
- worker identity/status;
- current job/mode/query;
- page/progress;
- observed/sent/error counts;
- outbox status;
- Pause/Resume/Stop;
- Capture Current Page.

The Side Panel does not own durable job truth.

## 8. Job Contract

Back Office sends business-level jobs, never mouse coordinates or raw DOM selectors.

Conceptual example:

```json
{
  "job_id": "J-00182",
  "type": "DISCOVER_SEARCH",
  "query": "รถเข็นเด็ก",
  "limits": {"max_pages": 10, "max_products": 1000},
  "collection_profile": "product-card-v1"
}
```

Final payload schema is governed by versioned application/API contracts.

## 9. Worker States

Conceptual operational states:

`OFFLINE -> REGISTERING -> IDLE -> JOB_ACCEPTED -> PAGE_READY -> COLLECTING -> BATCH_SENDING -> COMPLETING -> DONE`

Explicit error/wait states include:
- WAITING_FOR_USER;
- SESSION_REQUIRED;
- PAGE_UNSUPPORTED;
- PAGE_CHANGED;
- NETWORK_ERROR;
- BACKOFFICE_UNREACHABLE;
- JOB_FAILED.

Ambiguous state is never guessed as success.

## 10. Local Durability / Outbox

```text
Collect batch
 -> Persist local outbox
 -> Send to Back Office
 -> Receive durable ACK
 -> Mark/delete delivered local batch
```

No ACK means retain and retry using the same batch/idempotency identity.

## 11. Deduplication Boundary

The extension may suppress duplicate cards within the same bounded collection operation.

Canonical cross-job/cross-worker deduplication is Back Office responsibility.

Historical observations must not be dropped merely because the product was seen previously.

## 12. Collection Profiles

Parsing rules are versioned, e.g.:
- `search-card-th-v1`;
- `category-card-th-v1`;
- `shop-card-th-v1`.

Each observation records extractor/profile version.

## 13. UI Change Detection

Known supported structure -> collect.

Unknown/changed structure -> `PAGE_CHANGED` -> capture safe diagnostics -> stop affected operation.

A parser must not silently return zero products and mark the job successful when expected structures disappeared.

## 14. Diagnostics

Report/store safe diagnostic fields:
- job_id;
- worker_id;
- page/surface context;
- state;
- timestamp;
- extractor version;
- structured error code;
- short safe detail;
- optional diagnostic evidence reference.

Sensitive session/authentication data must not be logged.

## 15. Heartbeat / Registry

Heartbeat may include:
- worker_id;
- extension/browser version;
- status;
- current_job;
- current_surface;
- last_success_at;
- queued_local_batches;
- capability/version metadata.

Heartbeat is liveness telemetry, not durable job truth.

## 16. Product Funnel

```text
RAW OBSERVATIONS
 -> NORMALIZATION
 -> CANONICAL PRODUCT CATALOG
 -> HARD FILTERS
 -> OPPORTUNITY FEATURES
 -> OPPORTUNITY SCORE
 -> SHORTLIST/REVIEW
 -> AFFILIATE OFFER DISCOVERY
```

All steps after acquisition are Back Office Engine/Application responsibilities.

## 17. Data Quality Metrics

Measure:
- products observed;
- valid identity rate;
- field completeness;
- duplicate rate within job;
- parse error rate;
- pages processed;
- unexpected zero-result rate;
- batch delivery success;
- observation latency.

Broken parsers must be detectable quantitatively.

## 18. Testability Requirements

Without a live Shopee session, automated tests must be able to verify:
- page recognition on sanitized saved fixtures;
- field extraction/normalization boundary;
- missing-field/null behavior;
- schema-changed detection;
- within-job duplicate suppression;
- batch construction;
- outbox persist/send/ACK/retry;
- message version/error mapping;
- job state transitions.

Live-browser tests validate real adapter compatibility, not core Product Intelligence decisions.

## 19. Non-Goals

The Worker does not:
- calculate final Product Opportunity Score;
- choose affiliate offers;
- generate affiliate links;
- create content;
- post videos;
- control Android devices;
- bypass authentication/platform controls;
- hide failure conditions.

## 20. Operational Boundary

The worker assists normal authorized browser workflows. It must not be designed around bypassing authentication, CAPTCHA, anti-abuse controls or other platform protections.

Collection cadence/limits are centrally configurable and observable.

## 21. MVP Acceptance

MVP requires:
1. isolated Side Panel operator UI;
2. worker registration + heartbeat;
3. manual current-page capture;
4. search-result capture;
5. stable product identity + core observable facts;
6. batch send to Back Office;
7. local outbox + ACK/retry;
8. job progress and pause/stop;
9. extractor versioning;
10. explicit `PAGE_CHANGED` behavior;
11. fixture-based parser/transport tests.

## 22. Key Design Decision

**Product Discovery Worker is a Worker/Adapter, not the brain.**

Reliable acquisition and provenance are its value. Product scoring, trend detection, portfolio strategy and learning remain independently testable in Python Back Office engines.