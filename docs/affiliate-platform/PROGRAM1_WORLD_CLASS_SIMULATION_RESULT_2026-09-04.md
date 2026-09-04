# Program 1 World-Class Simulation Result — 2026-09-04

Status: SIMULATION BASELINE VERIFIED
Production readiness: NOT YET CLAIMED

## Authoritative verification

GitHub Actions run: 33880974475
Verification PR: #7 `verify(program1): world-class green gate`
Verified snapshot base: `ac104a56c0e821a9a1e4eab444319eae902e8cf4`

All required CI jobs passed:
- Back Office core/contract: 157 passed, 46 deselected; branch coverage 95.85%.
- SQLite/Alembic integration: 45 passed; branch coverage 95.20%.
- Program 1 extension: 67 passed, 0 failed.
- Stress: 1 passed, 202 deselected.
- Ruff: passed.
- No quality threshold was weakened.

## Simulation coverage

The deterministic headless Program 1 simulation verifies:
1. AffiliateSuccessHypothesis + SignalRequirements -> approved DiscoveryPlan.
2. Durable strategy-to-work package.
3. Durable Shared Job creation and idempotency.
4. Worker Registry as capability authority.
5. Compatible job leasing and one-active-lease invariant.
6. Job start / lease renewal / state-before-lease mutation guards.
7. Synthetic product observation ingestion and batch ACK semantics.
8. Durable checkpoint.
9. Deterministic Product Intelligence shortlist.
10. VERIFYING -> COMPLETED.
11. Full database/runtime recomposition and restart.
12. Restored job state, event history, checkpoint, strategy package and observations.
13. Identical shortlist after restart.
14. Duplicate batch replay.
15. Batch-ID collision with changed payload.
16. Duplicate job request without duplicate work.
17. Expired unsafe execution -> NEEDS_HUMAN.
18. PAUSED / NEEDS_HUMAN state barriers.
19. Stale lease / wrong worker / capability mismatch rejection.
20. Repository conflict, stale version and atomic state+event behavior.
21. API lease-next, lease, renew, start, checkpoint, pause/resume, verify and complete contracts.
22. Extension outbox/ACK, registry, heartbeat, pagination, parsing and transport regression tests.

## Defects found and CAPA during verification

- Lease expiry boundary ambiguity -> exact expiry is treated as expired.
- State/event split persistence risk -> atomic state + event repository contract.
- Unvalidated model-copy transitions -> transitions are revalidated through JobRecord.
- Worker self-asserted capabilities -> Worker Registry is authoritative.
- Multiple active leases per worker -> prohibited by Shared Job Engine.
- Durable job with non-durable payload reference -> durable Program 1 strategy-work repository added.
- SQL parent/event flush ordering -> explicit parent flush inside one transaction.
- State/lease error precedence ambiguity -> state validity is checked before lease ownership.
- CI lint diagnostics were insufficient -> Ruff --diff retained for exact remediation.
- New lifecycle surface lowered branch coverage -> adversarial tests added; threshold remained 95%.

## Remaining release blockers

A green simulation baseline is not equivalent to production readiness.

1. The Program 1 MV3 background worker does not yet directly consume the Shared Job lifecycle (lease-next/start/renew/checkpoint/verify/complete). The Side Panel still owns significant auto-run orchestration.
2. MV3 service-worker termination/restart recovery must be verified end-to-end with a real Chromium-family browser while the Side Panel is closed.
3. Real Shopee DOM/selectors/surface signatures and marketplace signals remain evidence-gated.
4. Real marketplace pacing, anti-bot behavior, identity semantics and production scoring policy remain evidence-gated.

Release rule: do not mark Program 1 production-ready until these remaining gates are closed with runtime evidence.
