# Program 3 — Automated Test Architecture

Status: IMPLEMENTATION HANDOFF
Date: 2026-09-04

## Goal

Critical Program 3 behavior must be testable without physical Android, UI or live Shopee.

## Test pyramid

1. Unit: duplicate policy, plan validation, device admission, scene recognition, transition/recovery, reconciliation policy.
2. Component: Program2 handoff -> plan -> job -> scripted Scene workflow -> submit guard.
3. Contract: job/worker envelopes, pre-submit, POST_SUBMITTED, reconciliation.
4. Integration: SQL repositories/Alembic/API.
5. Resilience: worker kill, device disconnect, ACK loss, restart after submit, stale lease, duplicate submit event.
6. Deterministic Android fixture E2E using ScriptedUIAutomationAdapter.
7. Real-device laboratory gate.

## Mandatory adversarial cases

- invalid/stale Program2 handoff;
- video already published;
- same SHA under different video id;
- offer/link stale before submit;
- wrong account/job/lease;
- device unauthorized/offline/already-owned;
- current Scene UNKNOWN/AMBIGUOUS;
- expected transition mismatch;
- recovery budget exhausted;
- duplicate POST_SUBMITTED event;
- process killed immediately after POST_SUBMITTED;
- success signal lost;
- outcome unknown after restart;
- attempted second SUBMIT without explicit safe-to-retry decision;
- duplicate confirmed-success race;
- UI closed/restarted during execution.

## Quality gates

- Ruff/static architecture checks;
- Program3 conformance executable;
- named invariant tests;
- >=95% branch coverage for governed core scope;
- SQLite migration/repository >=95%;
- deterministic Scene/worker fixture tests;
- stress smoke;
- unresolved CRITICAL/HIGH = 0.
