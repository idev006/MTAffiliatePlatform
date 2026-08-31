# Affiliate Offer Worker Specification

**Status:** IMPLEMENTATION HANDOFF BASELINE
**Step:** 2 — Affiliate Offer Discovery
**Owner Domain:** Affiliate Offer Automation
**Migrated to authoritative repo:** 2026-08-31

> Engine-first addendum: browser workers collect facts and execute bounded instructed actions. Eligibility, ranking, freshness, preferred/backup selection and business decisions belong to the Affiliate Offer Engine/Application layer.

## 1. Purpose

Convert an approved Product Candidate into a ranked, traceable set of Affiliate offers/links that can later be attached to content.

The browser plugin is a distributed execution worker, not a commercial decision engine.

## 2. Strategic Question

For a Product already approved for marketing, which currently available Affiliate Offer(s) provide the best combination of earnings opportunity, seller/offer quality, freshness and operational readiness?

## 3. Worker Farm Model

Many Offer Workers may run in parallel under one logical Back Office. Capability-based scheduling must allow workers to advertise functions such as:
- DISCOVER_OFFER
- READ_OFFER_CANDIDATES
- SELECT_OFFERS
- EXPORT_AFFILIATE_LINKS
- REPORT_DOWNLOAD

No PC is permanently bound to one step by architecture.

## 4. Primary Workflow

1. Receive Product job from Shared Job Engine.
2. Verify authorized affiliate page/session.
3. Search using approved product identity/query.
4. Read candidate offers available to the user.
5. Persist candidate batch locally before send.
6. Submit batch; advance only after durable Back Office ACK.
7. Wait for Back Office eligibility/ranking/selection decision.
8. Receive preferred/backup identifiers.
9. Perform permitted selection/export workflow.
10. Detect/export artifact metadata and report it.
11. Back Office imports/validates/persists link artifacts.
12. Job completes only after authoritative Back Office transition.

## 5. Responsibility Boundary

Worker owns:
- registration/heartbeat;
- page/session recognition;
- bounded search/extraction;
- local outbox;
- candidate submission;
- checkpoint reporting;
- instructed selection/export actions;
- safe diagnostics/errors.

Back Office owns:
- Product queue/campaigns;
- scheduling/leasing;
- offer eligibility;
- scoring/ranking;
- preferred/backup selection;
- freshness policy;
- canonical persistence;
- export/import validation;
- affiliate link state;
- audit/monitoring.

## 6. Account / Session Provenance

Worker identity is different from affiliate account/session identity.

Candidate facts that depend on account context must carry affiliate_account/session provenance sufficient for later audit and comparison.

Secrets/tokens are not stored in ordinary Offer records or logs.

## 7. Side Panel / UI

Preferred worker UI is an isolated extension Side Panel.

The UI displays worker/job/progress/error/outbox state but is not durable authority and contains no ranking logic.

## 8. Candidate Offer Contract

When available:
- product_id/canonical product identity;
- offer/external identifier;
- seller/shop identity and name;
- title;
- current/original price;
- rating/review/sold signals;
- base/extra/total displayed commission signals;
- voucher/promotion;
- availability/stock signal;
- collected_at;
- affiliate account/session provenance where relevant;
- worker/job/campaign provenance;
- extractor/profile/schema version.

Missing fields remain null/unknown.

## 9. Offer Set Policy

One Product retains multiple active/historical offers.

Candidate target counts such as 10–20 are configuration, not hard-coded architecture.

Back Office may maintain one preferred, multiple backups and rejected/stale/historical offers.

Product identity must never collapse into one permanent affiliate URL.

## 10. Ranking Boundary

Offer Engine may use versioned explainable factors including:
- commission opportunity;
- seller quality;
- price competitiveness;
- sales/review confidence;
- rating;
- vouchers/promotions;
- availability/freshness;
- own conversion history when available.

Worker never calculates the final commercial ranking.

Exact Offer Scoring Model v1 remains a production validation gate.

## 11. Job / Lease / Checkpoint

Shared Core `jobs` is the only lifecycle SSOT.

Domain-specific progress is represented through checkpoints/events rather than a second competing scheduler.

Meaningful checkpoints may include:
- SEARCH_STARTED;
- CANDIDATES_ACKNOWLEDGED;
- SELECTION_RECEIVED;
- SELECTION_COMPLETED;
- EXPORT_STARTED;
- DOWNLOAD_DETECTED;
- IMPORT_CONFIRMED.

Lease expiry triggers safe inspection/requeue according to Shared Job Engine policy.

## 12. Local Durability

`Persist local -> Send -> durable ACK -> advance checkpoint -> clear acknowledged outbox record`.

Temporary Back Office loss must not discard collected candidates or export events.

## 13. Error Model

Explicit errors include:
- PRODUCT_NOT_FOUND
- NO_OFFERS_FOUND
- SESSION_REQUIRED
- PAGE_CHANGED
- PAGE_UNSUPPORTED
- EXTRACTION_ERROR
- EXPORT_FAILED
- DOWNLOAD_NOT_DETECTED
- BACKOFFICE_UNREACHABLE
- RESOURCE_EXHAUSTED
- NEEDS_HUMAN

Ambiguous completion is never success.

## 14. Backpressure / Health

Back Office may slow/pause admission. Workers cap local backlog and report:
- heartbeat freshness;
- current state/job/product;
- candidate extraction success;
- retries/errors;
- local outbox size;
- last successful search/export;
- extension/browser version;
- capabilities.

## 15. Testability Requirements

Without live Shopee/browser, automated suites must verify:
- candidate normalization from sanitized fixtures;
- missing/null/account provenance semantics;
- parser schema-change detection;
- outbox/ACK/retry idempotency;
- job/checkpoint message contracts;
- selection/export command mapping;
- duplicate candidate batch submission behavior;
- explicit errors instead of false empty success.

Affiliate Offer Engine ranking/selection is tested separately using fake repositories/adapters.

## 16. Compliance Boundary

Automate only workflows available to the user's authorized account/session. Do not design around bypassing authentication, CAPTCHA, anti-abuse/rate controls or other platform protections.

## 17. Acceptance Criteria

1. Multiple Offer Workers process different jobs concurrently.
2. Every worker has persistent identity/capabilities/heartbeat.
3. Candidate facts reach Back Office with provenance and no embedded ranking decision.
4. Back Office can rank/select preferred/backups and return instructed actions.
5. Export artifacts correlate to originating job/account/selection.
6. Restart/crash cannot silently duplicate completed logical import.
7. Worker failure supports checkpoint-based safe requeue.
8. One Product retains multiple Offer histories/selections.
9. Step 3 consumes durable Offer/Link records, never worker memory.
10. Worker behavior is fixture/contract-testable without live platform.

## 18. Key Decision

**Step 2 plugin is a distributed worker/adapter farm. The commercial intelligence is a headless Back Office engine.**