# Program 1 — Agile Kanban Board

Status: ACTIVE
Date: 2026-09-04
Method: DOCUMENT-DRIVEN / AGILE KANBAN / SMALL VERTICAL SLICES

## 1. Flow

`BACKLOG -> ANALYSIS -> DESIGN/CONTRACT -> READY -> IN DEV -> CODE REVIEW -> VERIFY -> DONE`

Exception:
`BLOCKED | NEEDS_DECISION | NEEDS_REAL_DATA | NEEDS_HUMAN`

## 2. WIP Policy

Recommended WIP limits:
- ANALYSIS: 3
- DESIGN/CONTRACT: 2
- IN DEV: 2
- CODE REVIEW: 2
- VERIFY: 2

Prefer finishing an active card before opening another card in the same dependency chain.

Parallel work is allowed when boundaries are independent, especially:
- worker-runtime track;
- opportunity-intelligence track;
- test/CI track.

## 3. Iteration Philosophy

Kanban is continuous, but Program 1 improves through repeated learning loops:

```text
Observe problem/opportunity
 -> Analyze
 -> Update design
 -> Implement smallest slice
 -> Verify
 -> Collect feedback/evidence
 -> Learn
 -> Improve documents/tests
 -> Next slice
```

No fixed "final architecture" is assumed. Architecture evolves through versioned decisions while preserving ownership/invariants.

## 4. Current Board

### VERIFY

#### P1-A — Strategy-to-Work Contract
Outcome:
- affiliate hypothesis, signal requirement and discovery plan contracts exist;
- planner rejects undeclared signals.

Evidence:
- source/tests added;
- CI coverage scope added.

Verification state:
- isolated smoke PASS;
- repository CI evidence still requires current GitHub run confirmation;
- move to DONE only after authoritative repository gates are confirmed and recorded.

### READY / NEXT

#### P1-B — Shared Job Lifecycle for Program 1
Goal:
Back Office + Shared Job Engine own Program 1 long-running lifecycle.

Acceptance:
- lease/renew/checkpoint/complete;
- pause/resume;
- UI close does not stop durable job;
- MV3 restart can reconcile canonical job state;
- stale lease result rejected;
- deterministic tests.

#### P1-C — Worker Delivery Reliability
Goal:
Make outbox and ACK semantics robust.

Acceptance:
- structured error categories;
- duplicate/replay ACK semantics explicit;
- lost ACK replay safe;
- permanent invalid message cannot block valid queue forever without explicit quarantine policy;
- ambiguous ACK preserved for reconciliation;
- tests.

#### P1-D — Collection Router and Profile Contract
Goal:
Separate collection profiles from monolithic content logic.

Acceptance:
- router interface;
- profile metadata/version/evidence state;
- fixture profile;
- Shopee lab profiles remain evidence-gated;
- unsupported/ambiguous selection fails closed;
- fixture contract tests.

### READY IN PARALLEL AFTER P1-A

#### P1-E — Opportunity Feature Snapshot
Goal:
Create versioned derived features independent of browser worker.

Acceptance:
- feature snapshot domain model;
- evidence refs;
- unknown/data-sufficiency semantics;
- fake deterministic features;
- repository port/in-memory implementation;
- tests;
- no production weights.

#### P1-F — Opportunity Decision / Thesis
Depends: P1-E.

Acceptance:
- qualification;
- Opportunity Thesis;
- risk/uncertainty;
- action vocabulary;
- versioned decision;
- deterministic tests;
- NEEDS_EVIDENCE path.

#### P1-G — Program 1 -> Program 2 v1.1
Depends: P1-F.

Acceptance:
- qualified opportunity DTO;
- rationale/freshness/provenance;
- idempotency/conflict contract;
- contract tests.

### BACKLOG

#### P1-H — Deterministic Browser E2E in CI
Depends: P1-B/C/D.

#### P1-I — Evidence-Gated Search Profile Promotion
Depends: repeated real evidence.

#### P1-J — Category Profile Promotion
Depends: repeated real evidence.

#### P1-K — Shop Profile Promotion
Depends: repeated real evidence.

#### P1-L — PDP Profile Promotion
Depends: repeated real evidence.

#### P1-M — Outcome Attribution Input
Depends: downstream analytics availability.

#### P1-N — Learned Opportunity Policy
Depends: sufficient outcome evidence.

## 5. Card Template

```text
ID:
Title:
Status:
Outcome:
Business hypothesis/foundation rationale:
Governing docs/diagram IDs:
Owner component:
Inputs:
Outputs:
Durable state:
Contracts:
Failure/recovery:
Security/compliance:
UX impact:
Headless test path:
Acceptance criteria:
Dependencies:
Evidence gate:
Migration/config:
Rollback:
Verification evidence:
Next card:
```

## 6. Pull Policy

Pull a card into IN DEV only if:
- READY criteria satisfied;
- WIP limit allows it;
- dependencies are complete or fake contract is intentionally used;
- CRITICAL/HIGH design issues = 0.

## 7. Push Policy

Push after coherent recoverable checkpoints.

Minimum expectations:
- push at least at each completed card;
- prefer additional pushes after accepted contract, tested domain/application layer, and verified adapter/integration checkpoints;
- never retain substantial completed work only locally.

## 8. Improvement Metrics

Track:
- lead time;
- blocked time;
- rework caused by missing design;
- escaped defects;
- recurrence rate;
- CI failure root causes;
- headless test coverage of critical behavior;
- number of UI-only correctness paths (target zero);
- operator confusion/support events when measurable;
- candidate decision quality metrics when attribution exists.

Do not optimize vanity metrics such as raw commit count, scraped product count or test count without quality context.
