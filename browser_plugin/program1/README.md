# Program 1 Browser Plugin

Status: laboratory / evidence-gated implementation.
Current extension version: `0.1.23`.

This Manifest V3 extension is the Product Discovery Worker for Program 1. It intentionally does **not** contain production Shopee selectors yet. Real collection profiles remain a validation gate in the governing documents.

Current implemented capabilities:
- Vue 3 side panel (Vue Router views + Pinia stores) styled with Tailwind CSS + daisyUI, built with Vite into `dist/`;
- operator process panel with worker state, current step, captured/sent/queued/outbox counters and latest error;
- backend URL and worker ID stored in extension local storage;
- target page URL shortcut for opening a supported Shopee page from the worker UI;
- local durable outbox;
- ACK-style removal only after Back Office confirms `batch_id`, `received_count` and `accepted_count`;
- serialized outbox flushing to avoid concurrent read/mutate/write drains;
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

Implemented extractor profiles:
- `fixture-profile-v1` for deterministic fixture markup;
- `shopee-current-page-lab-v2` for logged-in/manual current-page capture where product links expose a candidate Shopee identity.

The Shopee current-page profile intentionally extracts only candidate product facts that are visible and identity-backed:
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
- worker registration is verified end-to-end with `tools/program1_registry_e2e_check.py` (opens the real side panel and expects `Registry: registered (...)`); Shopee evidence pages can be captured with `tools/program1_capture_search_evidence.py`.
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

Next gated work:
- real-browser MV3 kill/restart/reconcile E2E while Side Panel is closed;
- background-owned multi-page execution orchestration using DiscoveryPlan scope;
- saved sanitized real-page fixtures for observed search/category/shop/product-detail surfaces;
- versioned Shopee collection profiles after observation/validation.
