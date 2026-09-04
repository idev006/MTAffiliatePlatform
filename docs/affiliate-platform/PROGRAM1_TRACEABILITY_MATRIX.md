# Program 1 — Strategy / Architecture / Implementation Traceability Matrix

Status: GOVERNING TRACEABILITY BASELINE
Date: 2026-09-04

## 1. Purpose

Ensure Program 1 remains document-driven from affiliate strategy through implementation and verification.

Every material Program 1 feature must be traceable across:

```text
Business Objective
 -> Hypothesis
 -> Decision Signal
 -> Evidence
 -> Contract
 -> Component
 -> Data
 -> Test
 -> Outcome
```

## 2. Core Traceability Matrix

| Business Decision | Candidate Signals | Evidence / Source | Owning Component | Contract / Artifact | Durable Data | Required Test | Outcome / Validation |
|---|---|---|---|---|---|---|---|
| Which products deserve testing now? | demand, momentum, price/value, contentability, seller confidence, risk | approved observations + campaign context | Opportunity Feature + Evaluation Engines | DeriveOpportunityFeatures / EvaluateOpportunity | feature snapshot + opportunity decision | unit/component | candidate hit rate / downstream conversion |
| Which products need more evidence? | missing/stale/conflicting fields, weak identity, stale profile | observation history + profile metadata | Qualification Engine | EvaluateOpportunity | data sufficiency + NEEDS_EVIDENCE decision | unit/component | later evidence resolves uncertainty |
| Which watched products became timely? | momentum change, price/promo change, campaign timing | repeated observations + campaign context | Feature Engine / Evaluation | feature policy + evaluation policy | new feature snapshot + decision version | time-series/component | improved action timing |
| Which products should be deprioritized/stopped? | worsening demand/value, risk, saturation, poor outcomes | observations + downstream analytics | Evaluation/Ranking | EvaluateOpportunity | versioned decision | unit/component | waste reduction |
| What should Program 2 investigate? | qualified opportunity, rationale, freshness, identity | Program 1 decision | Handoff Use Case | ProductCandidateForOfferDiscovery v1.1 | handoff receipt | contract | offer conversion/availability |
| What page/surface should worker collect? | required signal capability, surface/profile compatibility | job plan + profile registry | Discovery Planning + Collection Router | DiscoveryJob / profile contract | job + checkpoint | contract/fixture | collection correctness |
| Is a page genuinely empty or broken/blocked? | page shell, schema indicators, anti-bot indicators | page context | Collection Profile/Router | collection result classification | observation/result evidence | fixture/E2E | zero-result correctness |
| Can a result be safely acknowledged? | batch identity, durable accounted state | ingestion receipt | Ingestion Application | observation batch/ACK | ingestion receipt + observations | integration/resilience | no duplicate/lost data |
| Can worker resume after restart? | canonical job/lease/checkpoint + local outbox | Shared Job + local durable state | Job Engine + Worker Runtime | lease/checkpoint protocol | job/checkpoint/outbox | resilience/E2E | correct resume/no duplicate |
| Can a collection profile be promoted? | repeated stable evidence + fixtures | controlled live evidence | Process/QA + Profile Registry | profile evidence lifecycle | profile metadata/evidence refs | fixture/live evidence | stable extraction |
| Is an opportunity recommendation explainable? | feature values, evidence refs, policy version, uncertainty | feature snapshot | Opportunity Evaluation | Opportunity Thesis | opportunity decision | component | reviewer can reconstruct why |
| Does Program 1 improve affiliate success? | candidate decisions + downstream click/order/commission/effort | attribution system | Analytics / Strategy | future performance observation | outcome history | analytics validation | revenue yield / candidate hit rate |

## 3. Governing Document Mapping

| Concern | Governing Document |
|---|---|
| Affiliate success strategy | `PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md` |
| Logical/system architecture | `PROGRAM1_SYSTEM_ARCHITECTURE.md` |
| UML/runtime collaboration | `PROGRAM1_UML_AND_RUNTIME_DIAGRAMS.md` |
| Implementation priorities | `PROGRAM1_ARCHITECTURE_REVIEW_AND_IMPLEMENTATION_PLAN.md` |
| Canonical platform workflow | `WORKFLOW.md` |
| Program 1 implementation readiness | `PROGRAM1_IMPLEMENTATION_READINESS.md` |
| Application/engine semantics | `APPLICATION_AND_ENGINE_CONTRACTS.md` |
| Durable data | `DATA_MODEL.md` |
| Program 1 -> 2 boundary | `PROGRAM1_TO_PROGRAM2_HANDOFF_CONTRACT.md` |
| Current handoff/status | `PROGRAM1_CURRENT_STATE.md` |
| Collection router/profile registry | `PROGRAM1_COLLECTION_ROUTER_AND_PROFILE_REGISTRY.md` |
| Live evidence promotion | `CONTROLLED_PRODUCTION_EVIDENCE_VALIDATION_STANDARD.md` + `PRODUCTION_EVIDENCE_PROMOTION_MATRIX.md` |
| Platform decisions | `DECISION_LOG.md` |
| Evidence | `docs/affiliate-platform/evidence/*` |

## 4. Source-Code Target Mapping

The following is target ownership, not a claim that current files already match exactly.

| Responsibility | Target Layer |
|---|---|
| Affiliate hypothesis / campaign use cases | application/domain |
| Discovery planning | application |
| Opportunity feature derivation | engines/domain |
| Qualification / Opportunity Thesis | engines/domain |
| Ranking / shortlist | engines/domain |
| ProductObservation | domain |
| Job lifecycle | Shared Job Engine/application |
| Worker registration/heartbeat | shared application/domain + browser background |
| Collection router/profile | browser adapter/extension |
| DOM selectors/parsing | versioned browser profile adapter only |
| Local outbox | worker infrastructure |
| Ingestion persistence | repository/UoW adapter |
| Opportunity persistence | repository/UoW adapter |
| Program 1 API | interface |
| Side Panel | presentation/operator shell |

## 5. Test Mapping

| Architecture Concern | Minimum Verification |
|---|---|
| Business rule | unit |
| Use-case orchestration | component |
| Port/API schema | contract |
| Collection profile | fixture |
| Persistence/idempotency | integration |
| lease/ACK/restart | resilience |
| real extension collaboration | deterministic browser E2E |
| Shopee assumption | controlled live evidence |

## 6. Change Rule

A Program 1 PR/card is incomplete if a material change cannot identify:
- business/foundation rationale;
- governing document;
- affected diagram/contract;
- source owner;
- required test;
- evidence gate.

If a source change introduces a new responsibility not represented in this matrix or the architecture documents, documentation must be updated first or in the same coherent change.
