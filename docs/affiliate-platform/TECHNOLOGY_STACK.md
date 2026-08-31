# Technology Stack Baseline

Status: DEVELOPMENT HANDOFF BASELINE

## Principles
- Portable-first, scale-ready.
- API-as-core.
- Component-based and pluggable.
- Database engine must be replaceable behind repository/storage interfaces.
- Tool choices are replaceable adapters unless explicitly promoted to domain policy.

## Back Office / Shared Core
- Python 3.12+ target runtime.
- FastAPI for versioned REST API and WebSocket telemetry endpoints.
- Pydantic v2 for API DTOs, configuration and contract validation.
- Uvicorn as local ASGI runtime; production server topology remains deployment-specific.
- PySide6 / Qt 6 for portable desktop Back Office UI.

## Persistence
- SQLAlchemy 2.x ORM/Core.
- Repository Pattern between application/domain services and persistence.
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

## Android / Step 3
- ADB as initial DeviceTransportAdapter candidate.
- uiautomator2 family as primary semantic UI automation candidate.
- Appium + UiAutomator2 as optional compatible/alternative adapter when its ecosystem is advantageous.
- scrcpy as initial ScreenStreamAdapter / operator-control candidate.
- STF/DeviceFarmer-style or other streaming/control implementations must be benchmarked before high-scale production lock.

## Media / Video Identity
- FFmpeg / ffprobe for deterministic media metadata/extraction operations.
- SHA-256 for exact file identity.
- Perceptual video/audio fingerprint libraries to be selected by benchmark; algorithm and thresholds are not frozen yet.

## Testing
- pytest.
- pytest-asyncio where async boundaries require it.
- HTTP/API contract tests against FastAPI application.
- DB compatibility suite for SQLite and PostgreSQL.
- failure-injection tests for job leasing, ACK loss, worker crash, DB conflict and publish ambiguity.

## Quality / Tooling
- Ruff for linting/formatting baseline.
- mypy or Pyright candidate for static typing; final CI choice may be decided during foundation spike.
- pre-commit optional but recommended.

## Packaging
- PyInstaller candidate for Windows portable distribution.
- Bundled external binaries only where licensing permits.
- Runtime data/config/logs must live outside immutable packaged application resources.

## Observability
- Python structured logging (JSON-capable format).
- Correlation IDs: request_id, job_id, worker_id, device_id where relevant.
- Metrics/exporter interface remains pluggable; Prometheus/OpenTelemetry may be added for Farm Mode without changing domain contracts.

## Technology Lock Policy
A technology is considered:
- BASELINE: recommended for development.
- CANDIDATE: benchmark/validation required.
- PLUGGABLE: must be hidden behind an interface/adapter.

Current baseline: Python, FastAPI, Pydantic, SQLAlchemy, Alembic, SQLite/PostgreSQL tiering, PySide6.
Current adapter candidates: ADB, uiautomator2/Appium, scrcpy/STF-style stream.
