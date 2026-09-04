# Program 3 — Developer Handoff

Status: IMPLEMENTATION READY
Date: 2026-09-04

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

## Existing implementation baseline

Already present:
- PublishPlan/ApprovedOfferRef/PublishingLedgerEntry;
- duplicate guard;
- in-memory/SQL publishing ledger;
- Scene Engine;
- Scene workflow engine;
- Program3WorkerExecutor;
- Program3WorkflowRunner;
- Scripted Android adapters/fakes;
- DeviceHostEngine;
- Android device/scene tests;
- basic Program3 API/runtime profile.

## Highest priority gaps

- typed Program2OfferHandoff -> PublishPlan planning authority;
- immutable/durable plan repository;
- Shared publish job integration;
- active worker/device/account/lease validation;
- versioned pre-submit decision;
- durable POST_SUBMITTED record;
- explicit reconciliation decision model;
- confirmed-success atomic/idempotent ledger semantics;
- no-resubmit guard after ambiguous submit;
- Program3 conformance/CI gate;
- deterministic full fixture E2E;
- production evidence gates for real Shopee Android.

## Non-negotiables

- UI/Android adapter never owns duplicate/publish outcome authority.
- Unknown Scene means no business action.
- no blind retry after POST_SUBMITTED.
- no long SQL transaction across Android/network/human work.
- Shared Job Engine remains lifecycle SSOT.
- fake/scripted adapters first, real device second.
