# Application and Engine Contracts

Status: IMPLEMENTATION HANDOFF BASELINE
Date: 2026-08-31

## 1. Purpose

Define stable semantic boundaries between UI/API/CLI, application use cases, domain engines and infrastructure adapters.

This document intentionally defines business contracts before concrete Python classes.

## 2. Contract Rules

1. Commands request state-changing intent.
2. Queries request information and do not mutate business state.
3. Results are typed and explicit; do not signal ordinary business outcomes only through exceptions.
4. Domain/application contracts contain semantic identities, not ORM entities, DOM nodes, Android selectors or UI widgets.
5. Side effects occur through ports.
6. Every side-effecting command that may be retried has idempotency semantics.
7. Errors use stable application error codes and structured context.
8. Contract version changes follow API/schema compatibility rules.

## 3. Common Command Metadata

Conceptual command metadata:
- command_id
- schema_version
- idempotency_key where applicable
- correlation_id
- requested_at
- actor/source
- expected_version where optimistic concurrency applies

## 4. Common Result Shape

Conceptual result:

```text
status: SUCCESS | REJECTED | CONFLICT | RETRYABLE_ERROR | NEEDS_HUMAN | OUTCOME_UNKNOWN
value: typed payload nullable
error: structured error nullable
events: domain/application events
version: resulting aggregate/job version where relevant
evidence_refs: optional
```

Exceptions are reserved for programmer/infrastructure failures that cannot be represented as expected business outcomes.

## 5. Common Error Contract

Fields:
- error_code
- category
- message_safe
- component
- retryable
- job_id nullable
- correlation_id
- worker_id/device_id nullable
- evidence_ref nullable
- adapter/version metadata nullable
- occurred_at

Categories:
- VALIDATION
- CONFLICT
- RETRYABLE
- NON_RETRYABLE
- SESSION_REQUIRED
- SCHEMA_CHANGED
- RESOURCE_EXHAUSTED
- NEEDS_HUMAN
- OUTCOME_UNKNOWN
- SECURITY_POLICY

Stable error codes are preferred over parsing human text.

## 6. Shared Job Engine Contracts

### CreateJob
Input:
- job_type
- domain
- payload/reference
- priority
- idempotency_key
- capability requirements

Output:
- job_id
- state
- job_version

Invariant:
Same idempotency identity must not create a second logical job.

### LeaseJob
Input:
- worker_id
- capabilities
- lease duration policy reference

Output:
- job_id
- lease_token
- lease_until
- job_version
- payload/reference

### RenewLease
Requires current lease token/version.

### RecordCheckpoint
Input:
- job_id
- lease identity
- checkpoint type/payload
- expected job_version

### CompleteJob / FailJob / NeedsHuman
Transitions are validated by Job Engine, not repository adapter.

## 7. Program 1 — Affiliate Opportunity Intelligence Contracts

Governing strategy: `PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md`.

### BuildDiscoveryPlan
Input:
- campaign / hypothesis reference;
- required signal ids;
- source/surface scope;
- bounded collection targets (for example approved listing/search URLs or opaque target refs);
- required worker capabilities;
- evidence/collection policy versions.

Output:
- durable DiscoveryPlan reference suitable for worker execution.

Rule:
Collection targets describe bounded operational work. They must not embed DOM selectors or browser implementation policy.

### IngestProductObservationBatch
Input:
- batch_id
- worker/source provenance
- observations[]
- schema_version

Output:
- accepted count
- rejected items/reasons
- durable ACK identity

### DeriveOpportunityFeatures
Input:
- campaign_id;
- affiliate/business hypothesis reference;
- product_ids or eligible set reference;
- normalized observation/history reference;
- feature_policy_version;
- feature/reference timestamp.

Output per product:
- versioned feature values;
- feature evidence/provenance references;
- data sufficiency/unknown state;
- uncertainty/freshness metadata.

Features may cover demand, momentum/timing, buyer-intent context, price/value, seller confidence, competition/saturation, contentability, risk and approved cross-program economic context where contracts allow.

### EvaluateOpportunity
Input:
- campaign_id;
- product_ids or eligible set reference;
- opportunity_policy_version;
- feature snapshot/reference timestamp;
- audience/account/campaign context where applicable.

Output per product:
- qualification state;
- recommended action such as TEST_NOW / WATCH / SCALE / HOLD / DEPRIORITIZE / STOP / NEEDS_EVIDENCE where supported by the active policy;
- Opportunity Thesis / explanation;
- risks/uncertainties;
- evidence freshness;
- optional component scores;
- total score only when an approved scoring model exists;
- policy/model version.

### ScoreProducts
This remains a compatible specialized contract for approved scoring models.

Input:
- campaign_id
- product_ids or eligible set reference
- scoring_model_version
- feature/reference timestamp

Output per product:
- score
- component scores
- explanation/reasons
- model version

A production score must not be invented merely to satisfy this contract. Until validated, qualification/features/opportunity thesis may drive shortlist decisions.

### BuildShortlist
Input:
- campaign_id;
- evaluated/scored product references;
- shortlist ruleset/version.

Output:
- shortlist/action-candidate decisions with reasons, evidence freshness and decision provenance.

The engine must produce deterministic output for the same normalized facts/features/context + policy/model version.

## 8. Affiliate Offer Contracts

### IngestOfferCandidateBatch
Input includes:
- product_id
- candidate facts
- affiliate account/session provenance when relevant
- observed_at
- source/schema version

### EvaluateOffers
Output:
- eligible/ineligible decision
- freshness
- score/components
- reasons
- model/ruleset version

### SelectOffers
Output:
- preferred_offer_id
- backup_offer_ids
- valid_from/freshness reference
- decision reason/model version

## 9. Content Identity Contracts

### RegisterVideo
Input:
- logical source reference/path
- supplied metadata if known

Engine/application obtains media facts via MediaProbePort.

Output:
- video_id
- exact_sha256
- validated media metadata
- registration state

### EvaluateVideoDuplicate
Input:
- video_id
- platform
- duplicate policy version

Output:
- EXACT | NEAR | UNIQUE | REVIEW
- matching references
- comparison score/distance when applicable
- policy/algorithm version
- publish_allowed boolean only if policy can decide conclusively

`REVIEW` does not silently become UNIQUE.

## 10. Publish Planning Contracts

### BuildPublishPlan
Input:
- platform
- account_id
- video_id
- target products/offers[]
- caption/tag references
- ruleset versions

Output:
- publish_plan_id
- validation findings
- ready boolean
- effective basket/capacity rule
- duplicate gate evidence

### QueuePublishPlan
Requires a ready validated plan and idempotency key.

## 11. Publishing Engine Contracts

### ValidatePreSubmit
Re-evaluates irreversible prerequisites immediately before submit where freshness matters.

Checks conceptually:
- correct video identity;
- expected products/offers selected;
- basket limits valid;
- caption/tag requirements;
- duplicate ledger still clear;
- offer freshness within rule;
- account/job/lease valid;
- Scene is ready-to-publish.

Output:
- ALLOW_SUBMIT or REJECT/NEEDS_HUMAN with findings.

### RecordPostSubmitted
Creates durable boundary evidence that irreversible action may have occurred.

### ConfirmPublishSuccess
Input:
- job/plan/video/platform/account identity
- post/evidence identifiers
- expected versions

Effect:
Atomically record ledger/platform state/job transition where feasible.

### ReconcilePublishOutcome
Input:
- post-submitted evidence
- current external/worker evidence

Output:
- CONFIRMED_SUCCESS
- CONFIRMED_FAILURE_SAFE_TO_RETRY
- OUTCOME_UNKNOWN
- NEEDS_HUMAN

Only `CONFIRMED_FAILURE_SAFE_TO_RETRY` may permit a new submit attempt under policy.

## 12. Scene Engine Contracts

### ObserveScene
Input is a normalized UISnapshot from UIAutomationPort, not raw framework-specific object.

UISnapshot may contain:
- package/activity metadata;
- semantic element observations;
- visible text/content descriptions;
- hierarchy relationships;
- dialogs/system state;
- adapter metadata.

### RecognizeScene
Output:
- scene_id
- confidence
- matched positive indicators
- matched negative indicators
- classification: CONFIRMED | PROBABLE | AMBIGUOUS | UNKNOWN

Business action requires configured sufficient recognition.

### PlanNextAction
Input:
- workflow/job context
- recognized Scene
- process checkpoint

Output:
- logical Action + Element target + expected transition.

It does not return raw XPath/coordinates.

### VerifyTransition
Input:
- previous Scene
- action
- observed next Scene
- expected transition

Output:
- SUCCESS
- KNOWN_ALTERNATIVE
- RECOVERABLE_MISMATCH
- AMBIGUOUS
- FAILED

### PlanRecovery
Output:
- REOBSERVE
- LOCAL_RECOVERY
- NAVIGATE_SAFE_ANCHOR
- CONTROLLED_RESTART
- HUMAN_TAKEOVER

Recovery budget is explicit in context/policy.

## 13. Port Contracts

### Repository Ports
Semantic methods; implementation must preserve transaction/concurrency semantics.

### ProductSourcePort
Returns normalized source observations or explicit schema/session errors; never silently returns empty success when source structure is unrecognized.

### AffiliateBrowserPort
Performs bounded platform interactions/observations and reports account/session context.

### DeviceTransportPort
Device discovery/lifecycle/basic control.

### UIAutomationPort
- capture normalized snapshot;
- resolve logical element using selector profile;
- execute bounded action;
- return evidence/result.

### ScreenStreamPort
Operational stream lifecycle only; no business-state authority.

### MediaProbePort
Deterministic metadata/extraction/hash/fingerprint primitives as selected.

### ClockPort
Returns controllable current time.

### EventPublisherPort
Publishes telemetry/domain integration events without becoming durability authority unless explicitly designed as such.

## 14. DTO Separation

Use separate models for:
- API DTO;
- application command/query;
- domain entity/value object;
- persistence ORM model;
- UI read model.

They may share fields but are not the same object by default.

This prevents transport/storage/presentation changes from contaminating domain rules.

## 15. Contract Test Requirement

Every concrete adapter used in production must pass a contract suite for behavior that the port guarantees.

Examples:
- SQLiteRepository and PostgresRepository satisfy same repository semantics;
- fake and concrete UIAutomation adapters produce compatible normalized result forms;
- browser adapter emits explicit schema-changed error rather than false empty success.

## 16. Versioning

Breaking public API/worker payload changes require new schema/API version or explicit compatibility translator.

Domain internal refactors do not require public version change if semantic contract is unchanged.

Persist model/ruleset/selector/algorithm versions alongside decisions where later audit/reproduction depends on them.