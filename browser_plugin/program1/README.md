# Program 1 Browser Plugin

Status: laboratory / evidence-gated implementation.
Current extension version: `0.1.26`.

This Manifest V3 extension is the Product Discovery Worker for Program 1. It intentionally does **not** contain production Shopee selectors yet. Real collection profiles remain a validation gate in the governing documents.

Current implemented capabilities:
- Vue 3 side panel (Vue Router views + Pinia stores) styled with Tailwind CSS + daisyUI, built with Vite into `dist/`;
- operator process panel with worker state, current step, captured/sent/queued/outbox counters and latest error;
- backend URL and worker ID stored in extension local storage;
- target page URL shortcut for opening a supported Shopee page from the worker UI;
- local durable outbox;
- durable quarantine for clearly permanent payload failures so a poison message cannot block later valid batches indefinitely;
- ACK-style removal only after Back Office confirms `batch_id`, `received_count` and `accepted_count`;
- serialized outbox flushing to avoid concurrent read/mutate/write drains;
- conservative failure classification: permanent payload errors quarantine, while auth/config, transient/network and ACK ambiguity stop fail-closed without deleting the message;
- queue/flush status that reports captured observations, queued observations, delivered batches, accepted observations, remaining and delivery error counts;
- side-panel auto-run mode with a dual-thumb from–to random delay range slider (`0-600` s), a live next-cycle countdown ticker, single in-flight cycle guard, and timer cleanup when stopped or when the panel closes;
- fixture-page capture adapter for deterministic development/testing;
- conservative Shopee current-page capture profile using product identity found in visible product URLs;
- explicit PAGE_UNSUPPORTED when no supported profile or product identity is found;
- explicit PAGE_BLOCKED_BY_ANTIBOT when Shopee serves a verification/anti-bot page — such pages never count as a successful empty harvest;
- Back Office worker registration (`POST /api/v1/workers/register`) as worker type `DISCOVERY_BROWSER_WORKER` using a persistent `installation_id`, the extension manifest version and advertised collector capabilities;
- background worker heartbeat (`POST /api/v1/workers/{worker_id}/heartbeat`) scheduled through `chrome.alarms` while the browser runs, reporting `ONLINE_IDLE`, or `DEGRADED` when the local outbox still retains undelivered work; alarm scheduling tolerates browsers where `chrome.alarms.create` returns no promise (0.1.11);
- automatic register + heartbeat when the side panel opens or after settings are saved;
- side panel registry status line showing the registered worker id or the last registration error; registration/heartbeat transport failures remain visible as process errors.

Implemented collection router/profile registry:
- `collector:profile-router-v1` deterministically selects one compatible profile;
- `fixture-profile-v1` for deterministic fixture markup;
- `shopee-search-lab-v1`;
- `shopee-category-lab-v1`;
- `shopee-shop-lab-v1`;
- `shopee-pdp-lab-v1`.

All Shopee profiles remain `LAB_VALIDATED`; their presence in the registry does not mean production approval. The router fails closed on unsupported, ambiguous or evidence-stage-incompatible profile selection.

The Shopee laboratory profiles intentionally extract only candidate product facts that are visible and identity-backed:
- `(platform, shop_id, item_id)` from URL shapes such as `-i.<shop_id>.<item_id>`, `/product/<shop_id>/<item_id>` or `shopid`/`itemid` query parameters;
- product name from nearby visible card text, or PDP-first title sources such as `h1` on product detail pages;
- product URL without query parameters;
- `source_worker_id` from Side Panel settings when configured;
- `price_current = null` and `sold_signal = null` until saved fixtures prove stable field boundaries.

## UI stack and build

The side panel is a Vue 3 SPA (`src/ui/`) styled with Tailwind CSS + daisyUI and routed with
Vue Router (Status / Settings / Activity views) with Pinia stores for worker process and
settings state. Vite compiles it to static assets under `dist/`, which `manifest.json`
references via `side_panel.default_path = dist/sidepanel.html`.

Frame rules that keep the extension testable and safe:
- `src/background.js` (service worker) and `src/content.js` (page context) stay **vanilla and
  un-bundled** — only the panel UI is a Vue app;
- all decision logic the panel needs lives in framework-free modules under `src/ui/lib/*.mjs`
  (URL/pagination rules, delay-range math, process/registry view mapping) plus a
  chrome-injected `workerBridge` factory, so `node:test` covers them without a DOM or browser;
- panel element ids used by the Playwright tools (`#registryStatus`, `#state`, `#step`,
  `#startAuto`, `#status`, …) are preserved across the views.

Build and test:

```powershell
cd browser_plugin\program1
npm ci          # first time
npm run build   # emit dist/ (gitignored)
npm test        # node --test: content parser, background transport, panel logic
```

After changing UI sources, rebuild and reload the extension at `chrome://extensions`. There is
no dev server; `npm run watch` re-emits `dist/` on change if you prefer continuous builds.

Delivery result semantics:
- `ok: true` means the current queue flush reached the Back Office and acknowledged the queued batch;
- `ok: false` with `queued: true` means the capture was durably queued locally but has not been delivered yet;
- `remaining_count` reports messages still retained in the local outbox.
- `Capture Current Page` requests permission for the active page origin before injecting the collector, for example `https://shopee.co.th/*`.
- `Start Auto Run` opens or reuses the target tab and repeats the same capture/delivery cycle after a randomized delay drawn from the operator's from–to range (`0-600` s); `Stop Auto Run` clears the timer and releases side-panel runtime work.
- listing captures report pagination context (current page, total, next link read from `.shopee-page-controller`); auto-run advances through the real next-page link and finishes cleanly on the last page instead of advancing past the end (0.1.13); failure and status lines include the page URL.
- mid-run `PAGE_UNSUPPORTED` is diagnosed, not just reported: the collector returns a `page_context` probe (listing shell present?, hydrated item roots, page title) so an empty throttled page is distinguishable from a genuinely unsupported page; auto-run retries a rendered listing shell twice (5 s then 12 s) before failing closed, and the stop reason carries the failing page URL (0.1.15).
- fixture pages (`data-program1-fixture-product`) may embed a real `.shopee-page-controller`; the fixture capture then reports pagination context, which lets the **pagination-aware auto-run be exercised end-to-end against deterministic non-Shopee pages** — including the clean last-page finish (0.1.16).
- the fixture listing E2E is scripted in `tools/program1_fixture_autorun_check.py`: it serves a two-page fixture listing + a mock Back Office on `127.0.0.1`, drives the real extension, and asserts the auto-run walks page 1 → 2 via the controller next link and finishes with `Auto run finished: reached the last page (page 2 of 2)` without requesting a page 3 (0.1.17).
- worker registration is verified end-to-end with `tools/program1_registry_e2e_check.py` (opens the real side panel and expects `Registry: registered (...)`); Shopee evidence pages can be captured with `tools/program1_capture_search_evidence.py`, which now emits structurally sanitized HTML plus a SHA-256 evidence manifest governed by ADR-047.
- host permissions are intentionally limited to Shopee and local Back Office URLs until a remote deployment profile is approved; the local Back Office (`http://127.0.0.1/*`, `http://localhost/*`) is a **required** host permission (silent grant — it is the worker's own control plane), while `https://shopee.co.th/*` stays optional so touching real Shopee pages always needs explicit operator consent (0.1.17).

Playwright persistent-profile test mode:

```powershell
D:\dev\MTAffiliatePlatform\.venv\Scripts\python.exe tools\program1_open_playwright_browser.py --hold
```

This opens a headed Playwright-controlled browser, loads this extension and stores browser session state under:

```text
D:\dev\MTAffiliatePlatform\.browser-profiles\shopee-program1
```

The profile directory is ignored by git. Do not export cookies into text files; use this profile for repeatable logged-in testing.

Harness smoke check:

```powershell
D:\dev\MTAffiliatePlatform\.venv\Scripts\python.exe tools\program1_open_playwright_browser.py --url about:blank --profile-dir .browser-profiles\program1-smoke --smoke-close-after 1 --require-extension
```

This check fails if the extension service worker is not detected.

Direct Brave visible test mode:

```powershell
D:\dev\MTAffiliatePlatform\.venv\Scripts\python.exe tools\program1_open_brave_direct.py --open-worker-tab
```

This starts Brave directly with a dedicated persistent profile and loads the Program 1 extension without Playwright. It exposes a local DevTools endpoint for compact structured inspection at `http://127.0.0.1:9223`.

Native Side Panel behavior:
- `manifest.json` declares `side_panel.default_path = dist/sidepanel.html` (built from `src/ui/`);
- background startup calls `chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true })`;
- the extension action intentionally has no `default_popup`, so clicking the toolbar icon opens the browser native side panel instead of a popup.

Operator process states:
- `CONFIG_REQUIRED` when Backend URL is not configured;
- `READY` / `IDLE` when the worker can capture;
- `COLLECTING` while injecting the collector and reading visible facts;
- `QUEUED` after a batch is built locally;
- `DELIVERED` after Back Office ACK;
- `DELIVERY_BLOCKED` when the local outbox retains undelivered work;
- `PAGE_UNSUPPORTED` when the active page has no supported identity-backed profile;
- `PAGE_BLOCKED_BY_ANTIBOT` when the active page is a Shopee verification/anti-bot page.

Observed supported lab surfaces after human CAPTCHA completion:
- search results: `li.shopee-search-item-result__item[data-sqe="item"]`;
- category listings: same root as search results;
- shop listings: identity-backed product anchors such as `a.contents[href*="-i."]`;
- product detail pages: current product identity from the page URL, title from `h1`, shop/category provenance from visible PDP sections.

Unsupported/CAPTCHA/schema-drift pages must fail closed and must not be reported as a successful empty harvest.

Shared Job integration (0.1.23):
- the MV3 background service worker now owns durable active-job lifecycle state;
- workers can lease the next compatible Program 1 job, fetch its durable strategy/work package, start it, renew the lease, checkpoint acknowledged observation batches, reconcile after service-worker restart, and verify/complete bounded work;
- an existing durable active job blocks a second lease;
- restart reconciliation fails closed when authoritative Back Office state is no longer an active lease;
- Side Panel remains an operator shell; remaining work is to move the full multi-page auto-run trigger/scheduling loop behind this background-owned job lifecycle and prove kill/restart recovery in a real Chromium-family browser.

Background execution ownership (0.1.24):
- Start/Stop Auto Run is now a Side Panel command to the MV3 background runtime rather than a panel-owned timer loop;
- the background runtime executes one bounded cycle per alarm wake-up and persists phase/run state before yielding;
- DiscoveryPlan may carry bounded `collection_targets`, so executable work can survive UI closure and browser/service-worker restart without relying on panel-only target state;
- page-load waits, bounded PAGE_UNSUPPORTED retries and next-cycle delays are alarm-driven rather than long-lived Side Panel timers;
- successful durable observation ACKs become Shared Job checkpoints;
- last-page detection verifies/completes the Shared Job and terminates the background run;
- delivery blocks, permission gaps and ambiguous pagination fail closed.

Next gated work:
- fresh independent Search-surface evidence under ADR-047;
- saved sanitized real-page fixtures for observed search/category/shop/product-detail surfaces;
- promotion of individual Shopee profiles only after their evidence gates pass;
- downstream attribution/learning only when real outcome data is sufficient.

Delivery reliability hardening (0.1.25):
- clearly permanent payload errors (`400/409/413/415/422`) are moved atomically from the active outbox to a durable quarantine record and later valid messages may continue;
- `401/403/404/405/410`, `408/425/429`, `5xx`, network/unknown errors and ACK mismatches never remove the current message;
- process status exposes `outbox_quarantine_count`; heartbeat remains `DEGRADED` while either active outbox or quarantine needs attention;
- Shared Job checkpoints are written only when the **current queued batch** receives an authoritative matching ACK;
- delivery error normalization is structural (`error.message`) rather than `instanceof Error`, so cross-realm/VM/extension error objects preserve canonical error codes.

Controlled evidence capture (2026-09-05):
- verification/anti-bot pages fail closed immediately by default;
- `--allow-human-verification-wait` must be supplied explicitly to wait while a human completes an ordinary platform verification step;
- persisted HTML removes scripts/styles/iframes, input values, media URLs and secret-like attributes before writing;
- evidence URLs retain only route plus approved evidence query keys;
- each capture writes an evidence manifest with classification, blocked state, promotion decision, browser/session category, code version and SHA-256;
- a successful capture is still `HOLD`; profile promotion requires repeated independent live evidence under `CONTROLLED_PRODUCTION_EVIDENCE_VALIDATION_STANDARD.md`.

Collection Router + Versioned Profile Registry (0.1.26):
- `content.js` is now only the message bridge/bootstrap; parsing responsibilities live under `src/collectors/`;
- background injection order is core -> fixture/Shopee helpers -> search/category/shop/PDP profiles -> router -> bridge;
- each profile declares profile id/version, surface, evidence stage, required/optional indicators, extracted/unknown fields, compatibility scope, evidence refs and failure modes;
- the router enforces deterministic single-profile selection and a configurable minimum evidence stage;
- equal-priority multiple matches fail as `PROFILE_AMBIGUOUS`; unsupported pages do not fall back to a generic guessed parser;
- worker registration advertises the router and individual surface-profile capabilities;
- search/category/shop/PDP remain `LAB_VALIDATED` pending fresh independent evidence under ADR-047.

Real Chromium restart/reconcile CI (2026-09-05):
- dedicated `program1-browser-e2e` GitHub Actions job uses Playwright Chromium under Xvfb;
- no Shopee, login, Side Panel click or external network target is required for runtime correctness;
- page 1 is collected, ACKed and checkpointed before the persistent Chromium context is closed;
- reopening the same profile proves `onStartup` registration + Shared Job reconcile/renew and recovery of the same active job/run state;
- a stale tab id is safely replaced, page 2 is collected and ACKed, and the same job reaches verify/complete;
- the harness asserts exactly two observation batches, two checkpoints, one lease lineage, cleared active-job state, terminal run state and empty outbox;
- Chromium alarm delivery timing is not used as the sole correctness oracle after restart; startup reconciliation is proven first and the same bounded background-cycle command used by alarm wakes is then driven deterministically in CI.
