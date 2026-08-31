# MTAffiliatePlatform

Unified Affiliate Intelligence + Automation Platform.

This repository is the authoritative project repository (SSOT) for the three-step platform:

1. Product Discovery / Product Intelligence
2. Affiliate Offer Automation
3. Content Publishing / Android Device Farm

## Current Handoff Status

**FOUNDATION IMPLEMENTATION READY / FEATURE-GATED HANDOFF**

The project documentation is sufficient for the development team to start foundation code and isolated vertical slices without inventing architecture.

Shopee-specific behaviors that still require real-world validation remain explicit production gates and must not be guessed into hard-coded policy.

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

## Developer Start Here

Read in this order:

1. `docs/affiliate-platform/DEVELOPMENT_HANDOFF_MASTER.md`
2. `docs/affiliate-platform/PROJECT_CHARTER.md`
3. `docs/affiliate-platform/WORKFLOW.md`
4. `docs/affiliate-platform/ARCHITECTURE.md`
5. `docs/affiliate-platform/SYSTEM_PHYSIOLOGY_MODEL.md`
6. `docs/affiliate-platform/COMPONENT_RESPONSIBILITY_AND_HEALTH_MATRIX.md`
7. `docs/affiliate-platform/SYSTEM_DIAGRAMS.md`
8. `docs/affiliate-platform/INTEGRATION_DIAGRAMS.md`
9. `docs/affiliate-platform/SEQUENCE_DIAGRAMS.md`
10. `docs/affiliate-platform/ENGINEERING_GOVERNANCE.md`
11. `docs/affiliate-platform/PROJECT_STRUCTURE_AND_ENGINE_ARCHITECTURE.md`
12. `docs/affiliate-platform/APPLICATION_AND_ENGINE_CONTRACTS.md`
13. `docs/affiliate-platform/DATA_MODEL.md`
14. `docs/affiliate-platform/TEST_STRATEGY_AND_QUALITY_GATES.md`
15. `docs/affiliate-platform/IMPLEMENTATION_READINESS_AND_DEFINITION_OF_READY.md`
16. `docs/affiliate-platform/TECHNOLOGY_STACK.md`
17. `docs/affiliate-platform/specs/README.md`

`WORKFLOW.md` is the canonical business pipeline. `SYSTEM_PHYSIOLOGY_MODEL.md` defines system-wide sensing, control, verification, health, resource-homeostasis and recovery rules. `COMPONENT_RESPONSIBILITY_AND_HEALTH_MATRIX.md` defines ownership and Input/Process/Output/Health/Failure/Recovery boundaries. `SYSTEM_DIAGRAMS.md` contains context/component/use-case/swimlane/activity/state/deployment views. `INTEGRATION_DIAGRAMS.md` defines logical, step-to-step, runtime, protocol, SSOT, failure-boundary and test-integration views. `SEQUENCE_DIAGRAMS.md` is the normative runtime-collaboration pack for critical multi-component flows.

Latest senior review record: `docs/affiliate-platform/ARCHITECTURE_REVIEW_2026-08-31_SYSTEM_PHYSIOLOGY.md`.

## Foundation Implementation Boundary

Authorized implementation areas include:
- Python `src/` project skeleton and architecture checks;
- common typed IDs/result/errors/correlation primitives;
- configuration foundation;
- SQLAlchemy/Repository/UnitOfWork + Alembic;
- SQLite/PostgreSQL compatibility harness;
- Shared Job Engine;
- FastAPI application factory/common contracts;
- worker registration/heartbeat/lease/result reference flow;
- reusable fake/in-memory adapters;
- Step 1 fake-driven thin slice;
- Step 2 fake-driven thin slice;
- Content Identity exact-hash core;
- Publish Plan validation;
- Scene Engine simulation with scripted UI fixtures;
- common component health event vocabulary and fault-simulation fixtures.

## Optional UI

PySide6/Qt 6 is the baseline desktop UI technology when a GUI becomes useful. The UI must wrap stable application commands/queries/read models and must not own scoring, duplicate policy, job state transitions, recovery policy or direct database writes.

## Previous Repository

`idev006/MTShopeeMobile` is retained as an existing Android publishing implementation/historical reference. It is no longer the authoritative repository for the overall Affiliate Platform.