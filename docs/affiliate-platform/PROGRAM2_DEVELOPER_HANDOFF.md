# Program 2 — Developer Handoff

Status: ENGINEERING COMPLETE BASELINE / PRODUCTION EVIDENCE GATED
Date: 2026-09-05

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

## Verified implementation baseline

Implemented and verified:
- typed Program 1 QualifiedOpportunity admission;
- Program 2 discovery jobs/work packages on Shared Job Engine;
- job/worker/lease/account/session-bound observation provenance;
- OfferFeatureSnapshot, qualification and deterministic durable OfferSelectionDecision;
- SQL/in-memory decision/work/artifact repositories and migrations;
- freshness and evidence sufficiency gates;
- AffiliateLinkArtifact validation;
- typed Program3OfferHandoff;
- Program 2 conformance and >=95% platform quality gates;
- deterministic Program 1 -> Program 2 -> Program 3 closed-loop contract.

Current engineering maturity score: **95.0 / 100**. See `PROGRAMS_1_2_3_ENGINEERING_MATURITY_SCORECARD_2026-09-05.md`.

Remaining work is primarily live-platform evidence and operator/product hardening, not missing core commercial authority.

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

The current engineering completion target is achieved at **95.0 / 100**.

Future work must preserve this baseline while promoting individual live Shopee profiles/adapters through controlled evidence. A production-evidence gap is not permission to weaken provenance, idempotency, Shared Job authority or CI gates.
