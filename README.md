# MTAffiliatePlatform

Unified Affiliate Intelligence + Automation Platform.

This repository is the authoritative project repository (SSOT) for the three-step platform:

1. Affiliate Opportunity Intelligence (Product / Market Discovery + Product Intelligence)
2. Affiliate Offer Automation
3. Content Publishing / Android Device Farm

## Current Handoff Status

**FOUNDATION / LABORATORY DEVELOPMENT READY — REAL PLATFORM FEATURES REMAIN EVIDENCE-GATED**

The project documentation and headless foundations are sufficient for Codex Work Desktop or a development team to continue vertical-slice development without inventing architecture.

Shopee-specific behaviors that still require real-world validation remain explicit production gates and must not be guessed into hard-coded policy.

## Codex Work Desktop — Start Here

Codex/coding agents must begin with:

1. `AGENTS.md`
2. `docs/affiliate-platform/CODEX_WORK_DESKTOP_HANDOFF.md`
3. `docs/affiliate-platform/CODEX_NEXT_WORK_QUEUE.md`
4. `docs/affiliate-platform/DEVELOPMENT_HANDOFF_MASTER.md`
5. the relevant Program/Step design, Kanban card and verification report.

The Codex handoff includes local bootstrap commands, architecture boundaries, evidence gates, CI rules, Definition of Done and end-of-session reporting format.

**Important:** inspect the CI state of the current HEAD before unrelated feature work. A latest commit is not automatically a verified baseline.

## Engineering Principles

- Document-driven project — project must follow the document.
- Engine-first / headless-first core.
- UI is an optional presentation shell.
- Testability is an architecture requirement.
- API as core.
- Single Source of Truth (SSOT).
- Component-based and pluggable adapters.
- Inward dependency direction.
- System Physiology model: Sense / Decide / Act / Verify / Recover.
- Every component has explicit ownership, health detection and recovery.
- Portable-first, scale-ready deployment.
- Agile Kanban + vertical slices.
- Correctness, recoverability, traceability and testability before raw throughput.

## Architecture Shape

```text
UI / CLI / FastAPI
        |
        v
Application Use Cases
        |
        v
Domain Engines / State Machines / Policies
        |
        v
Ports / Interfaces
        |
        v
Concrete Adapters
DB / Browser / Android / Media / Notifications
```

Core business behavior must be testable without graphical UI, live browser or physical Android device.

Every important flow is reviewed through:

```text
Input
  -> Sense / Observe
  -> Validate / Interpret
  -> Decide / Plan
  -> Act / Execute
  -> Verify
  -> Record Durable Output
  -> Feedback / Learn
  -> Recover / Escalate when abnormal
```

## Full Developer Reading Order

After the Codex entrypoint documents, read:

1. `docs/affiliate-platform/PROJECT_CHARTER.md`
2. `docs/affiliate-platform/WORKFLOW.md`
3. `docs/affiliate-platform/ARCHITECTURE.md`
4. `docs/affiliate-platform/SYSTEM_PHYSIOLOGY_MODEL.md`
5. `docs/affiliate-platform/COMPONENT_RESPONSIBILITY_AND_HEALTH_MATRIX.md`
6. `docs/affiliate-platform/SYSTEM_DIAGRAMS.md`
7. `docs/affiliate-platform/INTEGRATION_DIAGRAMS.md`
8. `docs/affiliate-platform/SEQUENCE_DIAGRAMS.md`
9. `docs/affiliate-platform/ENGINEERING_GOVERNANCE.md`
10. `docs/affiliate-platform/DECISION_LOG.md`
11. `docs/affiliate-platform/PROJECT_STRUCTURE_AND_ENGINE_ARCHITECTURE.md`
12. `docs/affiliate-platform/APPLICATION_AND_ENGINE_CONTRACTS.md`
13. `docs/affiliate-platform/DATA_MODEL.md`
14. `docs/affiliate-platform/TEST_STRATEGY_AND_QUALITY_GATES.md`
15. `docs/affiliate-platform/IMPLEMENTATION_READINESS_AND_DEFINITION_OF_READY.md`
16. `docs/affiliate-platform/TECHNOLOGY_STACK.md`
17. `docs/affiliate-platform/specs/README.md`

`WORKFLOW.md` is the canonical business pipeline. Program 1 business strategy is governed by `PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md`, with implementation architecture in `PROGRAM1_SYSTEM_ARCHITECTURE.md`, runtime/UML collaboration in `PROGRAM1_UML_AND_RUNTIME_DIAGRAMS.md`, the execution roadmap in `PROGRAM1_ARCHITECTURE_REVIEW_AND_IMPLEMENTATION_PLAN.md`, and strategy-to-code verification in `PROGRAM1_TRACEABILITY_MATRIX.md`. Affiliate/Marketing Strategy defines decision hypotheses/signals before engineering collection logic. `SYSTEM_PHYSIOLOGY_MODEL.md` defines system-wide sensing, control, verification, health, resource-homeostasis and recovery rules. `COMPONENT_RESPONSIBILITY_AND_HEALTH_MATRIX.md` defines ownership and Input/Process/Output/Health/Failure/Recovery boundaries. `SYSTEM_DIAGRAMS.md` contains context/component/use-case/swimlane/activity/state/deployment views. `INTEGRATION_DIAGRAMS.md` defines logical, step-to-step, runtime, protocol, SSOT, failure-boundary and test-integration views. `SEQUENCE_DIAGRAMS.md` is the normative runtime-collaboration pack for critical multi-component flows.

Latest senior review record: `docs/affiliate-platform/ARCHITECTURE_REVIEW_2026-08-31_SYSTEM_PHYSIOLOGY.md`.

## Current Development Boundary

Authorized/effective development areas include:
- Python `src/` architecture and dependency checks;
- typed domain/application contracts;
- configuration foundation;
- SQLAlchemy repositories + Alembic;
- SQLite Tier-1 portable persistence and PostgreSQL compatibility work;
- Shared Job Engine integration;
- FastAPI application/common contracts;
- worker registration/heartbeat/lease/result/outbox flows;
- reusable fake/in-memory adapters;
- Program 1 Affiliate Opportunity Intelligence foundation, governed by `docs/affiliate-platform/PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md`;
- Program 2 Offer Intelligence, worker/outbox and synthetic export laboratory;
- Program 3 PublishPlan/duplicate ledger, Scene/Device Host foundations and scripted Android laboratory;
- controlled failure/recovery fixtures and resilience tests.

Real Shopee/browser/Android facts remain evidence-gated as documented in the Program readiness files and `CODEX_NEXT_WORK_QUEUE.md`.

## Local Development

Python target: 3.12+

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
ruff check src tests migrations
pytest -m "not stress and not integration"
pytest -m integration tests/integration/sqlite --timeout=60
pytest -m stress --timeout=60
```

CI definitions and authoritative quality gates are in `.github/workflows/ci.yml`.

## Separate Program Runtime Profiles

Each program can be installed/launched separately while keeping one shared core:

```powershell
mtaffiliate-program1-api
mtaffiliate-program2-api
mtaffiliate-program3-api
mtaffiliate-all-api
```

Direct ASGI module paths are also available:

```powershell
uvicorn mtaffiliate.runtime.program1:app --port 8001
uvicorn mtaffiliate.runtime.program2:app --port 8002
uvicorn mtaffiliate.runtime.program3:app --port 8003
uvicorn mtaffiliate.runtime.all:app --port 8000
```

See `docs/affiliate-platform/INSTALLATION_PROFILES.md`.

## Optional UI

PySide6/Qt 6 is the baseline desktop UI technology when a GUI becomes useful. The UI must wrap stable application commands/queries/read models and must not own scoring, duplicate policy, job state transitions, recovery policy or direct database writes.

## Previous Repository

`idev006/MTShopeeMobile` is retained as an existing Android publishing implementation/historical reference. It is no longer the authoritative repository for the overall Affiliate Platform.
