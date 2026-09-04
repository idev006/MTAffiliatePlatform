# Program 1 Process Conformance Audit — 2026-09-04

Status: ACTIVE ENGINEERING CONTROL BASELINE
Scope: Program 1 — Affiliate Opportunity Intelligence
Method: Strategy-first / Document-driven / Agile Kanban / Risk-based verification

## 1. Executive verdict

Program 1 backend/engine is **conformant at the platform-foundation and bounded-job lifecycle level**, but it is **not yet complete against the full strategic Program 1 mission**.

Current maturity:
- Strategy -> hypothesis -> signal requirements -> DiscoveryPlan: PASS
- Durable job/work package lifecycle: PASS
- Worker registration/capability/lease authority: PASS
- Durable observation ingestion/history: PASS
- Idempotency/restart/recovery/failure containment: PASS in simulation
- Browser collection laboratory path: PASS WITH EVIDENCE GATES
- Normalize/identity/history intelligence layer: PARTIAL
- Versioned opportunity feature derivation: PARTIAL / FRAMEWORK ONLY
- Qualification + Opportunity Thesis: NOT COMPLETE
- Production ranking/scoring: EVIDENCE-GATED, NOT APPROVED
- Human/policy approval workflow: PARTIAL
- Qualified Program 1 -> Program 2 handoff with full rationale/provenance: PARTIAL
- Real Chromium MV3 kill/restart lifecycle evidence: NOT YET CLOSED
- Real Shopee production evidence: NOT YET CLOSED
- Downstream outcome/attribution learning loop: NOT YET AVAILABLE AS A CLOSED LOOP

Therefore: **Simulation baseline can be verified; strategic/production completeness cannot yet be claimed.**

## 2. Governing objective conformance

| Strategic objective | Current implementation evidence | Verdict |
|---|---|---|
| Improve probability affiliate effort is spent on right products | explainable Product Intelligence framework + shortlist | PARTIAL |
| Strategy must lead engineering | AffiliateSuccessHypothesis, SignalRequirement, DiscoveryPlan | PASS |
| Collect only decision-supporting evidence | required_signal_ids + strategy work package | PASS AT CONTRACT LEVEL |
| Preserve historical observations | append-oriented observations + latest projection | PASS |
| Separate observed fact -> derived feature -> decision | architecture boundaries exist | PASS ARCHITECTURE / PARTIAL IMPLEMENTATION |
| Evaluate demand/momentum/timing | demand placeholder exists; temporal feature engine incomplete | PARTIAL |
| Buyer-intent intelligence | not implemented as production feature | NOT COMPLETE |
| Contentability | documented, no production feature engine | NOT COMPLETE |
| Competition/saturation | documented, no production feature engine | NOT COMPLETE |
| Seller/fulfilment confidence | observation fields partly available; evaluation incomplete | PARTIAL |
| Audience/account fit | documented future context; no full ranking implementation | NOT COMPLETE |
| Risk/uncertainty | evidence gates/fail-closed behavior strong; business opportunity risk model incomplete | PARTIAL |
| Opportunity Thesis | contract/document exists; entity/use-case not complete | NOT COMPLETE |
| TEST_NOW/WATCH/SCALE/HOLD/etc. actions | documented, not yet full domain implementation | NOT COMPLETE |
| Production score only after evidence | current scoring explicitly framework/placeholder | PASS GOVERNANCE |
| Explainable deterministic shortlist | deterministic current framework with reasons/version | PASS LAB / NOT PRODUCTION MODEL |
| Program 2 receives qualified opportunities only | intended boundary exists; full qualified handoff DTO incomplete | PARTIAL |
| Closed learning loop from downstream outcomes | documented, attribution/outcome loop not closed | NOT COMPLETE |

## 3. Canonical workflow conformance

Governing Program 1 pipeline:

Strategy -> Hypothesis -> Required Signals -> Discovery Plan -> Bounded Job -> Worker Lease -> Observe -> Local Outbox -> Durable Ingestion -> Normalize / Identity / History -> Feature Derivation -> Qualification -> Opportunity Evaluation -> Explainable Ranking -> Approval -> Program 2 Handoff

| Stage | Status | Notes |
|---|---|---|
| Strategy/Hypothesis | PASS | typed immutable model |
| Required Signals | PASS | explicit decision-supported signals |
| DiscoveryPlan | PASS | durable strategy package |
| Job creation/idempotency | PASS | Shared Job Engine |
| Worker registration/health | PASS | Back Office authoritative |
| Capability matching | PASS | worker cannot self-authorize API lease capability |
| Lease/start/renew | PASS | backend + background lifecycle controller |
| Observation execution | PARTIAL | fixture/current-page lab; real profile evidence gated |
| Local outbox | PASS LAB | durable local queue + serialized drain |
| Durable ACK | PASS | ACK only after durable ingestion |
| Checkpoint | PASS | job checkpoint after acknowledged batch |
| Restart/reconcile | PASS SIMULATION | real MV3 kill/restart E2E remains |
| Normalize/identity | PARTIAL | canonical product key; richer identity normalization pending |
| Historical projection | PASS | append facts + latest observation projection |
| Feature derivation | PARTIAL | scoring components exist; full strategic feature set incomplete |
| Qualification | PARTIAL | minimum score/shortlist only; no complete qualification state model |
| Opportunity Thesis | NOT COMPLETE | documented contract, not implemented end-to-end |
| Approval | PARTIAL | policy/human review concept, not full workflow |
| Program 2 handoff | PARTIAL | shortlist exists, full rationale/provenance handoff incomplete |
| Learning loop | NOT COMPLETE | requires downstream attribution/outcome subsystem |

## 4. Use-case verification matrix

| UC | Use case | Status | Test/evidence |
|---|---|---|---|
| P1-UC-01 | Define affiliate success hypothesis | PASS | unit/component strategy tests |
| P1-UC-02 | Define required decision signals | PASS | model/planner tests |
| P1-UC-03 | Build validated DiscoveryPlan | PASS | planner tests |
| P1-UC-04 | Persist strategy work package | PASS | memory + SQLite integration |
| P1-UC-05 | Create idempotent discovery job | PASS | unit/component/integration |
| P1-UC-06 | Register/heartbeat discovery worker | PASS | contract/SQLite/extension |
| P1-UC-07 | Lease only compatible work | PASS | unit/contract/adversarial |
| P1-UC-08 | Prevent simultaneous active jobs per worker | PASS | adversarial state-machine tests |
| P1-UC-09 | Fetch durable job work package | PASS IMPLEMENTED 2026-09-04 | API contract |
| P1-UC-10 | Start/renew/checkpoint/verify/complete | PASS BACKEND | unit/contract/integration |
| P1-UC-11 | Background owns durable active-job state | PASS LAB | Node lifecycle tests |
| P1-UC-12 | Reconcile after service-worker restart | PASS LOGIC / E2E PENDING | Node tests; real browser pending |
| P1-UC-13 | Capture deterministic fixture page | PASS | extension tests/E2E |
| P1-UC-14 | Capture supported Shopee current page | LAB-VALIDATED ONLY | evidence gated |
| P1-UC-15 | Detect unsupported/schema/anti-bot page | PASS LAB | fail-closed tests |
| P1-UC-16 | Durable local outbox + ACK replay | PASS | extension tests |
| P1-UC-17 | Atomic durable observation batch ingest | PASS | SQLite integration |
| P1-UC-18 | Preserve history and project latest state | PASS | repository tests |
| P1-UC-19 | Derive complete strategic opportunity feature set | NOT COMPLETE | missing full domain/application layer |
| P1-UC-20 | Evaluate Opportunity Thesis | NOT COMPLETE | contract only |
| P1-UC-21 | Recommend TEST_NOW/WATCH/SCALE/etc. | NOT COMPLETE | policy model pending |
| P1-UC-22 | Human/policy approval | PARTIAL | workflow concept only |
| P1-UC-23 | Qualified opportunity handoff to Program 2 | PARTIAL | shortlist exists; richer handoff pending |
| P1-UC-24 | Learn from clicks/orders/commission | NOT COMPLETE | downstream attribution required |

## 5. Test-case conformance

The current suite is strong for implemented foundation behavior, but **it is incorrect to claim every Program 1 test case is complete**, because several strategic use cases do not yet have production implementation.

Current automated control families:
- domain model validation;
- strategy traceability;
- idempotency;
- job lifecycle allowed/forbidden transitions;
- lease ownership/expiry;
- restart/recomposition;
- unsafe-expiry escalation;
- worker capability/admission;
- observation batch replay/collision;
- atomic SQLite state/event persistence;
- API contracts;
- extension parser/transport/outbox/pagination;
- adversarial repository conflicts;
- stress;
- branch coverage >= 95%.

Required future test families:
- temporal demand/momentum features;
- buyer intent;
- competition/saturation;
- contentability;
- seller confidence;
- audience/account fit;
- uncertainty/freshness;
- Opportunity Thesis;
- action recommendation state;
- Program 1 -> Program 2 qualified handoff;
- baseline/random-vs-model business experiment;
- real Chromium MV3 kill/restart;
- real Shopee schema/profile regression;
- PostgreSQL Tier-1 parity for expanded Program 1 lifecycle;
- performance/capacity budgets for browser workers/ingestion/scoring.

## 6. Process-engineering controls

Existing controls: document authority; RACI/single authority; explicit state machine; process interlocks; durable checkpoints; health/heartbeat/outbox feedback; CAPA + regression tests; fail-closed behavior; CI quality gates; risk-based failure injection.

Added on 2026-09-04: an executable Program 1 process-conformance gate now verifies required governing documents, extension version consistency, background lifecycle ownership, governing workflow/strategy anchors, opportunity contracts, and critical restart/idempotency/NEEDS_HUMAN simulation scenarios.

CI command: python tools/program1_conformance_check.py

## 7. Process Engineer Control Plan

| Process step | CTQ / invariant | Detection | Control action |
|---|---|---|---|
| Strategy intake | every signal supports explicit decision | planner validation + traceability audit | reject Not Ready |
| Job creation | one logical job/idempotency key | unique semantics + tests | conflict/reuse existing |
| Worker admission | only eligible healthy capable worker | registry + capability match | reject lease |
| Lease ownership | one active lease/worker | state engine | reject second lease |
| Observation | unsupported/anti-bot is not empty success | page classification | fail closed |
| Outbox | facts survive transport failure | local durable queue | retry same identity |
| Durable ingest | ACK only after commit | transaction + batch receipt | retain outbox |
| Checkpoint | external work separated from SQL transaction | job checkpoint | resume/reconcile |
| Restart | worker cannot forget active job | durable active state | reconcile before new lease |
| Feature derivation | same facts/policy -> same feature | deterministic engine tests | block non-determinism |
| Opportunity decision | explainable + versioned | decision provenance | NEEDS_EVIDENCE if insufficient |
| Program 2 handoff | only qualified opportunities | handoff gate | reject arbitrary raw products |

## 8. FMEA-style priority risks

| Risk | Effect | Current control | Remaining action | Priority |
|---|---|---|---|---|
| MV3 worker killed mid-job | duplicate/lost work | durable active job + reconcile logic | real browser kill/restart E2E | P0 |
| Work package unavailable after lease | leased job cannot execute | persist lease before fetch, fail closed | operator/recovery route + explicit NeedsHuman endpoint if needed | P0 |
| Side Panel still schedules multi-page loop | UI remains execution dependency | background lifecycle owns job | move scheduling/cycle orchestration to background | P0 |
| Real Shopee DOM drift | silent bad observations | fail-closed parser | sanitized regression fixtures + evidence promotion | P0 |
| Placeholder scoring interpreted as production model | bad affiliate decisions | model_version + governance docs | opportunity feature/qualification engine first | P0 |
| Missing business outcome loop | cannot prove affiliate success | strategic north star documented | attribution/learning subsystem | P1 |
| Weak identity semantics on real data | duplicate/misattributed history | canonical key | real-data identity evidence | P1 |
| Missing formal Opportunity Thesis entity | weak explainability/handoff | contract documentation | implement entity/use case/persistence | P1 |
| No quantitative runtime process capability | scaling instability | stress/health framework | define SLOs/control limits after benchmark | P1 |

## 9. Definition of Program 1 Complete

Program 1 must not be declared complete until all are true:
1. every strategic objective is PASS or explicitly removed by approved strategy decision;
2. every Program 1 use case has implementation + automated acceptance test;
3. all critical failure modes have detection/recovery controls;
4. background worker execution does not require Side Panel presence;
5. MV3 kill/restart recovery passes real-browser E2E;
6. real Shopee profiles are evidence-validated and regression-fixtured;
7. Opportunity feature/qualification/thesis workflow is implemented;
8. Program 1 -> Program 2 handoff is typed, durable and traceable;
9. business outcome measurement exists to evaluate decision quality;
10. CI/conformance gates are green on the exact release commit.

## 10. Recommended next implementation sequence

P0-A: background-owned multi-page execution loop driven by durable DiscoveryPlan.
P0-B: real Chromium service-worker kill/restart/reconcile E2E.
P0-C: sanitized Shopee fixture/evidence promotion pipeline.
P0-D: OpportunityFeatureSnapshot + Qualification + OpportunityThesis domain/application slice.
P1-A: qualified Program 1 -> Program 2 handoff contract.
P1-B: runtime SLO/control metrics and process capability baseline.
P1-C: downstream attribution/learning-loop contract.

Each slice follows: Document/Card -> DoR -> implementation -> automated tests -> failure injection -> CI -> audit -> CAPA -> evidence -> Done.