# Development Handoff Master — Affiliate Platform

Date: 2026-09-05
Status: **PROGRAMS 1–3 ENGINEERING COMPLETE BASELINE / PRODUCTION EVIDENCE GATED**
Implementation authority: governed by `ENGINEERING_GOVERNANCE.md`

## 1. Governing Principle

**Project must follow the document.**

This repository is the SSOT for requirements, architecture, workflow, contracts, state models, database rules, deployment rules, test expectations and implementation decisions.

Priority of authority:
1. `PROJECT_CHARTER.md`
2. `WORKFLOW.md`
3. `ARCHITECTURE.md`
4. `ENGINEERING_GOVERNANCE.md`
5. accepted ADRs / `DECISION_LOG.md`
6. `PROJECT_STRUCTURE_AND_ENGINE_ARCHITECTURE.md`
7. `APPLICATION_AND_ENGINE_CONTRACTS.md`
8. `DATA_MODEL.md`
9. Step baselines and feature specifications
10. source code/tests

If code and an approved document disagree, the code is non-conforming until the discrepancy is intentionally resolved.

## 2. Architecture Decision for Implementation

The implementation is **engine-first and headless-first**.

Business capability must be implemented so it can run/test without graphical UI.

Baseline dependency flow:

```text
UI / CLI / FastAPI
        |
        v
Application Use Cases
        |
        v
Domain Engines / Policies / State Machines
        |
        v
Ports / Interfaces
        |
        v
Concrete Adapters
DB / Browser / Android / Media / Notifications
```

Dependency direction is inward.

PySide6 is an optional desktop presentation shell to be built when stable commands/queries and operator value exist. It must not own business rules.

## 3. Reviewed Business Scope

### Program 1 — Affiliate Opportunity Intelligence
Accepted direction:
- Affiliate/Marketing Strategy defines the decision hypothesis and required signals before engineering collection work;
- distributed browser-worker farm;
- Back Office owns planning, sharding, job leasing, checkpoints and canonical deduplication;
- browser extension workers collect observations only;
- observations are historical/append-oriented;
- opportunity intelligence separates observed facts, normalized facts, derived features and decisions;
- Opportunity Evaluation owns qualification/thesis/action/ranking policy;
- scoring remains optional/evidence-gated and versioned;
- UI is novice-friendly presentation/command shell, not job/business authority;
- core behavior must be headlessly testable and CI-friendly.

Program 1 developer entrypoint: `PROGRAM1_DEVELOPER_HANDOFF.md`.

### Step 2 — Affiliate Offer Automation
Accepted direction:
- distributed affiliate-worker farm using the same Shared Core worker platform;
- Product 1:N Offers;
- affiliate account/session provenance is mandatory where offer facts depend on account context;
- Offer Engine owns eligibility/ranking/preferred/backup/freshness policy;
- Shared Core `jobs` is the sole lifecycle SSOT;
- Program 1 `QualifiedOpportunityHandoff` is the normal admission authority for commercial work;
- Program 2 separates observed facts -> feature snapshot -> qualification -> durable selection decision -> validated link artifact;
- Program 3 consumes only typed, fresh, durable Program 2 handoffs.

Program 2 developer entrypoint: `PROGRAM2_DEVELOPER_HANDOFF.md`.

### Step 3 — Content Publishing / Android Device Farm
Accepted direction:
- Python Back Office is Control Plane;
- Device Host Manager owns local device lifecycle/resources;
- one active Worker Runtime controls one Android device;
- Worker is Scene-aware: `Observe -> Recognize -> Validate -> Act -> Verify -> Checkpoint`;
- Scene Engine owns recognition/transition/recovery policy;
- Android selectors/device commands are adapters;
- screen streaming is observability/operator control, not business SSOT;
- publish ambiguity never triggers blind repost;
- Publishing Engine + Ledger enforce duplicate/irreversible-action policy;
- typed Program 2 offer handoff is the commercial admission authority;
- POST_SUBMITTED is a durable irreversible boundary;
- reconciliation, not worker memory, decides whether retry is safe.

Program 3 developer entrypoint: `PROGRAM3_DEVELOPER_HANDOFF.md`.

## 4. Core Engines

Foundation architecture includes these logical engines:
- Shared Job Engine;
- Product Intelligence Engine;
- Affiliate Offer Engine;
- Content Identity Engine;
- Publishing Engine;
- Scene Engine.

Engines are domain/application components, not separate microservices by default.

They must be independently testable with fake/in-memory ports.

## 5. Repository Structure Baseline

Source implementation follows `PROJECT_STRUCTURE_AND_ENGINE_ARCHITECTURE.md`.

Key package boundaries:

```text
src/mtaffiliate/
  domain/
  engines/
  application/
  ports/
  adapters/
  interfaces/
  workers/
  bootstrap/
  common/

tests/
  unit/
  component/
  contract/
  integration/
  e2e/
  resilience/
  compatibility/
  fixtures/
  fakes/
  factories/
```

Framework-specific imports are forbidden in domain/engine layers.

## 6. API-as-Core Rule

All major components communicate through versioned business-level contracts.

Public component boundaries must not expose brittle implementation details such as DOM paths, Android coordinates or internal ORM objects.

Baseline communication surfaces:
- REST/HTTP for commands, queries, registration, lease/ACK and administrative APIs;
- WebSocket for live worker/device/Scene telemetry;
- durable database state for authoritative business/job state;
- local outbox for acknowledged worker delivery.

Detailed semantic contracts: `APPLICATION_AND_ENGINE_CONTRACTS.md` and `API_COMMUNICATION_AND_PLUGIN_ARCHITECTURE.md`.

## 7. Runtime Ownership

| Resource | Authoritative owner |
|---|---|
| Business rules | Domain Engines / Back Office |
| Application orchestration | Application Use Cases |
| Job lifecycle | Shared Job Engine |
| Product identity/history | Product domain + repositories |
| Offer identity/history | Offer domain + repositories |
| Video identity/fingerprint | Content Identity Engine + repositories |
| Publishing policy/ledger transition | Publishing Engine + repositories |
| Device discovery/lifecycle | Device Host Manager |
| Worker process lifecycle | Worker Supervisor on Device Host |
| Scene execution decision | Scene Engine / Worker Runtime |
| Android selector profile | UI Automation adapter registry |
| Screen-stream lifecycle | Screen Stream adapter/manager |
| Presentation state | UI shell only; never durable business truth |

No resource may have two independent lifecycle authorities.

## 8. Persistence Baseline

- SQLAlchemy 2.x behind repository/UnitOfWork boundaries.
- Alembic manages schema revision.
- SQLite Tier-1 Portable Mode.
- PostgreSQL Tier-1 Farm Mode.
- workers/UI do not mutate canonical tables directly.
- short transactions only; no external/browser/device/human wait inside transaction.
- optimistic concurrency, idempotency and constraints enforce invariants.

Canonical semantic model: `DATA_MODEL.md`.

## 9. Reliability Invariants

1. One active lease per executable Job.
2. One active automation Worker per Android Device.
3. Worker reports facts; Back Office owns canonical transitions.
4. Side-effecting retries require idempotency/reconciliation semantics.
5. No SQL transaction waits on browser/mobile/UI/network/human work.
6. Every acknowledged observation/result survives restart.
7. Unknown publish outcome becomes reconciliation/`NEEDS_HUMAN`, never blind retry.
8. Duplicate prevention exists at planning/queue/pre-submit/ledger boundaries as applicable.
9. Worker/Host failure is isolated from unrelated workers.
10. Overload causes admission throttling/controlled degradation rather than unbounded queues/resource collapse.
11. UI close/restart cannot invalidate durable job state.
12. domain/engine behavior is deterministic under controlled inputs where expected.

## 10. Testability Baseline

Testing is architectural, not optional cleanup.

Critical business behavior must be testable without:
- graphical UI;
- physical Android device;
- live browser;
- external network;
- production database.

Foundation must include fake/in-memory adapters, deterministic clock/ID facilities and separate unit/component/contract/integration/resilience/compatibility test layers.

Governing test policy: `TEST_STRATEGY_AND_QUALITY_GATES.md`.

## 11. UI Policy

UI is optional shell.

Allowed:
- commands;
- queries/read models;
- telemetry;
- operator approval/takeover;
- visualization.

Prohibited:
- domain scoring;
- duplicate decisions;
- job transitions;
- direct ORM writes;
- hidden retry/recovery business policy;
- raw selector macros as business workflow.

Governing UI policy: `UI_SHELL_AND_PRESENTATION_ARCHITECTURE.md`.

## 12. Deployment Modes

### Portable Mode
- one Windows PC;
- Back Office + optional UI + Device Host on same machine;
- SQLite;
- local worker processes;
- optional bundled external tools where licensing permits.

### Farm Mode
- one logical Back Office;
- PostgreSQL;
- multiple Device Hosts/browser workers;
- same application/domain contracts;
- no domain redesign.

### Test Mode
- in-memory/fake ports;
- optional real SQLite/PostgreSQL integration fixtures;
- scripted browser/Scene snapshots;
- no UI/device required for domain/component suites.

## 12.1 Program 1 Developer Pack

For Program 1 specifically, developers must also read:
- `PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md`;
- `PROGRAM1_SYSTEM_ARCHITECTURE.md`;
- `PROGRAM1_UML_AND_RUNTIME_DIAGRAMS.md`;
- `PROGRAM1_ARCHITECTURE_REVIEW_AND_IMPLEMENTATION_PLAN.md`;
- `PROGRAM1_TRACEABILITY_MATRIX.md`;
- `PROGRAM1_DEVELOPER_HANDOFF.md`;
- `PROGRAM1_KANBAN.md`;
- `PROGRAM1_IMPLEMENTATION_CARDS.md`;
- `PROGRAM1_UX_AND_OPERATOR_EXPERIENCE.md`;
- `PROGRAM1_AUTOMATED_TEST_ARCHITECTURE.md`.

This pack is the implementation-ready Program 1 handoff and takes precedence over older generic Step 1 wording where the newer strategy-led design is more specific.

## 12.2 Program 2 Developer Pack

For Program 2 specifically, developers must also read:
- `PROGRAM2_AFFILIATE_SUCCESS_STRATEGY.md`;
- `PROGRAM2_SYSTEM_ARCHITECTURE.md`;
- `PROGRAM2_UML_AND_RUNTIME_DIAGRAMS.md`;
- `PROGRAM2_TRACEABILITY_MATRIX.md`;
- `PROGRAM2_DEVELOPER_HANDOFF.md`;
- `PROGRAM2_KANBAN.md`;
- `PROGRAM2_IMPLEMENTATION_CARDS.md`;
- `PROGRAM2_UX_AND_OPERATOR_EXPERIENCE.md`;
- `PROGRAM2_AUTOMATED_TEST_ARCHITECTURE.md`.

This pack is the implementation-ready Program 2 handoff and takes precedence over older generic Step 2 wording where more specific.

## 12.3 Program 3 Developer Pack

For Program 3 specifically, developers must also read:
- `PROGRAM3_PUBLISHING_SUCCESS_AND_SAFETY_STRATEGY.md`;
- `PROGRAM3_SYSTEM_ARCHITECTURE.md`;
- `PROGRAM3_UML_AND_RUNTIME_DIAGRAMS.md`;
- `PROGRAM3_TRACEABILITY_MATRIX.md`;
- `PROGRAM3_DEVELOPER_HANDOFF.md`;
- `PROGRAM3_KANBAN.md`;
- `PROGRAM3_IMPLEMENTATION_CARDS.md`;
- `PROGRAM3_UX_AND_OPERATOR_EXPERIENCE.md`;
- `PROGRAM3_AUTOMATED_TEST_ARCHITECTURE.md`.

This pack is the implementation-ready Program 3 handoff and takes precedence over older generic Step 3 wording where more specific.

## 13. Required Reading Before Coding

Every developer/agent modifying core behavior must read:
- `PROJECT_CHARTER.md`
- `WORKFLOW.md`
- `ARCHITECTURE.md`
- `ENGINEERING_GOVERNANCE.md`
- `DECISION_LOG.md`
- `PROJECT_STRUCTURE_AND_ENGINE_ARCHITECTURE.md`
- `APPLICATION_AND_ENGINE_CONTRACTS.md`
- `DATA_MODEL.md`
- `TEST_STRATEGY_AND_QUALITY_GATES.md`
- `IMPLEMENTATION_READINESS_AND_DEFINITION_OF_READY.md`
- `TECHNOLOGY_STACK.md`
- `API_COMMUNICATION_AND_PLUGIN_ARCHITECTURE.md`
- `DATABASE_CONCURRENCY_AND_PORTABILITY_SPEC.md`
- relevant Step baseline/specification.

## 14. Foundation Implementation Authorization

The following are authorized to enter coding after card-level Definition of Ready review:
- Python project/package skeleton;
- architectural dependency checks;
- common typed IDs/result/error/correlation primitives;
- configuration foundation;
- SQLAlchemy repository/UnitOfWork foundation;
- Alembic baseline;
- SQLite + PostgreSQL compatibility harness;
- Shared Job Engine;
- API app factory/common contracts;
- worker registration/heartbeat/lease/result reference protocol;
- fake/in-memory adapter library;
- Step 1 fake-driven thin slice;
- Step 2 fake-driven thin slice;
- Content Identity exact-hash thin slice;
- Publishing plan validator thin slice;
- Scene Engine with scripted UI fixtures.

This is the **implementation-ready foundation boundary**.

## 15. Production Feature Gates Still Open

The following must be validated before affected feature may be called production-ready:
- Product Scoring Model v1 exact formula/weights;
- Offer Scoring Model v1 exact formula/weights;
- Product external identity against real Shopee observations;
- Offer/link identity against real Shopee observations;
- final Step1->Step2 and Step2->Step3 payload schemas;
- real Android Shopee Scene inventory/signatures/selectors;
- basket maximum/behavior by relevant app/account version;
- Scene safe-anchor/recovery validation;
- screen-stream/device-host capacity benchmark;
- perceptual fingerprint algorithm/threshold;
- post-submit reconciliation evidence rules;
- numeric pacing/retry defaults from endurance tests.

Do not hard-code guesses for these. Isolate them behind configuration/ports/versioned policies until validated.

## 16. Recommended Implementation Order

Follow vertical slices:
1. FND-001 project skeleton + dependency rules;
2. common primitives/test doubles;
3. persistence + Alembic + DB compatibility;
4. Shared Job Engine + API reference slice;
5. Step 1 fake-driven end-to-end slice;
6. Step 2 fake-driven end-to-end slice;
7. Content Identity + duplicate core;
8. publish-plan validation;
9. Scene Engine simulation;
10. browser/Android concrete adapters;
11. controlled publishing laboratory flow;
12. recovery/failure injection;
13. multi-device scaling;
14. operator UI around stable commands/queries;
15. analytics/learning loop.

## 17. Definition of Ready / Done

Every Kanban card follows `IMPLEMENTATION_READINESS_AND_DEFINITION_OF_READY.md`.

Before coding:
- unresolved CRITICAL/HIGH design issues for the slice = 0.

Before Done:
- tests pass at required layers;
- architecture dependency rules pass;
- documentation/ADR remains conforming;
- failure/idempotency/recovery behavior tested where applicable.

## 18. Handoff Statement

Programs 1–3 now satisfy the current engineering-completion baseline and the maturity target recorded in `PROGRAMS_1_2_3_ENGINEERING_MATURITY_SCORECARD_2026-09-05.md`.

The verified headless control plane includes durable Shared Job authority, Program 1 opportunity handoff, Program 2 commercial decision/link handoff, Program 3 durable publish/device/pre-submit/submission/reconciliation authority, and deterministic cross-program E2E coverage.

This statement does not claim that unvalidated Shopee-specific behavior is production-approved. Live browser/affiliate/Android profiles remain explicit evidence gates and must be promoted through controlled evidence, tests and document updates.