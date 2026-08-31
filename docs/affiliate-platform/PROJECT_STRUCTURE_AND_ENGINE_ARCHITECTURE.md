# Project Structure and Engine-First Architecture

Status: IMPLEMENTATION HANDOFF POLICY
Date: 2026-08-31

## 1. Objective

Define a project structure that is testable-friendly, headless-first, component-based and suitable for both Portable Mode and Farm Mode.

The core rule is:

> **Business capability lives in engines/services that can run without any graphical UI. UI is an adapter/shell over application APIs and must not own business rules.**

This allows the team to build, test and automate the system before a desktop UI exists, while keeping PySide6 or another future UI replaceable.

## 2. Architectural Shape

```text
UI / CLI / HTTP API / Worker Transport
                |
                v
        Application Layer
     Use Cases / Orchestration
                |
                v
          Domain Engines
 Rules / State Machines / Policies
                |
          Ports / Interfaces
                |
      +---------+---------+
      |         |         |
      v         v         v
 Persistence  Platform   External
 Adapters      Adapters    Services
```

Dependency direction is inward only.

Outer layers may depend on inner layers. Inner layers must not import PySide6, FastAPI, SQLAlchemy, browser APIs, ADB, uiautomator2, scrcpy or other infrastructure-specific libraries.

## 3. Proposed Repository Layout

```text
MTAffiliatePlatform/
├─ pyproject.toml
├─ README.md
├─ config/
│  ├─ default.toml
│  ├─ portable.toml
│  ├─ farm.toml
│  └─ local.toml.example
├─ docs/
│  └─ affiliate-platform/
├─ src/
│  └─ mtaffiliate/
│     ├─ domain/
│     │  ├─ shared/
│     │  ├─ product/
│     │  ├─ offer/
│     │  ├─ content/
│     │  └─ publishing/
│     ├─ engines/
│     │  ├─ job_engine/
│     │  ├─ product_intelligence_engine/
│     │  ├─ offer_engine/
│     │  ├─ content_identity_engine/
│     │  ├─ publishing_engine/
│     │  └─ scene_engine/
│     ├─ application/
│     │  ├─ commands/
│     │  ├─ queries/
│     │  ├─ use_cases/
│     │  └─ dto/
│     ├─ ports/
│     │  ├─ repositories/
│     │  ├─ messaging/
│     │  ├─ product_sources/
│     │  ├─ affiliate_browser/
│     │  ├─ android/
│     │  ├─ media/
│     │  └─ observability/
│     ├─ adapters/
│     │  ├─ persistence/
│     │  │  ├─ sqlite/
│     │  │  └─ postgres/
│     │  ├─ browser/
│     │  ├─ android/
│     │  ├─ media/
│     │  └─ notifications/
│     ├─ interfaces/
│     │  ├─ api/
│     │  ├─ cli/
│     │  └─ ui/
│     ├─ workers/
│     │  ├─ browser_worker/
│     │  ├─ device_host/
│     │  └─ android_worker/
│     ├─ bootstrap/
│     │  ├─ container.py
│     │  ├─ config.py
│     │  ├─ paths.py
│     │  └─ runtime.py
│     └─ common/
│        ├─ ids.py
│        ├─ clock.py
│        ├─ errors.py
│        └─ result.py
├─ migrations/
├─ data/
├─ logs/
├─ cache/
├─ outbox/
├─ artifacts/
├─ tests/
│  ├─ unit/
│  ├─ component/
│  ├─ contract/
│  ├─ integration/
│  ├─ e2e/
│  ├─ resilience/
│  ├─ compatibility/
│  ├─ fixtures/
│  ├─ fakes/
│  └─ factories/
├─ tools/
├─ scripts/
└─ packaging/
```

This is the baseline structure. Minor naming changes are allowed only if the dependency rules remain intact.

Runtime-owned paths must be resolved through the project PathManager/RuntimePaths service rather than assumed directly from this physical tree. Governing policy: `PATH_AND_CONFIGURATION_POLICY.md`.

## 4. Engine Definition

An Engine is a deterministic or controlled stateful domain component that:
- accepts explicit input/command objects;
- depends on ports/interfaces instead of concrete infrastructure;
- returns typed results/events;
- exposes observable state transitions;
- can be instantiated in tests without UI, web server or physical device;
- never performs hidden global side effects.

An Engine is appropriate when logic contains rules, ranking, state transitions, retries/recovery policy, orchestration or reusable decision behavior.

Do not create an Engine merely to rename a utility function.

## 5. Baseline Engines

### Shared Job Engine
Owns:
- job state machine;
- lease semantics;
- attempt policy;
- checkpoint policy;
- idempotency decisions;
- terminal-state validation.

### Product Intelligence Engine
Owns:
- normalization inputs;
- feature calculation;
- scoring/ranking policy;
- shortlist policy;
- explainability output.

It does not scrape pages.

### Affiliate Offer Engine
Owns:
- candidate eligibility;
- freshness policy;
- ranking/preferred/backup selection;
- account-context-aware validation.

It does not control browser DOM directly.

### Content Identity Engine
Owns:
- exact hash identity;
- perceptual fingerprint comparison policy;
- duplicate classification;
- platform duplicate-gate decisions.

Media extraction itself is behind a MediaPort.

### Publishing Engine
Owns:
- publish-plan validation;
- duplicate gates;
- product/video/offer/account/device constraints;
- irreversible-action guards;
- publish outcome reconciliation policy;
- Publishing Ledger transition rules.

It does not tap Android UI directly.

### Scene Engine
Owns:
- Scene recognition decision;
- Scene confidence evaluation;
- expected transition validation;
- Process/Action sequencing;
- bounded recovery policy;
- safe-anchor selection;
- transition events/checkpoints.

Android selectors and device commands remain adapters.

## 6. Application Layer

Application use cases coordinate engines and ports.

Examples:
- DiscoverProducts
- ScoreProducts
- SelectAffiliateOffers
- RegisterVideo
- BuildPublishPlan
- DispatchPublishJob
- RecordWorkerResult
- ReconcilePublishOutcome

Application use cases may open short database transactions through a UnitOfWork/Repository port, but domain engines must not know SQLAlchemy sessions.

## 7. Ports and Adapters Rule

Every external dependency with meaningful variability or side effects must sit behind a port where practical.

Examples:
- ClockPort for deterministic time tests;
- IdGeneratorPort where reproducible IDs matter;
- ProductSourcePort;
- AffiliateBrowserPort;
- Repository ports;
- DeviceTransportPort;
- UIAutomationPort;
- ScreenStreamPort;
- MediaProbePort;
- EventPublisherPort;
- NotificationPort.

Tests use Fakes/InMemory adapters implementing the same ports.

## 8. Path and Configuration Boundary

Filesystem layout and configuration are infrastructure/bootstrap concerns.

Mandatory rules:
- use `pathlib.Path`;
- resolve managed filesystem locations through injectable `PathManager`/`RuntimePaths`;
- never rely on the current working directory for correctness;
- prefer relative/logical paths under explicit managed roots;
- do not hard-code developer-specific absolute paths;
- TOML is the baseline human-editable settings format;
- typed settings are validated at startup;
- secrets are separated from ordinary committed TOML;
- mutable operational/business values are configuration/rules rather than scattered constants;
- engines receive only typed config/policy objects they need, not a global mutable settings singleton.

Governing policy: `PATH_AND_CONFIGURATION_POLICY.md`.

## 9. UI Boundary

The desktop UI may:
- send application commands;
- query read models;
- subscribe to telemetry/events;
- display validation errors;
- request operator-approved actions.

The desktop UI must not:
- calculate product or offer scores;
- mutate canonical ORM models directly;
- decide job transitions;
- decide duplicate policy;
- own retry/recovery policy;
- execute raw Android selectors as business behavior.

Closing the UI must not invalidate durable business state.

## 10. Headless Requirement

Before GUI implementation, all critical business workflows must be executable through at least one headless interface, normally application tests and/or CLI/API.

Minimum headless scenarios:
1. create and lease a job;
2. ingest product observations and produce shortlist output;
3. ingest offer candidates and produce selected offers;
4. register a video and evaluate duplicate state;
5. construct and validate a publish plan;
6. simulate Scene workflow with fake Android adapter;
7. record/reconcile publishing result.

## 11. Dependency Enforcement

CI must eventually enforce architectural boundaries using one or more of:
- import-linter;
- custom dependency tests;
- module graph checks.

Mandatory rules:
- `domain` imports no `adapters`, `interfaces`, FastAPI, PySide6 or SQLAlchemy;
- `engines` import domain types and ports only;
- `application` may import domain/engines/ports;
- `adapters` implement ports;
- `interfaces` call application use cases;
- UI never imports concrete persistence repositories directly.

Additional static/conformance checks should flag:
- obvious absolute path literals in source;
- direct use of `os.getcwd()`/working-directory assumptions for canonical paths;
- operational timeout/retry/device limits duplicated outside typed settings/rules;
- direct reading of TOML from domain/engine modules.

## 12. Composition Root

Concrete dependency wiring belongs only in bootstrap/composition-root modules.

Example deployment compositions:
- Portable: SQLite + local API + local Device Host + optional PySide6 shell;
- Farm: PostgreSQL + central API + remote workers/device hosts;
- Test: InMemory repositories + FakeClock + FakeDevice + FakeBrowser + Temp PathManager.

The domain/application code is unchanged across these compositions.

Composition root also owns:
- configuration profile selection;
- PathManager root selection;
- secret-provider binding;
- concrete repository/adapter selection;
- startup validation.

## 13. Testability Acceptance Criteria

A module is not accepted as architecture-conforming if it cannot be tested without launching unrelated infrastructure.

Critical domain behavior must be testable with:
- deterministic inputs;
- controlled clock/randomness;
- in-memory/fake ports;
- temporary filesystem roots;
- test TOML/settings profiles;
- no network;
- no browser;
- no Android phone;
- no graphical UI.

Integration tests then verify concrete adapters separately.

## 14. Implementation Rule

For every new feature, developers must build in this order where applicable:

`Domain rule/state -> Engine/Application use case -> Port -> Fake/Test -> Concrete Adapter -> API/CLI -> UI shell`

UI-first implementation is prohibited for business-critical behavior unless explicitly approved by ADR.

Path/config rules are part of the same Definition of Ready: new code may not introduce hidden machine-specific paths or tunable hard-coded values.
