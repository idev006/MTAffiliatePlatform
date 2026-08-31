# Program 2 — Affiliate Offer Intelligence & Automation

Status: IMPLEMENTATION-GOVERNING DESIGN / FOUNDATION READY
Date: 2026-08-31

## 1. Mission
Program 2 answers: **For each approved Product, which affiliate Offer(s), seller/context and affiliate link should be used?**

Program 2 does not decide which Product enters the platform; that is Program 1. Program 2 does not publish content; that is Program 3.

## 2. System Boundary
Inputs:
- approved Product identity from Program 1;
- campaign/policy profile;
- affiliate account/session context;
- worker capability/health facts.

Outputs:
- normalized Offer candidates and observations;
- eligibility result;
- ranked/selected preferred and backup Offers;
- validated affiliate link/export artifact;
- versioned Program 2 -> Program 3 handoff.

Durable authority remains Back Office. Browser workers collect facts and execute bounded platform operations only.

## 3. Core Workflow
`ProductCandidate -> OfferDiscoveryJob -> OfferObservations -> Normalize -> Eligibility -> Score -> Select -> Export/LinkAcquire -> Validate -> AffiliateLinkReady -> HandoffReady`

Exceptional flow includes:
`SESSION_REQUIRED | PRODUCT_NOT_FOUND | NO_OFFERS_FOUND | SCHEMA_CHANGED | RETRYABLE_ERROR | CONFLICT | NEEDS_HUMAN | CANCELLED`

## 4. Domain Model
Implementation foundation may define:
- `AffiliateAccountContext`
- `AffiliateOfferIdentity`
- `AffiliateOfferObservation`
- `OfferEligibilityDecision`
- `OfferScore`
- `OfferSelection`
- `AffiliateLink`
- `OfferExportArtifact`

Product 1:N Offer is mandatory. Preferred Offer is a versioned decision, not Product identity.

### Candidate Offer Identity
Until real Shopee evidence freezes canonical identity, adapters must preserve the richest observed identity tuple available, including platform/product/shop/item/seller/offer/account-context evidence. No weak UI label becomes canonical identity by itself.

## 5. Authority and State Ownership
Back Office owns:
- lifecycle and job authority through Shared Core jobs/job_events;
- Offer eligibility/ranking/selection;
- freshness policy;
- account-context provenance;
- export/import validation;
- canonical AffiliateLink records.

Worker owns only ephemeral execution state and durable local outbox/checkpoint needed for reliable delivery.

## 6. Account / Session Provenance
`worker_id != affiliate_account_id != session_id`.

Offer observations, selected offers and generated links retain account-context provenance where external facts can vary by account. Credentials/cookies/tokens are secret references and must not be stored in canonical Offer/Product rows.

## 7. API / Contract Direction
Business commands:
- `DISCOVER_OFFERS`
- `READ_OFFER_CANDIDATES`
- `SELECT_PLATFORM_OFFERS` only when Back Office has already decided identities
- `EXPORT_AFFILIATE_LINKS`
- `REPORT_EXPORT_ARTIFACT`

Worker events:
- `OFFER_DISCOVERY_STARTED`
- `OFFER_OBSERVED`
- `OFFER_DISCOVERY_COMPLETED`
- `EXPORT_STARTED`
- `EXPORT_ARTIFACT_READY`
- `SESSION_REQUIRED`
- `SCHEMA_CHANGED`
- `JOB_CHECKPOINT`
- `NEEDS_HUMAN`

All mutating commands require idempotency semantics appropriate to their external side effect.

## 8. Data / Persistence Baseline
Domain concepts:
- affiliate_offer_campaigns
- affiliate_offer_candidates / observations
- affiliate_offer_scores
- affiliate_offer_selections
- affiliate_export_jobs / items / artifacts
- affiliate_links

Shared `jobs`/`job_events` remain the lifecycle SSOT. Domain tables must not duplicate lease/retry/assignment authority.

## 9. Freshness
Every observation/link/selection carries timestamps and policy/version provenance. A link or selection can become STALE without deleting historical evidence. Program 3 may require freshness revalidation before publish-plan admission.

## 10. Failure and Recovery Rules
- duplicate event delivery is idempotent;
- ACK-dependent durable acceptance follows ADR-042 atomicity where applicable;
- external side effects are never blindly replayed after ambiguous outcome;
- schema/page drift is classified as `SCHEMA_CHANGED`, not generic retry;
- session/auth failure requires explicit session recovery or `NEEDS_HUMAN`;
- worker crash must not corrupt canonical selection history;
- retry policy is bounded and configuration-driven.

## 11. Testing Tailoring
Program 2 adds to the project Development Cycle:
1. scoring property/boundary tests;
2. eligibility decision-table tests;
3. Product 1:N Offer invariants;
4. account-context separation tests;
5. duplicate/event/idempotency tests;
6. export parser golden fixtures;
7. schema-drift fixtures;
8. SQLite/PostgreSQL repository compatibility;
9. restart/outbox/ACK-loss tests;
10. concurrent selection/link acquisition tests;
11. real browser-worker controlled-lab tests before production.

## 12. Implementation Readiness
### Foundation authorized now
The following may be implemented without waiting for real Shopee validation:
- domain types and ports;
- fake/in-memory repositories;
- eligibility/scoring engine with versioned configurable policy placeholder;
- application service;
- API DTOs/contracts;
- Shared Job integration contracts;
- SQLite/PostgreSQL-ready repository interfaces;
- worker protocol fakes;
- test harnesses and fixtures.

### Production completion gates
- canonical Offer identity validated with real Shopee evidence;
- Offer Scoring Model v1 business rules frozen;
- normalization semantics frozen;
- account-context behavior validated;
- export/download parser validated against real artifacts;
- Program 2 -> Program 3 contract version validated end-to-end;
- browser selector/schema profile validated;
- endurance/capacity evidence.

Unresolved CRITICAL/HIGH design issues for foundation implementation: **0**.

## 13. Initial Vertical Slices
P2-VS1: Product handoff -> fake Offer observations -> eligibility/score -> preferred/backup selection.

P2-VS2: durable Offer observation/selection persistence with SQLite + migrations + restart/idempotency.

P2-VS3: browser worker contract + local outbox + fake adapter.

P2-VS4: export/link artifact ingest + validation using golden fixtures.

P2-VS5: real controlled-browser spike and identity/account-context evidence capture.
