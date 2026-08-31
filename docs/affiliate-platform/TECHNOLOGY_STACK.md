# Technology Stack Baseline

Status: IMPLEMENTATION HANDOFF BASELINE
Date: 2026-08-31

## Principles
- Portable-first, scale-ready.
- API-as-core.
- Engine-first / headless-first.
- UI is optional presentation shell.
- Component-based and pluggable.
- Testability is an architecture requirement.
- Database engine must be replaceable behind repository/storage interfaces.
- Tool choices are replaceable adapters unless explicitly promoted to domain policy.

## Python Core
- Python 3.12+ target runtime.
- `src/` package layout.
- Domain/Engine/Application layers must remain framework-independent.
- Dependency injection/composition is explicit at bootstrap/runtime boundaries; do not use hidden global service locators for business dependencies.

## Back Office / Shared Core
- FastAPI for versioned REST API and WebSocket telemetry endpoints.
- Pydantic v2 for API DTOs, configuration and contract validation.
- Uvicorn as local ASGI runtime; production server topology remains deployment-specific.
- CLI/admin interface should exist for core operational workflows and laboratory use.

## Desktop UI — Optional Shell
- PySide6 / Qt 6 is the baseline desktop UI technology when a GUI is required.
- Core engines/application must not import PySide6.
- UI communicates through application commands/queries/read models/events.
- UI implementation may be deferred until stable vertical slices exist.

## Persistence
- SQLAlchemy 2.x ORM/Core in persistence adapters only.
- Repository Pattern + Unit of Work boundary between application/domain services and persistence.
- Alembic for schema migrations and database revision tracking.
- SQLite for default Portable Mode.
- PostgreSQL for Farm/Server Mode.
- MySQL/MariaDB may be added later only after compatibility tests; not Tier-1 initially.

## Browser Workers — Step 1 / Step 2
- Chrome/Chromium Extension, Manifest V3.
- Extension Side Panel API for worker management UI where supported.
- Content Script as replaceable Shopee page adapter.
- Extension Service Worker for lifecycle, API transport, local outbox and message routing.
- REST/HTTP + WebSocket client to Back Office.
- Saved sanitized DOM/data fixtures for parser/schema regression tests.

## Android / Step 3
- ADB as initial DeviceTransportAdapter candidate.
- uiautomator2 family as primary semantic UI automation candidate.
- Appium + UiAutomator2 as optional compatible/alternative adapter when its ecosystem is advantageous.
- scrcpy as initial ScreenStreamAdapter / operator-control candidate.
- STF/DeviceFarmer-style or other streaming/control implementations must be benchmarked before high-scale production lock.
- Scene Engine itself must run against scripted fake UI snapshots/hierarchies with no real phone dependency.

## Media / Video Identity
- FFmpeg / ffprobe for deterministic media metadata/extraction operations behind Media ports.
- SHA-256 for exact file identity.
- Perceptual video/audio fingerprint libraries to be selected by benchmark; algorithm and thresholds are not frozen yet.

## Testing
Baseline:
- pytest.
- pytest-asyncio where async boundaries require it.
- FastAPI application/contract tests.
- SQLAlchemy repository tests.
- DB compatibility suite for SQLite and PostgreSQL.
- failure-injection tests for job leasing, ACK loss, worker crash, DB conflict and publish ambiguity.

Recommended:
- Hypothesis for property-based invariant tests where beneficial.
- reusable in-memory/fake ports rather than excessive mocking.
- sanitized golden fixtures for Scene/browser/media contract regression tests.

## Architecture Enforcement
Recommended baseline tooling:
- import-linter or equivalent custom dependency tests;
- CI checks preventing domain/engine imports from infrastructure/UI frameworks.

Mandatory architectural assertions:
- domain/engines do not import FastAPI, PySide6, SQLAlchemy, browser APIs or Android libraries;
- concrete adapters implement ports;
- UI does not import persistence implementations;
- composition root is the only place wiring concrete implementations.

## Quality / Tooling
- Ruff for linting/formatting baseline.
- Pyright or mypy for static typing; select one as required CI tool during foundation slice.
- pre-commit recommended for local developer feedback.

## Packaging
- PyInstaller candidate for Windows portable distribution.
- Core package should remain independently testable before packaging.
- Bundled external binaries only where licensing permits.
- Runtime data/config/logs must live outside immutable packaged application resources.

## Observability
- Python structured logging with JSON-capable formatter.
- Correlation IDs: request_id, job_id, worker_id, device_id where relevant.
- structured domain/application events for major state transitions.
- Metrics/exporter interface remains pluggable; Prometheus/OpenTelemetry may be added for Farm Mode without changing domain contracts.

## Technology Lock Policy
A technology is considered:
- BASELINE: recommended/required for the current implementation handoff.
- CANDIDATE: benchmark/validation required.
- PLUGGABLE: must be hidden behind an interface/adapter.

Current core baseline:
- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- SQLite/PostgreSQL tiering
- pytest
- Ruff
- engine/application/ports/adapters architecture

Current optional presentation baseline:
- PySide6/Qt 6

Current adapter candidates:
- ADB
- uiautomator2/Appium
- scrcpy/STF-style stream
- perceptual fingerprint implementation

No candidate tool may become business architecture merely because it is convenient during the first implementation.