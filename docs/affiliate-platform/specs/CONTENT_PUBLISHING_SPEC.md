# Content Publishing Specification

Status: IMPLEMENTATION HANDOFF BASELINE
Owner Domain: Content Publishing
Date: 2026-08-31

## 1. Purpose

Own the durable relationship and workflow from Video identity through Publish Plan, job execution, verification, Publishing Ledger and analytics attribution.

The domain answers:
- Is this video allowed to publish to this platform/account under current duplicate policy?
- Which Product/Offer set should be attached?
- Is the plan ready for irreversible submit?
- What is the authoritative outcome after execution?

## 2. Core Relationships

- Product 1:N Videos.
- Product 1:N Affiliate Offers.
- Publish Plan references one Video and one or more target Product/Offer selections subject to platform capacity policy.
- One Video may have multiple platform/account publish-state records, but duplicate policy may block them centrally.

## 3. Video Registration

Every video must be registered before publish planning.

Capture conceptually:
- video_id;
- logical source/path reference;
- filename metadata;
- duration;
- dimensions;
- exact SHA-256;
- media metadata;
- fingerprint records when configured;
- ingestion/validation state.

Filename is never primary identity.

## 4. Content Identity Engine

Responsibilities:
- exact SHA-256 identity;
- perceptual comparison policy when algorithm is enabled;
- duplicate classification;
- platform duplicate-gate decision;
- comparison evidence/model version.

Baseline classifications:
- EXACT;
- NEAR;
- UNIQUE;
- REVIEW.

`REVIEW` is not silently treated as UNIQUE.

Perceptual algorithm/window/threshold remain production validation gates.

## 5. Duplicate Policy

Current baseline Shopee policy:
A video identity confirmed successfully published to Shopee is blocked from subsequent Shopee publish jobs across the managed account pool unless an explicit versioned policy changes this rule.

Enforcement should occur at multiple boundaries:
1. Publish Plan creation;
2. queue admission;
3. pre-dispatch/pre-submit freshness gate;
4. confirmed-success ledger transaction.

The Publishing Ledger is authoritative.

## 6. Publish Plan

A versioned immutable/supersedable plan contains:
- publish_plan_id;
- platform;
- account_id;
- video_id;
- selected product/offer references;
- caption/tag references;
- capacity/basket rule version;
- duplicate policy version;
- offer freshness rule/version;
- validation findings;
- created_at.

Back Office sends product/offer identities, not just search text.

## 7. Basket / Product Capacity

Platform basket capacity is configurable and version/context-aware.

The currently observed design target may allow up to six products, but this must be validated against actual Shopee app/account/version before production lock.

Do not encode `6` as an immutable domain constant.

## 8. Publishing Engine

Owns:
- plan validation;
- duplicate gate;
- identity/product/offer/account constraints;
- offer freshness/readiness checks;
- irreversible-action pre-submit guard;
- publish outcome state policy;
- reconciliation decisions;
- ledger transition rules.

Does not:
- tap Android UI;
- own raw selectors;
- stream device screens;
- import PySide6/ADB/uiautomator2.

## 9. Job Flow

Conceptual:

`PLAN_VALIDATED -> JOB_QUEUED -> JOB_LEASED -> EXECUTING -> READY_TO_SUBMIT -> POST_SUBMITTED -> VERIFYING -> CONFIRMED_SUCCESS`

Alternative outcomes:
- FAILED_SAFE_BEFORE_SUBMIT;
- SKIPPED_DUPLICATE;
- POST_OUTCOME_UNKNOWN;
- NEEDS_HUMAN;
- CANCELLED where safe.

Shared Job Engine remains lifecycle SSOT; publishing-specific states/evidence are domain records/events, not a competing scheduler.

## 10. Pre-Submit Guard

Immediately before irreversible submit, verify:
- expected video identity;
- selected products/offers match plan;
- basket capacity valid;
- caption/tags/required metadata valid;
- duplicate policy still passes;
- offer freshness/policy still passes;
- account/job/lease valid;
- Worker/Scene reports ready-to-publish state.

If any critical precondition is ambiguous, do not submit.

## 11. Irreversible Boundary

`POST_SUBMITTED` is a critical boundary.

After this boundary, timeout/crash/disconnect does not mean failure.

Prohibited:
- automatic blind repost;
- assuming no result = not posted.

Required:
- record submitted evidence/checkpoint;
- reconcile with available evidence;
- classify confirmed success / confirmed safe failure / unknown;
- route unknown to NEEDS_HUMAN if not provable.

## 12. Publishing Ledger

On confirmed success, record atomically where feasible:
- video/platform/account;
- publish_plan_id;
- job_id;
- external post ID if observable;
- submitted/confirmed times;
- success outcome;
- evidence refs;
- policy/idempotency identity;
- platform publish-state transition;
- job completion transition.

Database constraints should backstop duplicate invariants using semantics portable across Tier-1 DBs or documented per-adapter equivalents.

## 13. Worker Event Inputs

Worker reports facts/events such as:
- VIDEO_SELECTED;
- SCENE_CHANGED;
- BASKET_ATTACHED;
- DETAILS_ENTERED;
- READY_TO_PUBLISH;
- POST_SUBMITTED;
- POST_SUCCESS_SIGNAL;
- POST_FAILED_SIGNAL;
- POST_OUTCOME_UNKNOWN;
- NEEDS_HUMAN.

Back Office validates these facts before canonical transitions.

## 14. Transaction Rule

Never hold DB transaction open while waiting for video upload/Android UI/network/human response.

Use short transactions for:
- plan/queue validation;
- lease/checkpoint;
- submitted-boundary record;
- final ledger/result commit.

## 15. Testability

Publishing Engine must be fully component-testable with:
- InMemoryVideoRepository;
- InMemoryPublishingLedger;
- FakeClock;
- deterministic identity fixtures;
- fake offer/product state;
- scripted Worker/Scene facts.

Mandatory tests:
- exact duplicate blocked;
- near/review behavior per policy;
- race: two jobs attempt same video;
- stale version conflict;
- offer becomes stale before submit;
- basket mismatch;
- repeated `POST_SUBMITTED` event idempotency;
- crash after submitted boundary;
- unknown outcome never auto-reposts;
- confirmed success atomically updates ledger/state;
- duplicate success conflict rejected.

Physical phone is not required for these rules.

## 16. Analytics Attribution

Confirmed publication facts should later support attribution by:
- product;
- offer;
- video/content angle;
- platform/account;
- campaign/ruleset/model version;
- publish time.

Analytics ingestion remains adapter-driven and does not directly rewrite historical decision provenance.

## 17. Acceptance Criteria

1. Every publishable video has registered identity.
2. Duplicate policy can block job creation/submit using durable history.
3. Publish Plan is versioned and explainable.
4. Worker cannot independently mark canonical publish success.
5. Unknown post outcome never causes blind repost.
6. Confirmed success is durably auditable and attributable.
7. Publishing Engine tests run headless with no Android/UI/network.
8. Concrete Android execution can be replaced without rewriting duplicate/publishing policy.

## 18. Open Production Gates

- perceptual fingerprint algorithm/threshold/window;
- final basket capacity/rules by real app/account/version;
- final Step2->Step3 DTO fields;
- precise post-submit success/reconciliation evidence on real Shopee;
- pacing/retry/timing values from real-device tests.