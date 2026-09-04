# Program 3 — Implementation Cards

Status: IMPLEMENTATION READY
Date: 2026-09-04

## P3-001 Publish planning
Input: Program3OfferHandoff + registered content identity + account/caption metadata.
Output: versioned immutable PublishPlan.
Acceptance: wrong/stale handoff rejected; offer/link refs traceable.

## P3-002 Durable plan
Persist PublishPlan separately from executable job lifecycle.
Acceptance: restart-safe, idempotent semantic key, conflict protected.

## P3-003 Shared publish job
Create/queue PUBLISH_CONTENT job referencing durable plan.
Acceptance: capability-based lease; no duplicate lifecycle owner.

## P3-004 Execution authorization
Validate worker lease, account context and device ownership before critical commands.
Acceptance: stale/forged lease, wrong device/account blocked.

## P3-005 Pre-submit guard
Recheck duplicate, handoff freshness, plan identity, current lease and READY_TO_PUBLISH evidence.
Output: ALLOW_SUBMIT or typed rejection/NEEDS_HUMAN.

## P3-006 POST_SUBMITTED
Record an idempotent durable boundary before treating the publish attempt as potentially externally committed.
Acceptance: restart retains boundary; duplicate report safe.

## P3-007 Reconciliation
Output: CONFIRMED_SUCCESS / CONFIRMED_FAILURE_SAFE_TO_RETRY / OUTCOME_UNKNOWN / NEEDS_HUMAN.
Acceptance: OUTCOME_UNKNOWN never permits blind submit.

## P3-008 Confirmed ledger
Persist final success with video/platform/account/plan/job/offer/handoff evidence.
Acceptance: duplicate confirmed success conflict blocked.

## P3-009 CI/conformance
Program3 executable conformance + >=95% governed branch coverage.

## P3-010 Scripted E2E
Program2 handoff -> plan -> job -> scripted Scenes -> pre-submit -> submitted -> confirmed success without physical device.
