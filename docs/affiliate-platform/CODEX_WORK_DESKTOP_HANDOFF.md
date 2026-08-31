# Codex Work Desktop Handoff — MTAffiliatePlatform

Date: 2026-08-31
Audience: Codex Work Desktop / coding agents / senior developers
Repository: `idev006/MTAffiliatePlatform`
Default branch: `main`

## 1. Purpose

This document is the operational handoff for continuing implementation efficiently without re-discovering project intent.

The repository is document-driven. Source code is implementation evidence, not the highest-level authority. When there is a conflict, follow the governance/SSOT precedence defined in `DEVELOPMENT_HANDOFF_MASTER.md` and resolve the discrepancy intentionally.

## 2. First 10 Minutes in Codex Work Desktop

Execute this sequence before taking a feature card:

```powershell
git status
git branch --show-current
git log -1 --oneline
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
ruff check src tests migrations
```

If the workspace already has a valid `.venv`, reuse it instead of recreating it.

Then read:
1. root `AGENTS.md`;
2. this handoff;
3. `CODEX_NEXT_WORK_QUEUE.md`;
4. `DEVELOPMENT_HANDOFF_MASTER.md`;
5. relevant Program/Step design + Kanban card.

Before unrelated feature work, inspect the current HEAD CI result and reproduce any failing gate locally. A commit being at HEAD does **not** mean it is verified.

## 3. Current Implementation Shape

```text
src/mtaffiliate/
  domain/          pure domain types/invariants
  engines/         deterministic policy/state-machine logic
  application/     use-case orchestration
  ports/           inward-facing interfaces/contracts
  adapters/        SQLAlchemy, fake workers, scripted Android, export parsers, etc.
  interfaces/      FastAPI and other delivery surfaces
  bootstrap/       composition/config/migrations wiring
  common/          shared primitives
```

Tests are layered under:

```text
tests/
  unit/
  component/
  contract/
  integration/
  stress/          when present / marker-driven
  fixtures/
```

Do not move business decisions outward into adapters or routes merely because integration code is easier to write there.

## 4. Verified Foundation Baseline

Program 1 has a durable/headless foundation with Product observations/intelligence, API contracts, SQLAlchemy/SQLite persistence, Alembic and adversarial verification.

Program 2 foundation includes:
- Affiliate Offer domain model;
- eligibility/scoring/ranking framework;
- preferred/backup selection;
- account-context provenance;
- application/API contracts;
- in-memory and SQLAlchemy/SQLite repositories;
- worker command/batch contracts;
- deterministic fake worker;
- atomic file outbox;
- Affiliate Link / export artifact contracts;
- synthetic export parser laboratory.

Program 3 foundation includes:
- immutable PublishPlan;
- duplicate/publishing guard;
- durable Publishing Ledger;
- Scene recognition;
- Scene workflow/transition validation;
- bounded recovery rules;
- device ownership/lease/resource admission foundations;
- replaceable Android ports;
- scripted Android adapter;
- headless worker executor;
- conservative publish reconciliation;
- full scripted multi-scene workflow laboratory.

The authoritative status/evidence record is `PROGRAM2_PROGRAM3_VERIFICATION_REPORT_2026-08-31.md`. Treat anything added after its last verified code head as requiring fresh CI evidence.

## 5. Current CI Handoff Note

The earlier verified Program 2/3 foundation code head was green in CI #155.

A later head added the synthetic export parser and full scripted workflow. CI #165 found three Ruff-only findings:
- wrong exception type for a non-list JSON root;
- import ordering in the full scripted workflow test;
- `zip` over successive pairs where `itertools.pairwise` is preferred.

These findings were corrected in subsequent commits without weakening Ruff. Codex must verify the latest HEAD and make current-tree CI green before treating the new parser/full-workflow additions as verified.

This is a deliberate handoff rule: **verified status follows evidence, not chronology.**

## 6. Mandatory Architectural Rules

### Engine-first / headless-first
Core behavior must be executable/testable without:
- PySide6 UI;
- live Shopee browser;
- physical Android phone;
- Internet;
- production database.

### Dependency direction

```text
Presentation / Transport
        -> Application
        -> Domain Engines
        -> Ports
        <- Adapters implement Ports
```

No framework imports in domain/engine code.

### Authority separation
- Back Office is Control Plane / canonical decision authority.
- Browser workers collect facts and execute bounded commands.
- Android workers execute an approved PublishPlan; they do not make commercial choices.
- Device Host owns device/process/resource admission, not business policy.
- DB persists truth but is not a dumping ground for business logic.

## 7. Program 2 Development Boundary

Safe to continue without real Shopee evidence:
- parser interfaces and synthetic/golden fixtures;
- link/export artifact validation;
- worker protocol/outbox reliability;
- persistence/restart/idempotency/concurrency;
- application/API contracts;
- PostgreSQL repository compatibility;
- fake/session/schema-drift classifications;
- test harnesses.

Evidence-gated — do not guess:
- canonical Offer identity;
- production Offer Scoring Model v1;
- real account/session effects;
- real export schema/parser;
- DOM/selectors;
- production pacing/capacity.

## 8. Program 3 Development Boundary

Safe to continue without a physical phone:
- Scene/workflow state machines;
- selector-resolution abstractions without real selectors;
- fake/scripted adapters;
- checkpoint/event contracts;
- duplicate/reconciliation policy;
- host/device ownership/resource state models;
- failure injection;
- restart/idempotency/concurrency;
- full fake E2E laboratory flows.

Evidence-gated — do not guess:
- Shopee Scene signatures;
- Android selectors/resource IDs/coordinates;
- Safe Anchor details;
- real ADB/uiautomator2 behavior;
- post-submit reconciliation evidence source;
- basket capacity;
- perceptual fingerprint threshold;
- device farm capacity numbers.

## 9. Golden Program 3 Execution Loop

Every UI action path must preserve:

```text
Observe
  -> Recognize
  -> Validate
  -> Act
  -> Verify transition
  -> Checkpoint
```

Forbidden:
- acting on UNKNOWN/AMBIGUOUS Scene;
- checkpointing an unverified transition;
- restarting/reposting blindly after an uncertain irreversible submit;
- embedding brittle coordinates as business workflow semantics.

## 10. Test Strategy for Each Change

Use the narrowest relevant layer first:

```powershell
pytest tests/unit/<target>.py
pytest tests/component/<target>.py
pytest tests/contract/<target>.py
pytest -m integration tests/integration/sqlite --timeout=60
```

Before a slice is Done, run repository gates matching CI:

```powershell
ruff check src tests migrations
pytest -m "not stress and not integration"
pytest -m integration tests/integration/sqlite --timeout=60
pytest -m stress --timeout=60
```

For code inside selected CI coverage scopes, preserve the 95% branch-coverage policy in `.github/workflows/ci.yml`. Add meaningful tests rather than excluding logic or lowering thresholds.

## 11. Database Rules

- SQLAlchemy 2.x behind repositories/UoW-style boundaries.
- Alembic owns schema evolution.
- SQLite = Tier-1 Portable Mode.
- PostgreSQL = Tier-1 Farm Mode target.
- No external wait while a SQL transaction is open.
- Repository adapters normalize dialect behavior before reconstructing domain objects.
- Durable ACK semantics must atomically preserve the state required to reproduce an acknowledged result after restart.

Migration changes require migration tests plus restart/compatibility tests where applicable.

## 12. Configuration Rules

Use typed configuration for legitimate policy/deployment knobs.

Do **not** make safety invariants disable-able merely to satisfy “configurable/no hard-code” goals.

Examples of invariants that should remain enforced in code/contracts:
- no blind repost after ambiguous publish;
- unknown Scene blocks action;
- one active device owner;
- durable ACK/restart consistency.

Shopee-specific values that lack evidence should be represented as unresolved/versioned profiles or ports, not invented defaults masquerading as production truth.

## 13. Git / Change Management

Recommended Codex workflow:

```text
inspect workspace
  -> choose one Kanban slice
  -> create/checkout focused branch when appropriate
  -> update governing doc first if behavior changes
  -> implement + tests
  -> run narrow tests
  -> run gates
  -> review diff
  -> small coherent commit(s)
  -> update verification/Kanban/CAPA
```

Never discard or rewrite unrelated user changes in the desktop workspace.

Avoid broad refactors while fixing a CI defect. Keep fixes attributable and regression-testable.

## 14. RCA / CAPA Trigger

Update `PROBLEM_LESSON_AND_CAPA_LOG.md` or the Program-specific CAPA document when a defect is meaningful, especially if it reveals:
- broken reliability invariant;
- wrong transaction boundary;
- incorrect idempotency semantics;
- architecture boundary violation;
- CI gate weakness;
- real adapter behavior different from fake assumptions;
- safety policy bypass.

Minor formatting-only fixes need not generate heavyweight RCA unless they expose a process pattern worth preventing.

## 15. Definition of Done for Codex

A card is not Done merely because code exists.

Done means:
- governing design is conforming;
- implementation respects dependency/authority boundaries;
- positive and negative tests exist;
- restart/idempotency/recovery tests exist when relevant;
- relevant local gates pass;
- current CI evidence is green or explicitly reported as pending;
- Kanban status is updated;
- verification/CAPA documentation is updated when material;
- remaining real-platform evidence gates are named rather than guessed away.

## 16. Expected End-of-Session Handoff

Codex should leave a concise record containing:

```text
Work Item:
Status:
HEAD/Branch:
Files Changed:
Tests Run:
CI State:
Architecture/ADR Changes:
Kanban Updated:
CAPA/Verification Updated:
Remaining Evidence Gates:
Recommended Next Card:
```

This makes the next Codex Work Desktop session resumable without reconstructing the previous session from git history.
