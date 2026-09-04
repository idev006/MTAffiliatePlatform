# Program 3 — Agile Kanban

Status: ENGINEERING COMPLETION BASELINE
Date: 2026-09-05

## Done / Verified

- [x] P3-001 Program2 handoff -> PublishPlan planning authority
- [x] P3-002 durable immutable PublishPlan repository/migration
- [x] P3-003 Shared publish job integration
- [x] P3-004 active job lease/account/device ownership preconditions
- [x] P3-005 durable versioned pre-submit guard decision
- [x] P3-006 durable POST_SUBMITTED boundary + Shared Job checkpoint
- [x] P3-007 reconciliation decision + no-blind-repost invariant
- [x] P3-008 confirmed-success ledger/idempotency
- [x] P3-009 Program3 conformance + CI coverage
- [x] P3-010 scripted Scene full workflow E2E
- [x] P3-011 durable execution/pre-submit/submission/reconciliation restart state
- [x] P3-012 durable one-worker-per-device ownership lease + expiry/reassignment
- [x] P3-016 full deterministic Program 1 -> Program 2 -> Program 3 closed-loop contract

## Engineering follow-up / non-blocking for current maturity baseline

- [ ] P3-013 richer operator takeover/read model
- [ ] P3-014 expanded structured observability/telemetry dashboards
- [ ] P3-015 optional novice-friendly UI shell

These are useful product/operations improvements but do not own business truth and are not allowed to weaken the verified headless control plane.

## Production evidence-gated

- [ ] P3-E01 real Shopee Scene catalog
- [ ] P3-E02 selector profiles by supported app/version/locale
- [ ] P3-E03 safe anchor paths
- [ ] P3-E04 basket capacity
- [ ] P3-E05 submit success/reconciliation evidence
- [ ] P3-E06 recovery timing/pacing budgets
- [ ] P3-E07 multi-device capacity/stream benchmark

Production-evidence cards promote adapters/policies only. They must not bypass duplicate protection, Back Office pre-submit authority, job/device leases or POST_SUBMITTED reconciliation.
