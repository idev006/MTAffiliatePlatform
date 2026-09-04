# Program 2 — Automated Test Architecture

Status: IMPLEMENTATION HANDOFF
Date: 2026-09-04

## Goal

Program 2 critical behavior must be fully testable without live Shopee, UI or external network.

## Pyramid

1. Unit: identity, freshness, qualification, deterministic selection, policy validation.
2. Component: Program1 handoff -> discovery job -> observations -> selection.
3. Contract: worker envelopes, account provenance, export commands, Program3 handoff.
4. Integration: SQLAlchemy/Alembic/API.
5. Resilience: lost ACK, duplicate batch, stale lease, restart, ambiguous export.
6. Deterministic browser fixture E2E.
7. Live evidence laboratory — separate, evidence-gated.

## Mandatory adversarial cases

- raw product bypasses Program1 gate;
- missing affiliate_account_id where required;
- source worker/job mismatch;
- wrong/stale lease token;
- duplicate observation id with changed payload;
- same offer across two accounts is not collapsed incorrectly;
- stale offer selected;
- unavailable preferred offer;
- backups deterministic;
- no eligible offer;
- export command replay;
- artifact reported for wrong selection/job/account;
- download absent;
- export outcome unknown;
- worker restart after EXPORT_STARTED;
- backend restart after ACK;
- UI closed while worker active.

## Quality gate

- Ruff/static architecture checks;
- named critical invariant tests;
- >=95% branch coverage for governed core scope;
- SQLite migration/repository coverage >=95%;
- deterministic extension suite;
- stress smoke;
- no CRITICAL/HIGH unresolved finding.
