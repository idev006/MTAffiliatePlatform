# Program 1 — Current State and Strategy-Aligned Handoff

Status: ENGINEERING MATURITY BASELINE / CONTROLLED EVIDENCE PHASE
Date: 2026-09-05
Program: Affiliate Opportunity Intelligence

## 1. Governing Order

For Program 1, read in this order before implementation:

1. `PROJECT_CHARTER.md`
2. `PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md`
3. `PROGRAM1_SYSTEM_ARCHITECTURE.md`
4. `PROGRAM1_UML_AND_RUNTIME_DIAGRAMS.md`
5. `PROGRAM1_ARCHITECTURE_REVIEW_AND_IMPLEMENTATION_PLAN.md`
6. `PROGRAM1_TRACEABILITY_MATRIX.md`
7. `PROGRAM1_DEVELOPER_HANDOFF.md`
8. `PROGRAM1_KANBAN.md`
9. `PROGRAM1_IMPLEMENTATION_CARDS.md`
10. `PROGRAM1_UX_AND_OPERATOR_EXPERIENCE.md`
11. `PROGRAM1_AUTOMATED_TEST_ARCHITECTURE.md`
12. `WORKFLOW.md`
13. `PROGRAM1_IMPLEMENTATION_READINESS.md`
14. `APPLICATION_AND_ENGINE_CONTRACTS.md`
15. `DATA_MODEL.md`
16. `PROGRAM1_TO_PROGRAM2_HANDOFF_CONTRACT.md`
17. Program 1 evidence documents / specs / Kanban card
18. current implementation and tests

If source conflicts with the governing documents, do not silently reinterpret the documents. Resolve the discrepancy intentionally.

## 2. Strategic Mission

Program 1 answers:

> Which product opportunities should we pursue next to maximize expected affiliate success per unit of effort, and why?

Program 1 is not measured primarily by products scraped, pages visited or requests executed.

Its purpose is to improve affiliate resource allocation by turning market evidence into qualified, explainable opportunity candidates.

## 3. Current Implemented Foundation

Current verified foundation includes:
- ProductObservation domain/application/persistence foundation;
- durable/idempotent observation ingestion with atomic ACK semantics;
- SQLite/Alembic foundation;
- Program 1 API runtime profile;
- worker registry + heartbeat;
- Manifest V3 Program 1 browser worker **0.1.26**;
- durable local outbox + permanent-payload quarantine + conservative failure classification;
- Shared Job lease/renew/checkpoint/reconcile/verify/complete lifecycle owned by background runtime + Back Office;
- Collection Router + versioned fixture/search/category/shop/PDP profiles;
- profile evidence-stage gate and ambiguity fail-closed behavior;
- explicit anti-bot/verification classification;
- Vue 3 Side Panel as optional operator shell, not lifecycle authority;
- deterministic parser/router/background/unit/component tests;
- real Playwright Chromium MV3 restart/reconcile CI using a persistent browser profile;
- deterministic Program 1 -> Program 2 -> Program 3 contract E2E.

The Chromium E2E has proven:
```text
Page 1 -> authoritative ACK -> checkpoint
 -> browser context closes
 -> persistent profile reopens
 -> onStartup register + reconcile/renew
 -> durable active job/run state recovered
 -> stale tab safely recreated
 -> Page 2 -> ACK -> checkpoint -> verify -> complete
 -> active job cleared / outbox empty / no duplicate batch
```

These capabilities are engineering evidence; they do not by themselves constitute a production Shopee collection contract.

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

### P1 — Controlled Search Profile Evidence (P1-I)
Use the hardened evidence-capture tooling and ADR-047 process to obtain fresh independent authorized browser evidence for the Search surface.

Do not promote from cached/public retrieval, one capture, or a verification-gated session.

Required next evidence:
- at least two independent fresh captures;
- identity/name boundary repeatability;
- candidate price/sold/rating/review semantics only when directly supported;
- negative/blocked evidence;
- sanitized fixture + manifest + parser tests;
- promotion review under the evidence standard.

### P1 — Evidence-driven profile refinement
Keep Search/Category/Shop/PDP at `LAB_VALIDATED` until each satisfies its own promotion gate.

### P2 — Outcome Attribution
Begin P1-M only when Program 2/3 downstream result data can be traced back to Program 1 candidate decisions.

### P2 — Learned Opportunity Policy
P1-N remains deferred until outcome history is sufficient to validate learning rather than encode assumptions.

Engineering lifecycle, delivery reliability, collection modularity and real-browser restart/reconcile are no longer open foundation gaps.

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

## 10. P1-A Strategy-to-Work Slice Status — 2026-09-04

Status: IMPLEMENTED / REPOSITORY CI EVIDENCE PENDING

Implemented:
- `AffiliateSuccessHypothesis`;
- `SignalRequirement`;
- `SignalValidationState`;
- `DiscoveryPlan`;
- `Program1StrategyPlanner`;
- unit/component tests for traceability, uniqueness, cross-hypothesis/campaign mismatch, unknown/unused signals;
- CI coverage scope updated to include the new Program 1 strategy domain/application modules.

Important invariant now enforced in code:
- a signal supplied to the planner but not required by the approved DiscoveryPlan is rejected, preventing "collect because technically available" behavior.

Local isolated smoke verification: PASS.
Full repository/authoritative GitHub Actions verification: pending; no workflow run was visible through the connected GitHub interface at the time of this handoff.

Recommended next slice after green CI:
- P1-B Program 1 Shared Job / lease / pause / resume lifecycle consolidation.

## 11. Completion Criterion for the Next Maturity Stage

Program 1 reaches its next maturity stage when:
- strategy -> signal -> implementation traceability is enforced;
- worker lifecycle is durable and UI-independent;
- collector profiles are modular/versioned;
- ingestion/retry/restart behavior is resilient;
- opportunity feature/thesis contracts exist in code and tests;
- real-platform evidence is sufficient to promote selected collection profiles;
- downstream attribution can begin evaluating candidate quality.
