# Program 1 Implementation Log — 2026-08-31

Status: IMPLEMENTATION STARTED
Governance: Document-Driven Project / Project Must Follow Documents / Agile Kanban

## Scope of first implementation slice

Backend:
- Python package skeleton;
- TOML typed configuration;
- relative-first PathManager;
- ProductObservation domain model;
- ProductRepository port + InMemory adapter;
- deterministic Product Intelligence scoring framework;
- Program1 application service;
- FastAPI observation ingestion + shortlist endpoints;
- unit/component tests.

Browser Plugin:
- Manifest V3 skeleton;
- isolated Side Panel;
- local durable outbox;
- configurable backend URL/worker ID;
- fixture-only content adapter;
- batch submission to Backend.

## Intentional non-implementation / HOLD

- No production Shopee DOM selectors are hard-coded.
- Exact Product Scoring Model v1 is not claimed final.
- Canonical Shopee identity remains validation-gated.
- Worker registration/heartbeat (FND-007) is implemented in the second slice below; job leasing/pause/resume remains next slice.
- SQLAlchemy persistent repository is next foundation slice.

## Architecture conformance

The first slice follows:
- engine-first/headless-first;
- UI as shell;
- ports/adapters;
- fake/in-memory first;
- relative-first paths;
- TOML configuration;
- no developer-machine absolute paths;
- no unvalidated Shopee selector assumptions.

---

## Second slice — Shared Core Worker Registry + Browser Worker heartbeat

Backend (Shared Core):
- `worker_registry` domain with `WorkerRegistration`, `WorkerRecord`, `WorkerSummary`, the Shared Core health vocabulary and deterministic stale/OFFLINE derivation;
- deterministic `WorkerRegistryService` (register idempotency, DISABLED workers never resurrected by re-registration, worker-side health-state limits);
- `WorkerRegistryRepository` port plus in-memory and SQLAlchemy adapters;
- Alembic migration `0003_shared_core_workers` creating the Shared Core `workers` table;
- shared endpoints `POST /api/v1/workers/register`, `POST /api/v1/workers/{worker_id}/heartbeat` and `GET /api/v1/workers[/{worker_id}]`, wired into every runtime profile with idempotent registration, 409 installation-conflict semantics and derived OFFLINE state.

Browser Worker (Program 1):
- background worker registration on startup and settings save, using a persistent `installation_id`, the extension manifest version and advertised collector capabilities;
- `chrome.alarms` heartbeat while the browser runs, reporting `ONLINE_IDLE`, or `DEGRADED` while the local outbox retains undelivered work;
- side panel registry status line showing the registered worker id or the last registration error;
- extension manifest bumped to `0.1.9`; no collector/parser changes.

Verification evidence (local `.venv`, 2026-08-31 window):
- Ruff PASS over `src tests migrations`;
- Node extension suite `45 passed`;
- core + contract `108 passed` at 96% branch coverage, new registry modules at 100%;
- SQLite integration `33 passed` at 97% branch coverage, including restart durability and concurrency;
- stress suite `1 passed`.

Architecture conformance:
- Shared Core registry per `DATA_MODEL` and `SHARED_CORE_SPEC` FND-007;
- workers report facts/state, Back Office owns status and conflict policy;
- UI stays a shell; durable outbox semantics untouched;
- OFFLINE is derived from heartbeat staleness, never stored as a worker-claimed state.

Intentional non-implementation / HOLD:
- job lease/pause/resume protocol remains the next slice;
- no registry pruning/cleanup endpoint yet (derived state only);
- no new Shopee collection profiles — promotion stays evidence-gated.

---

## Third slice — Registry E2E verification and browser-worker reliability (extension 0.1.11–0.1.13)

Backend verification:
- root-caused the operator-facing `Registry: not registered - HTTP_404`: the running Program 1 API predated the registry routes. Restarted the API on `127.0.0.1:8000` (fresh code, auto-migration 0003), then confirmed `/api/v1/workers`, `/register`, `/{worker_id}` and `/{worker_id}/heartbeat` in the OpenAPI surface.
- exercised the extension's exact payloads over HTTP: register → `version_no 1`; heartbeat → `version_no 2` with `last_seen_at` advanced; a worker claiming `DISABLED` → `422`; rows persisted in the SQLite `workers` table.
- full browser E2E (`tools/program1_registry_e2e_check.py`, headed Brave + real extension): side panel showed `Registry: registered (worker-e2e-browser)` with the backend reporting `ONLINE_IDLE` `version_no 2` and the SQLite row present. The operator's own session was observed heartbeating as `w00001`.

Browser Worker fixes:
- 0.1.11 — `scheduleHeartbeatAlarm` crashed the service worker after a successful register because `chrome.alarms.create` returns `void` in Chromium-family browsers and the code called `.catch()` on it, surfacing as `The message port closed before a response was received`. Now tolerates both void and promise returns; regression test added. Lesson: an earlier `HTTP_404` masked this path because registration never succeeded; E2E runs must cover the success path. Lesson 2: persistent profiles cache extension service workers across `--load-extension` launches — stale SW registrations must be cleared (fresh profile or version bump) when verifying iteratively.
- 0.1.12 — auto-run delay control converted to a dual-thumb from–to range slider (single track, two handles, order enforced so the range never inverts), with fill highlight, live readout and a next-cycle countdown ticker; verified in a live Brave DOM run.
- 0.1.13 — page advancement became pagination-aware: the collector reports pagination context (`current_page`, `total_pages`, `has_next`, real `next_url` from `.shopee-page-controller`), auto-run advances via the controller's next link, finishes cleanly on the last page, and verification/anti-bot pages are classified as `PAGE_BLOCKED_BY_ANTIBOT` (fail closed, never a fake empty harvest) with the failing page URL surfaced. Root cause of the earlier `Auto run stopped: PAGE_UNSUPPORTED`: blind `&page=N+1` advancement walked past the end of listings and hid anti-bot interstitials under one generic error.

Tools added:
- `tools/program1_registry_e2e_check.py` — opens the real side panel in headed Brave, saves settings, and reports the registry status text plus the backend worker row;
- `tools/program1_capture_search_evidence.py` — captures sanitized main-fragment DOM evidence from Shopee pages with the logged-in profile (human solves CAPTCHA; never bypasses anti-abuse controls).

Verification evidence (local `.venv`):
- Ruff PASS over `src tests migrations tools`;
- Node extension suite `51 passed` (registry, transport, parser, pagination and anti-bot classification coverage);
- core + contract `108 passed` at 96.01% branch coverage;
- SQLite integration `33 passed, 1 skipped` at 96.57% branch coverage;
- stress suite `1 passed`;
- worker registry rows for the HTTP simulation and the real-extension E2E confirmed in `data/program1.db`.

Open items unchanged:
- second independent Shopee capture (page 2 + a second keyword) remains deferred pending the anti-bot suspicion window cooling;
- job lease/pause/resume protocol; registry pruning; evidence-gated profile promotion remain next.
