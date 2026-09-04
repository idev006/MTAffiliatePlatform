# Program 2 — Developer Handoff

Status: IMPLEMENTATION READY
Date: 2026-09-04

## Mission

Implement Affiliate Offer Intelligence as a headless, durable, evidence-first subsystem that consumes qualified Program 1 opportunities and emits validated Program 3 offer/link handoffs.

## Required reading

1. PROGRAM2_AFFILIATE_SUCCESS_STRATEGY.md
2. PROGRAM2_SYSTEM_ARCHITECTURE.md
3. PROGRAM2_UML_AND_RUNTIME_DIAGRAMS.md
4. PROGRAM2_TRACEABILITY_MATRIX.md
5. PROGRAM2_AUTOMATED_TEST_ARCHITECTURE.md
6. PROGRAM2_KANBAN.md
7. PROGRAM2_IMPLEMENTATION_CARDS.md
8. specs/AFFILIATE_OFFER_WORKER_SPEC.md
9. APPLICATION_AND_ENGINE_CONTRACTS.md
10. DATA_MODEL.md
11. TEST_STRATEGY_AND_QUALITY_GATES.md
12. ENGINEERING_GOVERNANCE.md

## Current implementation baseline

Already present:
- AffiliateOfferObservation / OfferScore / OfferSelection;
- deterministic scoring framework v0;
- in-memory and SQL repositories;
- Program2Service ranking/selection;
- API/runtime foundation;
- SQLite integration;
- synthetic affiliate export adapter/workers;
- CI coverage infrastructure.

Known gaps before 90%:
- typed Program1 qualified intake authority;
- Program2 discovery jobs/work packages;
- job/worker/lease provenance on observations;
- explicit OfferFeatureSnapshot/Qualification/SelectionDecision;
- deterministic injected clock/ID in selection;
- durable selection decision version/evidence refs;
- freshness gate;
- artifact/link entity + validation/reconciliation;
- typed Program3 handoff;
- worker restart/export ambiguity resilience;
- Program2-specific conformance gate;
- evidence-validated live Shopee profiles.

## Architecture non-negotiables

- UI never ranks/selects.
- Worker never owns commercial decision.
- Shared Job Engine is sole job lifecycle.
- account/session provenance is separate from worker identity.
- no live Shopee assumptions without evidence.
- no bypass of CAPTCHA/auth/anti-abuse controls.
- no external waits inside SQL transactions.
- selection/export retries require idempotency/reconciliation.
- fake first, real adapter second.

## Developer completion target

Program 2 may score >=90 only when:
- all P0/P1 implementation cards are complete;
- critical use cases pass;
- coverage/process gates pass;
- restart/replay/ambiguity tests pass;
- documentation/code traceability is current;
- remaining production-specific evidence gates are explicitly isolated rather than guessed.
