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

## Fourth slice — Vue side-panel migration (extension 0.1.14)

The side panel UI moved from a single vanilla-JS page (`src/sidepanel.html` + `src/sidepanel.js`, ~800 lines of imperative DOM code) to a **Vue 3 SPA** built with Vite and styled with Tailwind CSS + daisyUI, using Vue Router and Pinia, per operator direction ("world-class UI/UX; use vuejs tailwindcss daisyUI vuerouter pinia"). Content/background contexts stay framework-free by design.

What changed:
- new toolchain under `browser_plugin/program1/`: `package.json`, `vite.config.mjs`, Vue app under `src/ui/` (`sidepanel.html` entry, `main.js`, `App.vue`, router with Status/Settings/Activity views, Pinia stores for settings and the worker process machine), output `dist/` (gitignored) referenced by `side_panel.default_path`; manifest bumped to `0.1.14`;
- all panel decision logic moved into framework-free modules under `src/ui/lib/*.mjs` (URL/pagination rules, delay-range math, process/registry view mapping) plus a chrome-injected `workerBridge` factory — the old imperative file is deleted;
- every automation-facing element id (`#registryStatus`, `#state`, `#step`, `#startAuto`, `#status`, metric/input ids) is preserved across the routed views so the Playwright tools keep working;
- the Playwright registry E2E tool was route-aware (Settings for fields, Status for process), and the paginated auto-run live driver now drives the routed panel (it still fails closed at Shopee's network-level traffic gate — see evidence doc 2026-09-04 entry; the guest-context probe confirmed `is_logged_in=false` blocking on `/verify/traffic/error`, i.e. the suspicion window is device/network-level, and the 0.1.13 anti-bot classification was validated against the real block page).

Verification evidence:
- `npm run build` clean (47 modules; ~46 kB gzip JS, ~10 kB gzip CSS incl. daisyUI);
- Node suites `59 passed` (content parser + background transport suites unchanged; side-panel suite ported to `.mjs` against the lib modules + fake-chrome bridge);
- real-browser E2E against the running Back Office (fresh profile): Vue panel booted with **zero console errors**, registered `panel-vue-e2e`, backend row `ONLINE_IDLE`, `version_no 2`, `stale: false`;
- route screenshots saved under `.browser-profiles/captures/2026-09-04/ui-vue/` (gitignored).

Open items unchanged (see third slice) — plus a new one: the extension build (`npm ci && npm run build`) is now a prerequisite before loading/reloading the extension, documented in the plugin README; the CI extension job was added to `.github/workflows/ci.yml`.

## Fifth slice — mid-listing PAGE_UNSUPPORTED diagnostics (extension 0.1.15)

A real run at ~14:26–14:31 (0.1.13, logged-in profile `w00001`, during the Shopee suspicion window) delivered 40 observations across listing pages 1–5 via the real next links, then stopped with `Auto run stopped: PAGE_UNSUPPORTED` mid-listing (page 5 of 12): the next page load rendered no product anchors and was not recognized by the anti-bot classifier, and the old stop reason did not say which page or why.

Changes:
- `content.js` now returns a `page_context` probe with every failure result: `listing_shell_present`, hydrated `item_roots` count and the page title — so an empty throttled page is distinguishable from a genuinely unsupported page (evidence-based; no speculative new block classification);
- auto-run treats a rendered listing shell with zero items as a transient state and retries it twice (5 s then 12 s) before failing closed — bounded, never an unbounded wait, and still never a fake empty harvest;
- the auto-run stop reason now includes the failing page URL (`Auto run stopped: <error> (<url>)`), and the Vue panel's last-payload pre keeps the full result incl. `page_context`.

Verification: node suites `61 passed` (content parser +2: shell-context on empty listing, no-shell on unrelated pages), Vite build clean, manifest/package bumped to `0.1.15`. Root-cause context unchanged: this is the device/network-level Shopee traffic gate documented in the evidence file — the fix makes the failure say exactly that instead of a bare code.

## Sixth slice — deterministic last-page-finish E2E and host-permission refinement (extension 0.1.16–0.1.17)

Goal: re-verify the pagination-aware auto-run's clean last-page finish end-to-end in a real Brave run without touching Shopee (which remains network-blocked).

Changes:
- the fixture adapter (`content.js`) now reads and returns pagination context when a fixture page embeds a real `.shopee-page-controller` — fixture pages can therefore drive the genuine advance + finish logic deterministically (0.1.16);
- `tools/program1_fixture_autorun_check.py`: threaded local server serving a two-page fixture listing AND a mock Back Office (register/heartbeat/observation ACK mirroring the real API shape: `batch_id` + `received_count` + `accepted_count`); drives the real extension 0.1.17 in Brave and asserts the auto-run walks page 1 → 2 via the controller next link and finishes cleanly (0.1.16→0.1.17);
- the local Back Office moved from optional to **required** `host_permissions` (`http://127.0.0.1/*`, `http://localhost/*`) while `https://shopee.co.th/*` stays optional: loopback is the worker's own control plane and should not need per-profile interactive grants; touching real Shopee pages still always requires explicit operator consent (0.1.17). This also removed the interactive Allow step from every Playwright tool run.

Verification evidence (extension 0.1.17, local `.venv`):
- `npm test` `63 passed` (content parser +2 fixture-pagination tests; background transport + panel lib suites unchanged);
- fixture E2E in headed Brave with a fresh profile: transcript `Auto run cycle 1 -> Captured, queued and delivered to Back Office -> Auto run finished: reached the last page (page 2 of 2)`; mock log showed exactly 2 observation batches (6 accepted) covering pages [0, 1], zero requests past the last page; final capture payload on page 2 reported `has_next: false, next_url: null`; metrics cycle 2 / session accepted 6 / outbox 0; zero console or page errors; screenshots + `report.json` under `.browser-profiles/captures/2026-09-04/fixture-autorun/`.

Open items unchanged (see fifth slice); live-Shopee last-page confirmation remains pending the traffic gate, but the exact finish path is now locked by a deterministic browser E2E.
