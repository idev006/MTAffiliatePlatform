# Program 1 — Agile Kanban Board

Status: ENGINEERING MATURITY TARGET ACHIEVED / CONTINUOUS EVIDENCE IMPROVEMENT
Date: 2026-09-05
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

### DONE / VERIFIED FOUNDATION

- [x] P1-A Strategy-to-Work contracts and undeclared-signal rejection
- [x] P1-B Shared Job lifecycle: lease/renew/checkpoint/pause/resume/complete
- [x] P1-E Opportunity Feature Snapshot / evidence sufficiency
- [x] P1-F Opportunity Decision / Thesis / TEST_NOW-NEEDS_EVIDENCE behavior
- [x] P1-G typed QualifiedOpportunityHandoff into Program 2
- [x] Program 1 conformance gate
- [x] Program 1 browser extension build/test suite (current CI-authoritative suite)
- [x] deterministic platform closed-loop contract through Programs 1 -> 2 -> 3

### ENGINEERING / PRODUCT FOLLOW-UP

- [x] P1-C worker delivery reliability: failure classification, durable poison quarantine, ACK ambiguity fail-closed, quarantine telemetry
- [x] P1-D Collection Router + Versioned Profile Registry: modular fixture/search/category/shop/PDP adapters, deterministic routing, evidence-stage gate
- [x] P1-H real Chromium MV3 restart/reconcile E2E: persistent profile, startup renew, stale-tab recovery, ACK/checkpoint, completion, no duplicate
- [ ] P1-M Outcome Attribution Input when downstream analytics is available
- [ ] P1-N Learned Opportunity Policy after sufficient outcome evidence

These follow-ups do not move business authority into the browser/UI and do not invalidate the current >=90 engineering maturity baseline.

### PRODUCTION EVIDENCE-GATED

- [ ] P1-I Search profile promotion — `NEEDS_REAL_DATA`; evidence plan/tooling READY, profile remains LAB_VALIDATED
- [ ] P1-J Category profile promotion
- [ ] P1-K Shop profile promotion
- [ ] P1-L PDP profile promotion

Live evidence promotion must remain fail closed and must not bypass anti-bot/access controls.

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
