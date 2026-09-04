# AGENTS.md — MTAffiliatePlatform

This file is the repository-level operating contract for Codex, coding agents and developers.

## Mission

Develop MTAffiliatePlatform according to the repository SSOT. Do not reverse-engineer a new architecture from source code when governing documents already define the intent.

**Project must follow the document.**

## Start Here — Mandatory Reading Order

Before changing core behavior, read at minimum:

1. `docs/affiliate-platform/CODEX_WORK_DESKTOP_HANDOFF.md`
2. `docs/affiliate-platform/CODEX_NEXT_WORK_QUEUE.md`
3. `docs/affiliate-platform/DEVELOPMENT_HANDOFF_MASTER.md`
4. `docs/affiliate-platform/PROJECT_CHARTER.md`
5. `docs/affiliate-platform/WORKFLOW.md`
6. `docs/affiliate-platform/ARCHITECTURE.md`
7. `docs/affiliate-platform/ENGINEERING_GOVERNANCE.md`
8. `docs/affiliate-platform/DECISION_LOG.md`
9. `docs/affiliate-platform/PROJECT_STRUCTURE_AND_ENGINE_ARCHITECTURE.md`
10. `docs/affiliate-platform/APPLICATION_AND_ENGINE_CONTRACTS.md`
11. `docs/affiliate-platform/DATA_MODEL.md`
12. `docs/affiliate-platform/TEST_STRATEGY_AND_QUALITY_GATES.md`
13. `docs/affiliate-platform/IMPLEMENTATION_READINESS_AND_DEFINITION_OF_READY.md`
14. the relevant Program/Step specification and Kanban card.

For Program 1 work, also read before changing business behavior:
- `docs/affiliate-platform/PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md`
- `docs/affiliate-platform/PROGRAM1_SYSTEM_ARCHITECTURE.md`
- `docs/affiliate-platform/PROGRAM1_UML_AND_RUNTIME_DIAGRAMS.md`
- `docs/affiliate-platform/PROGRAM1_ARCHITECTURE_REVIEW_AND_IMPLEMENTATION_PLAN.md`
- `docs/affiliate-platform/PROGRAM1_TRACEABILITY_MATRIX.md`
- `docs/affiliate-platform/PROGRAM1_IMPLEMENTATION_READINESS.md`
- `docs/affiliate-platform/PROGRAM1_TO_PROGRAM2_HANDOFF_CONTRACT.md`

For Program 2/3 continuation also read:
- `docs/affiliate-platform/PROGRAM2_AFFILIATE_OFFER_DESIGN_AND_READINESS.md`
- `docs/affiliate-platform/PROGRAM3_CONTENT_PUBLISHING_DESIGN_AND_READINESS.md`
- `docs/affiliate-platform/PROGRAM2_PROGRAM3_IMPLEMENTATION_KANBAN.md`
- `docs/affiliate-platform/PROGRAM2_PROGRAM3_VERIFICATION_REPORT_2026-08-31.md`

## Architecture Rules — Non-Negotiable

Dependency direction is inward:

```text
UI / CLI / FastAPI
        -> Application Use Cases
        -> Domain Engines / Policies / State Machines
        -> Ports / Interfaces
        -> Concrete Adapters
```

Rules:
- Domain/engine code must not import FastAPI, SQLAlchemy, browser DOM libraries, ADB, uiautomator2, Appium, scrcpy or PySide6.
- Business policy must not live in route handlers, ORM models, selectors, UI event handlers or adapters.
- Workers report facts; Back Office owns canonical business transitions.
- UI is an optional shell, never the business authority.
- Engines are logical responsibility boundaries, not microservices by default.
- Real infrastructure is wired at the composition root.
- Prefer `Fake first, real adapter second`.

## Safety / Reliability Invariants

Never weaken these to make tests pass:
- Unknown or ambiguous Android Scene blocks business action.
- Unknown publishing outcome must be reconciled or escalated; never blind repost.
- Acknowledged durable data must survive restart.
- No SQL transaction waits on browser/device/network/human activity.
- Side-effect retries require idempotency or reconciliation semantics.
- One active automation owner per Android device.
- Duplicate prevention is enforced at the appropriate planning/queue/pre-submit/ledger boundaries.
- ADB unauthorized requires human authorization; do not bypass platform/device safeguards.

A correctness/safety invariant is not an ordinary configuration toggle.

## Real-Platform Evidence Boundary

Do not invent or freeze Shopee-specific facts that have not been validated. In particular, do not guess:
- canonical Product/Offer identity semantics;
- production scoring formulas/weights;
- browser DOM/selectors/export schemas;
- Android Scene signatures/selectors/resource IDs;
- basket capacity;
- perceptual fingerprint thresholds;
- post-submit reconciliation evidence rules;
- retry/pacing/capacity numbers;
- 10/20/50/100-device scale claims.

Keep such details behind ports, fixtures, versioned policy/config profiles and explicit evidence gates until validated.

## Development Cycle

For every meaningful slice:

```text
Document / Card
    -> Definition of Ready
    -> Implement smallest vertical slice
    -> Unit / Component / Contract tests
    -> Integration / Resilience tests where applicable
    -> Ruff / CI / coverage gates
    -> RCA + CAPA for meaningful defects
    -> Update docs/Kanban/verification evidence
    -> Done
```

Before coding, unresolved CRITICAL/HIGH design issues for the slice must be 0.
Before marking Done, required test layers and documentation must be conforming.

## Local Bootstrap

Python target: 3.12+

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Portable verification commands:

```powershell
ruff check src tests migrations
pytest -m "not stress and not integration"
pytest -m integration tests/integration/sqlite --timeout=60
pytest -m stress --timeout=60
```

CI is authoritative for the repository gates in `.github/workflows/ci.yml`. Do not lower coverage/lint/test thresholds merely to obtain green CI.

## Working Method for Codex Work Desktop

At the start of every session:
1. inspect `git status` and do not overwrite unrelated user changes;
2. inspect current branch/HEAD;
3. read this file plus the Codex handoff/current queue;
4. inspect the latest CI result for current HEAD;
5. reproduce/fix any failing gate before starting unrelated feature work unless the documented card explicitly says otherwise;
6. select one small vertical slice/card;
7. identify governing documents, ports, tests and evidence gate;
8. implement with tests in the same change;
9. run the narrowest relevant test first, then the repository gates;
10. update Kanban/verification/CAPA when the change materially alters project state.

Prefer small, reviewable commits. Do not mix unrelated refactors with a feature/fix.

## Change Discipline

When behavior conflicts with an approved document:
- do not silently change code or documentation;
- determine whether the code is non-conforming or the design intentionally changed;
- if design changes, update the governing document/ADR first or in the same coherent change;
- add/adjust tests that prove the intended contract.

When a CI/test defect is found:
- fix the artifact/root cause;
- do not weaken a legitimate rule;
- add regression coverage when the defect can recur.

## Completion Report Expected from Codex

At the end of a work slice, report:
- card/slice completed;
- files changed;
- architectural/document decisions affected;
- tests executed and results;
- CI status/URL or state if available;
- remaining evidence gates/blockers;
- whether Kanban/verification/CAPA docs were updated.

Do not claim production readiness for evidence-gated Shopee/browser/Android behavior without the required real-world evidence.
