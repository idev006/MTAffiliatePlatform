# Program 2 + Program 3 Foundation Verification Report

Date: 2026-08-31
Status: FOUNDATION / LABORATORY VERIFIED — REAL PLATFORM GATES REMAIN
Governing cycle: `DEVELOPMENT_CYCLE_STANDARD.md`

## 1. Scope of This Verification

This report covers behavior that can be implemented and verified without guessing real Shopee browser structures or Android application selectors.

The verified scope includes:
- Program 2 headless Offer eligibility/scoring/selection framework;
- Program 2 account-context separation;
- Program 2 in-memory and SQLAlchemy/SQLite repositories;
- Program 2 worker command/batch contracts, deterministic fake worker and filesystem outbox;
- Program 2 Affiliate Link/export artifact contracts;
- Program 2 synthetic export parser laboratory and malformed/cross-account validation;
- Program 3 immutable PublishPlan and publishing guard;
- Program 3 durable Publishing Ledger;
- Program 3 deterministic Scene recognition and workflow transition/recovery engines;
- Program 3 Device Host ownership/lease rules;
- Program 3 host resource admission/degradation policy;
- Program 3 replaceable Android ports and scripted Android laboratory adapter;
- Program 3 headless Observe -> Recognize -> Validate -> Act -> Verify -> Checkpoint executor;
- Program 3 full scripted multi-scene VIDEO_SOURCE -> PUBLISH_SUCCESS workflow laboratory;
- conservative POST_OUTCOME_UNKNOWN reconciliation rules;
- FastAPI foundation contracts for Program 2/3;
- Alembic migration for Program 2/3 durable foundation tables;
- typed TOML configuration for configurable Program 2 policy and Program 3 policy version.

## 2. Program 2 Status

### Verified foundation/laboratory slices
- P2-VS1: Product/Offer contract-driven fake selection flow — VERIFIED.
- P2-VS2: SQLite durable Offer observations/selections, restart and idempotent replay — VERIFIED.
- P2-VS3: worker protocol + deterministic fake worker + local atomic file outbox — VERIFIED.
- P2-VS4A: Affiliate Link/export artifact contracts and selection/link validation — VERIFIED.
- P2-VS4B: parser port + synthetic JSON parser/fixture laboratory — VERIFIED.

The synthetic parser is explicitly a contract/golden-fixture laboratory tool and does not claim compatibility with a real Shopee export format.

### Not production-frozen
- canonical Shopee Offer identity;
- Offer Scoring Model v1 business formula;
- real Affiliate account/session behavior;
- real export/download parser profiles;
- browser DOM/selectors/schema profiles;
- endurance/capacity against real Shopee.

## 3. Program 3 Status

### Verified foundation/laboratory slices
- P3-VS1: PublishPlan -> duplicate gate -> ledger behavior — VERIFIED.
- P3-VS2: fixture-driven Scene recognition, transition validation and bounded recovery — VERIFIED.
- P3-VS3: device ownership/lease and resource admission foundation — VERIFIED.
- P3-VS4A: scripted Android adapter + headless worker action execution + ambiguous-outcome reconciliation — VERIFIED.
- P3-VS4B: full scripted multi-scene publishing workflow — VERIFIED.

### Safety invariants verified in foundation
- unknown/ambiguous Scene blocks business action;
- action must be allowed from the confirmed current Scene;
- next Scene must be verified before checkpoint;
- full scripted workflow stops at the first unverified transition;
- same-video confirmed publish on the same platform is blocked;
- POST_OUTCOME_UNKNOWN / NEEDS_HUMAN blocks blind repost;
- destructive-action uncertainty escalates to reconciliation/human control rather than restart/repost;
- one active worker ownership is enforced per device in the domain admission model;
- ADB UNAUTHORIZED is classified as human-required;
- resource pressure stops new admission rather than sacrificing correctness.

### Not production-frozen
- real Shopee Scene signatures/selectors;
- Safe Anchor evidence;
- physical ADB/uiautomator2 behavior;
- post-submit reconciliation evidence source against the real platform;
- perceptual video fingerprint algorithm/threshold;
- basket capacity by app/account/version;
- screen-stream/device-host capacity at 10/20/50/100 devices;
- real device disconnect/crash/endurance behavior.

## 4. Persistence and Migration

Alembic revision `0002_program2_program3` adds durable foundation tables for:
- `affiliate_offer_observations`;
- `affiliate_offer_selections`;
- `publishing_ledger`.

SQLite restart tests verify Program 2 Offer/Selection state survives repository recreation and Program 3 Publishing Ledger history continues to enforce duplicate prevention after restart.

Program 2 and Program 3 are composed into the portable runtime through SQLAlchemy repositories without moving business logic into ORM models.

## 5. API Foundation

Current foundation endpoints include:
- `POST /api/v1/program2/observations`;
- `GET /api/v1/program2/products/{product_id}/offers`;
- `POST /api/v1/program2/products/{product_id}/selection`;
- `POST /api/v1/program3/publish/evaluate`;
- `POST /api/v1/program3/publish/status`.

Contract tests cover success, collision/no-offer conflict semantics, duplicate/unknown publish blocking and malformed payload validation.

## 6. Configuration and Hard-Coding Review

Program 2 scoring weights and backup count are typed configuration values backed by TOML. Program 3 carries a versioned duplicate-policy identifier.

A proposed `block_ambiguous_outcomes` configuration toggle was removed during review because ambiguous publish blocking is a safety invariant, not an operator preference. Configuration must not provide a bypass around a governing correctness invariant.

Real Shopee selectors, scoring v1 values, basket capacity and retry/capacity thresholds remain outside hard-coded domain logic until validated by evidence.

## 7. Automated Verification Evidence

### Earlier foundation baseline
GitHub Actions CI #155 for code head `4f33f3b74a5e11880922b928a7da0e383147fdb8` completed successfully with Core, SQLite/Alembic and Stress jobs green.

### Parser + full scripted workflow cycle
CI #165 on head `7d45b77e7810c9d08bdb2988ebfc138138116cdb` found three Ruff findings in newly added laboratory code/tests. SQLite and Stress passed, while Core stopped at lint before pytest. The findings were:
- non-list JSON root raised `ValueError` instead of the lint-preferred `TypeError`;
- import ordering in the full scripted workflow test;
- successive-pair iteration used `zip` instead of `itertools.pairwise`.

The artifacts were corrected without lowering or bypassing Ruff.

GitHub Actions CI #168 for code head `f2b00b24fcb5c6573ae9bf77c851e7924d3b024f` completed successfully. This verifies the synthetic Program 2 export parser laboratory and the full scripted Program 3 workflow together with the existing repository gates.

CI coverage gates remain at 95% for the selected risk-bearing core and persistence/composition scopes. The threshold was not reduced to obtain a passing build.

Documentation-only Codex handoff commits made after this code head do not change business/runtime code; current HEAD CI should still be inspected as normal repository practice.

## 8. Readiness Decision

### GO
- continue Program 2/3 headless/application/persistence/protocol development;
- use current contracts for parallel integration;
- harden synthetic/golden fixtures and artifact integrity;
- expand scripted failure/replay/restart matrices;
- integrate Program 2/3 execution with Shared Job Engine authority;
- add PostgreSQL compatibility and concurrency suites;
- build controlled browser/device laboratories;
- add real evidence behind adapters/config profiles only after capture and review.

### HOLD / EVIDENCE REQUIRED
- production Offer scoring/identity claims;
- real Shopee browser parser/selector freeze;
- real Android Scene/selector freeze;
- irreversible real publishing automation beyond controlled laboratory validation;
- capacity/scale claims.

## 9. Codex Continuation Handoff

Codex Work Desktop / coding agents must follow:
- root `AGENTS.md`;
- `CODEX_WORK_DESKTOP_HANDOFF.md`;
- `CODEX_NEXT_WORK_QUEUE.md`;
- `CODEX_START_PROMPT.md`.

Verified status follows evidence, not merely latest-commit chronology. Current HEAD/CI must be checked at the start of each implementation session.

## 10. Quality Assessment

For the foundation/laboratory scope covered by this report:
- unresolved CRITICAL design issues: 0;
- unresolved HIGH design issues: 0;
- latest verified runtime-code baseline: CI #168 / `f2b00b24fcb5c6573ae9bf77c851e7924d3b024f` — PASS.

This does not assert production readiness for Shopee-specific behavior that requires browser/account/device evidence.
