# Program 2 — Implementation Cards

Status: IMPLEMENTATION READY
Date: 2026-09-04

## P2-001 Qualified intake
Objective: admit only Program1 QualifiedOpportunityHandoff.
Acceptance: raw/unqualified/stale handoff rejected; idempotent intake; campaign/hypothesis/decision provenance retained.

## P2-002 Discovery job
Objective: persist OfferDiscoveryPlan and create OFFER_DISCOVERY Shared Job.
Acceptance: capability-based lease; work package survives restart; no second lifecycle owner.

## P2-003 Observation provenance
Objective: candidate batches carry job_id/worker_id/lease_token plus affiliate-account context.
Acceptance: stale/forged envelope rejected before persistence; replay idempotent.

## P2-004 Feature snapshot
Objective: derive account-scoped freshness/economic evidence without invented total score.
Acceptance: null/unknown explicit; evidence refs/policy version retained.

## P2-005 Qualification/selection
Objective: determine SELECT_NOW/WATCH/HOLD/NEEDS_EVIDENCE and preferred/backups deterministically.
Acceptance: same facts/context/policy -> same result; no uuid/time globals in domain decision.

## P2-006 Durable decision
Objective: persist OfferSelectionDecision with evidence/policy/account/job provenance.
Acceptance: restart-safe; semantic conflict protected; latest decision query deterministic.

## P2-007 Program3 handoff
Objective: emit typed handoff only for fresh, validated selection/link.
Acceptance: stale/unvalidated decisions blocked.

## P2-008 Conformance/CI
Objective: executable gate checks docs/runtime/contracts/tests.
Acceptance: >=95% governed core branch coverage; >=95% SQL scope; lint; stress.

## P2-009 Link artifact
Objective: model export/link artifact and validation evidence.
Acceptance: artifact bound to selection/job/account; secrets excluded.

## P2-010 Export reconciliation
Objective: export retries safe.
Acceptance: EXPORT_STARTED survives restart; unknown outcome never blindly repeats.

## P2-011 Worker lifecycle
Objective: MV3 worker owns background job execution.
Acceptance: UI closed/restart continues/reconciles from durable checkpoint.

## P2-012 Fixture E2E
Objective: deterministic extension + mock Back Office + fixture offer pages.
Acceptance: discovery -> ACK -> selection command -> export artifact -> complete without live Shopee.

## Definition of Done

Every card must satisfy governing DoD and update traceability/Kanban/evidence.
