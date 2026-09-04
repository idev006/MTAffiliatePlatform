# Program 1 — Developer Implementation Handoff

Status: READY FOR ITERATIVE DEVELOPMENT
Date: 2026-09-04
Scope: Program 1 — Affiliate Opportunity Intelligence

## 1. Purpose

This is the developer entrypoint for Program 1 implementation.

A developer should be able to start from this document, understand the governing design, pick the next Kanban card, implement a small vertical slice, verify it headlessly, and push a recoverable checkpoint without inventing architecture.

## 2. Mandatory Reading Order

Before changing Program 1 behavior:

1. `PROJECT_CHARTER.md`
2. `PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md`
3. `PROGRAM1_SYSTEM_ARCHITECTURE.md`
4. `PROGRAM1_UML_AND_RUNTIME_DIAGRAMS.md`
5. `PROGRAM1_ARCHITECTURE_REVIEW_AND_IMPLEMENTATION_PLAN.md`
6. `PROGRAM1_TRACEABILITY_MATRIX.md`
7. `PROGRAM1_KANBAN.md`
8. `PROGRAM1_UX_AND_OPERATOR_EXPERIENCE.md`
9. `PROGRAM1_AUTOMATED_TEST_ARCHITECTURE.md`
10. `PROGRAM1_IMPLEMENTATION_READINESS.md`
11. `APPLICATION_AND_ENGINE_CONTRACTS.md`
12. `DATA_MODEL.md`
13. `PROGRAM1_TO_PROGRAM2_HANDOFF_CONTRACT.md`
14. affected source/tests/evidence files.

If these documents conflict, stop implementation of the affected behavior and reconcile the documents first.

## 3. Program 1 Mission

Program 1 exists to answer:

> Which product opportunities should we pursue next to maximize expected affiliate success per unit of effort, and why?

Engineering serves this strategy. Browser collection is a means, not the goal.

## 4. Non-Negotiable Architecture Rules

- Back Office owns durable business decisions.
- Shared Job Engine owns long-running job lifecycle.
- Browser worker executes bounded work only.
- Side Panel is presentation/commands only.
- Observations are not opportunity decisions.
- Unknown evidence remains unknown.
- Collection profiles are versioned and evidence-gated.
- No CAPTCHA/access-control/anti-bot bypass.
- No production scoring weights invented without evidence.
- No direct UI/worker writes to canonical business tables.
- No long DB transaction across browser/network/human work.
- Every retryable side effect has idempotency/reconciliation semantics.
- Core behavior must be testable without live Shopee and without graphical UI.

## 5. Development Order

Preferred order per slice:

```text
Document / Contract
  -> Domain
  -> Engine/Application
  -> Port
  -> Fake / In-Memory Adapter
  -> Unit / Component / Contract Tests
  -> Concrete Adapter
  -> API / CLI
  -> Optional UI
  -> Resilience / E2E
```

Do not begin with UI.

## 6. Current Development Track

Completed:
- strategy-led documentation baseline;
- Program 1 architecture/UML/traceability pack;
- P1-A Strategy-to-Work contracts implemented.

Next:
- P1-B Shared Job / lease / pause / resume integration;
- P1-C Worker delivery reliability;
- P1-D Collection Router / Profile architecture;
- P1-E Opportunity Feature Snapshot;
- P1-F Opportunity Decision / Thesis;
- P1-G Program 1 -> 2 v1.1;
- P1-H deterministic browser E2E CI;
- P1-I evidence-gated live profile promotion.

P1-E/F may proceed in parallel with P1-B/C/D using fake observations.

## 7. One-Card Rule

Prefer one coherent business/architecture outcome per branch/session.

A card should be small enough that:
- its acceptance criteria are explicit;
- relevant tests can run quickly;
- rollback is understandable;
- code review has one primary concern;
- the repository can be pushed at a recoverable checkpoint.

Avoid "finish Program 1" or multi-feature branches.

## 8. Required Card Fields

Every card must contain:
- ID;
- user/business outcome or foundation rationale;
- governing document/diagram IDs;
- scope;
- non-goals;
- owner component;
- inputs/outputs;
- durable state;
- contracts/API;
- failure/recovery behavior;
- security/compliance notes;
- test plan;
- acceptance criteria;
- dependencies;
- evidence gate;
- migration/config impact;
- rollback/recovery;
- status.

## 9. Commit / Push Discipline

Commit frequently at meaningful recoverable checkpoints.

Recommended checkpoints:
- document/contract accepted;
- domain model + unit tests;
- application/engine + component tests;
- port/fake + contract tests;
- concrete adapter + fixtures;
- integration/resilience tests;
- final documentation/verification update.

Push to GitHub after each coherent checkpoint when the branch remains buildable or clearly marked WIP.

Do not leave a substantial working implementation only on one local machine.

Commit messages should state intent, for example:
- `docs(program1): define lease recovery contract`
- `feat(program1): add discovery job lease application flow`
- `test(program1): cover lost-ack replay`
- `fix(program1): quarantine permanent outbox payload failures`

## 10. Developer Verification Before Push

At minimum run the narrowest relevant checks first, then the required repository gates.

Typical Python:
```text
ruff check affected paths
pytest affected unit/component/contract tests
```

Before claiming Done:
- core selected coverage gate;
- SQLite integration if persistence affected;
- extension tests/build if browser worker affected;
- deterministic browser E2E if worker flow affected;
- architecture/dependency gates when available.

Never weaken a gate simply to get green.

## 11. UX Requirement

Every operator-facing workflow must support a user with limited technical knowledge.

The operator should not need to know:
- DOM selectors;
- JSON payloads;
- job lease tokens;
- database IDs unless useful for support;
- browser extension internals;
- retry/error implementation.

UI/read models should answer:
- What is the system doing?
- What should I do next?
- Is the result trustworthy?
- Is anything blocked?
- Can I safely pause/close/reopen?
- What caused a failure?
- Is human action required?

Detailed technical evidence remains available through an advanced/support view.

## 12. Headless Testability Requirement

A feature is not architecture-complete if its business behavior can only be tested by clicking the UI.

The same application behavior must be callable through:
- pytest/fake harness;
- application service;
- API/CLI where appropriate.

UI tests verify presentation and command mapping only.

## 13. Stop Conditions

Stop and move the card to the appropriate blocked state when:
- a Shopee fact would need to be guessed;
- a selector/field lacks evidence required for promotion;
- an irreversible/retry behavior is ambiguous;
- a new lifecycle owner would conflict with Shared Job;
- a user workflow cannot be made understandable without hidden technical steps;
- a core behavior cannot be tested headlessly;
- CRITICAL/HIGH design issue remains.

Valid states:
`BLOCKED | NEEDS_DECISION | NEEDS_REAL_DATA | NEEDS_HUMAN`.

Stopping at a real evidence boundary is correct engineering.

## 14. End-of-Card Handoff

Before moving to DONE:
1. code/tests committed;
2. CI/result recorded;
3. docs/diagrams updated if behavior changed;
4. Kanban card updated;
5. known risks recorded;
6. next dependency identified;
7. branch pushed;
8. no important uncommitted local work remains.

## 15. Developer Success Criterion

A developer following this handoff should be able to continue Program 1 without asking where business logic belongs, which component owns lifecycle state, how to test the feature, or whether UI is required for correctness.
