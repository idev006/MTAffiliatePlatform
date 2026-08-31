# Canonical Data Model Baseline

Status: IMPLEMENTATION HANDOFF BASELINE
Date: 2026-08-31

## 1. Purpose

Define the conceptual data model and ownership rules before ORM implementation. This document is authoritative at the semantic level; SQLAlchemy models and Alembic migrations must conform to it.

## 2. Data Modeling Principles

1. Identity is separate from observation/history.
2. Workers report facts; Back Office owns canonical business state.
3. Shared Core `jobs` is the sole executable job lifecycle SSOT.
4. Current projections may coexist with append-oriented history, but history must not be silently destroyed.
5. Independent lifecycles use separate state fields/entities rather than one overloaded `status`.
6. Every critical mutable aggregate uses concurrency/version semantics where concurrent updates are possible.
7. External provenance is retained where it affects meaning.
8. Null/unknown/not-applicable must be distinguishable where business logic requires it.
9. Database constraints enforce critical invariants in addition to application validation.
10. Portable SQLite and Farm PostgreSQL must preserve the same domain semantics.

## 3. Shared Core

### workers
Conceptual fields:
- worker_id
- worker_type
- installation_id
- host_id nullable
- version
- capabilities
- health_state
- enrolled_at
- last_seen_at
- version_no

Worker identity is not authentication credential.

### device_hosts
- host_id
- installation_id
- hostname/label
- capabilities
- resource profile
- health_state
- last_seen_at

### devices
- device_id
- host_id
- transport_identity/serial
- label
- platform
- app/runtime metadata
- health_state
- capability snapshot
- version_no

### jobs
Authoritative lifecycle table.

- job_id
- job_type
- domain
- state
- priority
- payload/reference
- idempotency_key
- assigned_worker_id nullable
- lease_token nullable
- lease_until nullable
- attempt_no
- job_version
- created_at
- started_at nullable
- completed_at nullable
- failure/error reference nullable

Critical invariant: one executable job has at most one valid active lease.

### job_events
Append-oriented lifecycle/audit events:
- event_id
- job_id
- event_type
- sequence/version
- source
- payload/evidence reference
- emitted_at
- committed_at

### job_checkpoints
- checkpoint_id
- job_id
- checkpoint_type
- checkpoint_payload/reference
- worker_id
- created_at
- job_version

### ingestion_batches
- batch_id
- worker_id
- source/context
- schema_version
- sequence range
- received_at
- committed_at
- ack_state
- idempotency identity

### configuration_versions
- config_version_id
- scope
- key/ruleset identity
- version
- effective_from
- payload/reference
- created_by/source
- created_at

## 4. Product Domain

### products
Canonical identity/projection.

Candidate identity:
`(platform, shop_id, item_id)` pending real Shopee validation.

Fields conceptually:
- product_id internal
- platform
- shop_id
- item_id
- canonical title/current projection
- canonical shop/seller reference
- lifecycle/availability projection
- created_at
- updated_at
- version_no

### product_observations
Append-oriented observed facts:
- observation_id
- product_id
- observed_at
- worker/source/context provenance
- title
- price/current price
- sold signal
- rating/review/seller signals where observed
- promotion fields
- category/context
- raw evidence/reference where retained
- schema_version

Unknown fields must remain unknown, not coerced to zero.

### product_scores
Versioned scoring output:
- product_score_id
- product_id
- scoring_model_id/version
- feature snapshot/reference
- total_score
- component scores
- explanation/reasons
- calculated_at

### shortlist_entries
- shortlist_entry_id
- campaign_id
- product_id
- score reference
- decision_state
- approved/rejected by/source
- decision reason
- created_at/updated_at

## 5. Affiliate Offer Domain

### affiliate_accounts
Semantic account identity/provenance only; secrets stored separately.

- affiliate_account_id
- platform
- account label/external identity where permitted
- state
- created_at

### affiliate_session_contexts
Do not store raw secrets in ordinary domain records.

- session_context_id
- affiliate_account_id
- worker/context reference
- validity/freshness metadata
- observed_at

### affiliate_offers
Canonical offer identity where determinable:
- offer_id
- product_id
- platform
- seller/shop identity
- external offer/link identity where available
- current projection fields
- version_no

### affiliate_offer_observations
Append-oriented observed candidate facts:
- offer_observation_id
- offer_id/product_id
- affiliate_account_id/session_context_id where relevant
- observed commission/rate/value
- price/promotion/eligibility signals
- freshness/availability
- source provenance
- observed_at
- schema_version

### offer_scores
- offer_score_id
- offer_id
- product_id
- account context if required
- scoring_model/version
- component scores
- total score
- explanation
- calculated_at

### offer_selections
Versioned decision, not permanent Product identity:
- selection_id
- product_id
- preferred_offer_id
- backup_offer_ids/reference
- ruleset/scoring version
- valid_from
- invalidated_at nullable
- decision source

### affiliate_link_artifacts
- artifact_id
- offer_id/selection_id
- platform/account context
- artifact/link reference
- generated/imported_at
- freshness/expiry metadata
- provenance

## 6. Content / Video Domain

### videos
Identity and durable media registration:
- video_id
- source reference/path logical identifier
- original filename metadata
- duration
- dimensions
- media metadata
- exact_sha256
- ingestion_status
- validation_status
- created_at
- version_no

Do not use filename as identity.

### video_fingerprints
- fingerprint_id
- video_id
- algorithm
- algorithm_version
- segment/window definition
- fingerprint data/reference
- created_at

### video_duplicate_evaluations
- evaluation_id
- video_id
- compared_video_id/reference set
- algorithm/threshold version
- classification: EXACT / NEAR / UNIQUE / REVIEW
- score/distance
- evaluated_at

### product_video_links
Product 1:N Video relationship:
- product_video_link_id
- product_id
- video_id
- content_angle/reference
- active/version metadata

## 7. Publishing Domain

### publish_plans
Immutable/versioned plan snapshot before execution:
- publish_plan_id
- platform
- account_id
- video_id
- target product/offer references
- caption/tag references
- basket capacity/rule version
- duplicate rule version
- validation state
- created_at
- superseded_by nullable

### platform_publish_states
Separate from generic Video state:
- platform_publish_state_id
- video_id
- platform
- account_id
- current publish_state
- current job_id nullable
- external_post_id nullable
- submitted_at nullable
- confirmed_at nullable
- version_no

### publishing_ledger
Authoritative append-oriented publication record/evidence.

- ledger_entry_id
- video_id
- platform
- account_id
- publish_plan_id
- job_id
- outcome
- external_post_id nullable
- submitted_at nullable
- confirmed_at nullable
- evidence reference
- idempotency/dedup identity
- created_at

Critical invariant: a confirmed success violating configured duplicate policy must be blocked transactionally where portable semantics permit.

### publishing_events
- event_id
- job_id/publish_plan_id
- video_id
- event_type
- Scene/process/action context where relevant
- worker_id/device_id
- evidence/error reference
- emitted_at

Examples:
`VIDEO_SELECTED`, `BASKET_ATTACHED`, `POST_SUBMITTED`, `POST_CONFIRMED`, `POST_OUTCOME_UNKNOWN`, `NEEDS_HUMAN`.

## 8. Android Scene Domain

### scene_profiles
Versioned logical Scene definition:
- scene_profile_id
- platform/app
- app version/locale/context compatibility
- scene_name
- required indicators
- positive/optional/negative indicators
- confidence policy version
- safe_anchor flag
- active/version metadata

### selector_profiles
Adapter-level implementation data, not domain business truth:
- selector_profile_id
- logical_element_id
- app/version/locale/context
- strategy type
- selector data
- priority/fallback order
- active/version metadata

### worker_scene_checkpoints
Durable where needed for resume/recovery:
- checkpoint_id
- job_id
- worker_id
- device_id
- current_scene
- previous_scene
- expected_scene
- current_process
- current_action
- confidence
- recovery_level/count
- created_at

High-frequency frame/scan data should not be written as canonical DB rows unless explicitly sampled/evidenced.

## 9. Campaign / Rules Domain

### campaigns
- campaign_id
- name
- objective
- state
- Step configuration references
- created_at/updated_at

### campaign_shards
- shard_id
- campaign_id
- scope/range
- state
- job relationship/reference

### rulesets / scoring_models
Versioned policies:
- ruleset_id/model_id
- domain
- semantic version/revision
- configuration payload/reference
- status
- created_at

Outputs always record which policy/model version produced the decision.

## 10. Transaction Boundaries

Never keep a transaction open during external/browser/device/human work.

Examples:
- claim/lease job: one short transaction;
- ACK observation batch: one short transaction after validation/commit;
- checkpoint: one short transaction;
- confirmed publish ledger + platform state + job completion: one short atomic transaction where feasible.

## 11. Concurrency

Baseline mechanisms:
- optimistic version columns for mutable aggregates;
- conditional updates;
- unique constraints for identity/idempotency/invariants;
- job leases;
- append events;
- bounded retry only for safe database conflicts/deadlocks;
- no blind retry of irreversible external actions.

## 12. Repository Boundary

Application code uses semantic repository operations, not vendor SQL.

Examples:
- reserve_job(...)
- append_product_observations(...)
- save_product_score(...)
- replace_active_offer_selection(...)
- register_video_identity(...)
- evaluate_platform_duplicate(...)
- save_publish_plan(...)
- confirm_publish_success(...)

Concrete SQLite/PostgreSQL differences stay inside persistence adapters/migrations.

## 13. Migration Requirements

Alembic revision is part of release identity.

Each migration must be reviewed for SQLite/PostgreSQL compatibility. Vendor-specific capabilities may be used only behind documented compatibility strategy.

## 14. Open Validation Items

Still not frozen:
- final Shopee Product external identity semantics;
- final Offer external identity/link semantics;
- exact Step 1->2 and Step 2->3 DTO schemas;
- exact scoring feature fields/formula;
- perceptual fingerprint algorithm/threshold;
- final Scene/selector schema after real app capture;
- final duplicate database constraint form across SQLite/PostgreSQL.

These open items must not be guessed into irreversible schema without an ADR/migration plan.