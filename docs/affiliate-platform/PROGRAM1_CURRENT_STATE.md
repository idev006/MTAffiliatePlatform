# Program 1 — Current State and Strategy-Aligned Handoff

Status: ACTIVE PROGRAM HANDOFF
Date: 2026-09-04
Program: Affiliate Opportunity Intelligence

## 1. Governing Order

For Program 1, read in this order before implementation:

1. `PROJECT_CHARTER.md`
2. `PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md`
3. `PROGRAM1_SYSTEM_ARCHITECTURE.md`
4. `PROGRAM1_UML_AND_RUNTIME_DIAGRAMS.md`
5. `PROGRAM1_ARCHITECTURE_REVIEW_AND_IMPLEMENTATION_PLAN.md`
6. `PROGRAM1_TRACEABILITY_MATRIX.md`
7. `WORKFLOW.md`
8. `PROGRAM1_IMPLEMENTATION_READINESS.md`
9. `APPLICATION_AND_ENGINE_CONTRACTS.md`
10. `DATA_MODEL.md`
11. `PROGRAM1_TO_PROGRAM2_HANDOFF_CONTRACT.md`
12. Program 1 evidence documents / specs / Kanban card
13. current implementation and tests

If source conflicts with the governing documents, do not silently reinterpret the documents. Resolve the discrepancy intentionally.

## 2. Strategic Mission

Program 1 answers:

> Which product opportunities should we pursue next to maximize expected affiliate success per unit of effort, and why?

Program 1 is not measured primarily by products scraped, pages visited or requests executed.

Its purpose is to improve affiliate resource allocation by turning market evidence into qualified, explainable opportunity candidates.

## 3. Current Implemented Foundation

Current foundation includes:
- ProductObservation domain/application/persistence foundation;
- durable/idempotent observation ingestion;
- SQLite/Alembic foundation;
- Program 1 API runtime profile;
- worker registry + heartbeat;
- Manifest V3 Program 1 browser worker;
- local outbox and ACK validation;
- current-page/fixture collectors;
- conservative candidate Shopee identity parsing;
- search/category/shop/PDP laboratory evidence;
- pagination-aware auto-run laboratory;
- explicit anti-bot/verification classification;
- Vue 3 Side Panel operator UI;
- deterministic parser/unit tests;
- deterministic two-page fixture auto-run E2E tooling.

These capabilities are implementation evidence; they do not by themselves constitute a production Shopee collection contract.

## 4. Evidence Status

Current real-platform evidence remains controlled and incomplete.

Validated/observed areas include candidate product identity shapes and selected surface structures.

Still gated include:
- final production Product identity semantics;
- repeated stable price/sold/rating/review/seller field boundaries;
- production per-surface collection profiles;
- pacing/scroll/page budgets;
- production opportunity feature schema;
- Product/Opportunity Scoring Model exact weights/formula;
- downstream outcome attribution sufficient to prove predictive value.

Anti-bot/access-control conditions remain fail-closed and must not be bypassed.

## 5. Strategy-to-Implementation Rule

Every Program 1 business-feature slice must trace:

```text
Affiliate Success Question / Hypothesis
 -> Decision Signal
 -> Evidence Requirement
 -> Data Contract / Feature
 -> Collection Requirement
 -> Engine / Application Behavior
 -> Test / Evidence Gate
 -> Downstream Outcome to Measure
```

A proposal that starts with "this field can be scraped" is incomplete until its decision value is stated.

## 6. Current Architecture Direction

Target:

```text
Affiliate / Marketing Strategy
        -> Campaign / Hypothesis / Signal Requirements
        -> Back Office Discovery Planning
        -> Shared Job / Lease
        -> Browser Worker Background Runtime
        -> Collection Profile Router
        -> Versioned Surface Profile
        -> ProductObservation
        -> Durable Ingestion / ACK
        -> Identity / Normalize / History
        -> Opportunity Feature Derivation
        -> Qualification / Opportunity Thesis
        -> Explainable Ranking / Action Candidate
        -> Approval
        -> Program 2 Handoff
```

Side Panel is an operator shell. It should not become the durable job-orchestration authority.

Browser worker collects/executes bounded work. It does not own commercial policy.

## 7. Immediate Documentation-Driven Engineering Priorities

### P0 — Verify/Freeze Strategy-Aligned Baseline
- keep documents and extension version metadata consistent;
- verify current HEAD CI after documentation changes;
- establish automated version/SSOT conformance checks;
- update Program 1 implementation/Kanban evidence after code changes, not before.

### P1 — Worker Lifecycle Consolidation
Implement the already-documented shared job/lease/pause/resume model for Program 1 so long-running work is owned by Back Office + background worker rather than Side Panel lifecycle.

### P1 — Collector Modularity
Refactor monolithic collection behavior toward a profile router and versioned per-surface collection profiles after the relevant evidence gates are met.

### P1 — Reliability Hardening
Review:
- ACK semantics for duplicate/idempotent replay;
- poison-message/head-of-line blocking;
- retryable vs permanent vs ambiguous delivery failures;
- quarantine/reconciliation semantics;
- MV3 service-worker restart state;
- structured transport errors.

### P1 — Opportunity Intelligence Foundation
Implement domain/application scaffolding for:
- versioned opportunity features;
- data sufficiency/unknown state;
- Opportunity Thesis;
- recommended action;
- decision provenance.

Do not invent production scoring weights.

### P2 — Evidence Expansion
After normal Shopee access returns:
- second independent search captures;
- repeat evidence for price/sold and other proposed fields;
- category/shop/PDP repeated captures;
- profile promotion only after evidence review.

### P2 — Deterministic Browser E2E CI
Run the fixture-based extension workflow in CI or an equivalent deterministic browser harness without touching live Shopee.

## 8. Known Documentation Drift Closed

On 2026-09-04 Program 1 browser plugin README lagged runtime metadata:
- README: 0.1.17;
- manifest/package: 0.1.22.

The documentation baseline is being corrected. Automated conformance should prevent recurrence.

## 9. Non-Priorities Right Now

Do not prioritize:
- aggressive scrolling/crawling;
- CAPTCHA/anti-bot bypass;
- large worker farms;
- opaque 0-100 production scoring;
- microservice extraction;
- bigger UI surface;
- production selector hard-freeze from one capture.

## 10. Completion Criterion for the Next Maturity Stage

Program 1 reaches its next maturity stage when:
- strategy -> signal -> implementation traceability is enforced;
- worker lifecycle is durable and UI-independent;
- collector profiles are modular/versioned;
- ingestion/retry/restart behavior is resilient;
- opportunity feature/thesis contracts exist in code and tests;
- real-platform evidence is sufficient to promote selected collection profiles;
- downstream attribution can begin evaluating candidate quality.
