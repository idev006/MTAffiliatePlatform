# Program 3 — Developer Handoff

Status: ENGINEERING COMPLETE BASELINE / PRODUCTION EVIDENCE GATED
Date: 2026-09-05

## Mission

Implement a durable, duplicate-safe, Scene-aware Android publishing system that consumes validated Program2 handoffs and produces auditable confirmed publication outcomes without blind retries.

## Required reading

1. PROGRAM3_PUBLISHING_SUCCESS_AND_SAFETY_STRATEGY.md
2. PROGRAM3_SYSTEM_ARCHITECTURE.md
3. PROGRAM3_UML_AND_RUNTIME_DIAGRAMS.md
4. PROGRAM3_TRACEABILITY_MATRIX.md
5. PROGRAM3_AUTOMATED_TEST_ARCHITECTURE.md
6. PROGRAM3_KANBAN.md
7. PROGRAM3_IMPLEMENTATION_CARDS.md
8. PROGRAM3_UX_AND_OPERATOR_EXPERIENCE.md
9. specs/CONTENT_PUBLISHING_SPEC.md
10. specs/ANDROID_SCENE_ENGINE_SPEC.md
11. APPLICATION_AND_ENGINE_CONTRACTS.md
12. DATA_MODEL.md
13. TEST_STRATEGY_AND_QUALITY_GATES.md

## Verified implementation baseline

Implemented and verified:
- typed Program2OfferHandoff -> immutable/durable PublishPlan planning authority;
- Shared PUBLISH_CONTENT job lifecycle;
- SQL/in-memory execution repositories and Alembic migrations;
- durable Program 3 device registry and optimistic one-worker ownership leases;
- active Shared Job lease + active device lease + target account + Scene readiness pre-submit checks;
- durable PreSubmitDecision owned by Back Office;
- POST_SUBMITTED execution record + Publishing Ledger state + Shared Job checkpoint;
- explicit CONFIRMED_SUCCESS / CONFIRMED_FAILURE_SAFE_TO_RETRY / OUTCOME_UNKNOWN / NEEDS_HUMAN reconciliation;
- no blind resubmit after ambiguous submission;
- Scene Engine / workflow engine / ScriptedAndroidAdapter;
- deterministic Android-to-ledger fixture E2E;
- deterministic Program 1 -> Program 2 -> Program 3 closed-loop contract;
- Program 3 conformance and >=95% governed quality gates.

Latest verified platform CI baseline is recorded in `PROGRAMS_1_2_3_ENGINEERING_MATURITY_SCORECARD_2026-09-05.md`.

## Remaining work is production evidence, not missing core authority

Still evidence-gated:
- real Shopee Scene signatures/selectors;
- safe-anchor paths;
- basket capacity by app/account/version;
- actual publish-success/reconciliation evidence;
- pacing/recovery budgets and multi-device capacity benchmarks;
- optional operator UI/telemetry enrichment.

## Non-negotiables

- UI/Android adapter never owns duplicate/publish outcome authority.
- Unknown Scene means no business action.
- no blind retry after POST_SUBMITTED.
- no long SQL transaction across Android/network/human work.
- Shared Job Engine remains lifecycle SSOT.
- fake/scripted adapters first, real device second.
