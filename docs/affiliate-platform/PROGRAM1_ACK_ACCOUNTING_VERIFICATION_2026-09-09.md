# P1-C-ACK verification — 2026-09-09

Contract: `PROGRAM1_ACK_ACCOUNTING_CONTRACT.md`. Status: IN VERIFY; live acceptance remains open.

## Implemented

Back Office exposes additive v2 observation receipt counts from its atomic batch result. Exact duplicates are acknowledged without inventing new-product counts. SQLite batch ingestion now preserves source_job_id. Changed payloads remain conflicts; historical missing provenance is not guessed or repaired.

Worker validates version/counts, checkpoints only its current batch receipt, and serializes outbox writes. A receipt is persisted with removal in one storage update and scoped to the backend URL. The daisyUI panel restores this evidence and explains observation versus product counts. Extension version: 0.1.27. No Shopee selectors, pacing rules or Program 2/3 business behavior changed.

## Local evidence

Runtime: D:\dev\MTAffiliatePlatform\.venv\Scripts\python.exe, Python 3.12.10.
Full pipeline report: runtime/verification/20260909T035430Z-050ff0fa/report.json (ignored runtime artifact).

- Static/conformance: PASS.
- Core: 281 passed; branch coverage 95.01% against unchanged 95% gate.
- SQLite: 58 passed, 1 skipped; coverage 96.24% against unchanged 95% gate.
- Stress: 1 passed.
- Extension: build PASS; 104 tests passed.
- Browser: FAILED before browser startup, Playwright spawn UNKNOWN. Full pipeline is not reported green.

SQLite regressions dispose/recompose the engine, verify mixed and duplicate-only receipts, replay and conflict behavior, and query actual rows: two observations and three receipts, with source_job_id retained. A real HTTP/SQLite harness regression also proves one observation and two receipts across restart/replay. Worker tests cover malformed/legacy ACKs, backlog isolation, storage failure, concurrent enqueue/remove/quarantine, and receipt restoration.

The Chromium E2E now uses real SQLite ingestion alongside mock job lifecycle and fixture DOM, checking duplicate replay plus restored receipt UI. The Chromium scenario passed in CI run 34309195647; it does not establish Shopee or Brave acceptance.

## Remaining evidence

- Code commit 9ad41141fd9e0d678474c416612d75c3774f50c9: all five CI jobs PASS, including Chromium receipt/restart scenario: https://github.com/idev006/MTAffiliatePlatform/actions/runs/34309195647. Draft PR #43 is stacked on pipeline PR #42. Baseline 6144d90 CI run 34192288649 passed.
- Visible Brave: existing Default profile and installed extension page opened. Computer Use stopped because it could not establish the browser URL confidently; no further UI actions were attempted. Receipt UI acceptance on Brave is unverified.
- Live Shopee pagination/DOM: unchanged and not newly verified by this slice.
- Actual new-product totals require product identity evidence; observation ACK counts cannot establish them.

Kanban, contract, UML, pipeline runbook and CAPA PL-2026-013 updated. No database migration required.


## 2026-09-09 manual capture bootstrap defect

Live Brave screenshot showed Receiving end does not exist after Capture Current Page. Source inspection found the manual bridge injected content.js alone although its documented bootstrap requires collectors/router first. Align the manual injection order with the existing background controller; no selector or business-policy change. Regression executes the actual injected scripts in a fresh VM and verifies one receiver after first injection and reinjection. Live acceptance requires rebuilding/reloading the extension and repeating Capture; do not infer success from registration.

## 2026-09-09 narrow-panel telemetry UX

User screenshot showed overlapping metric labels. Root cause: daisyUI stats column auto-flow combined with grid-cols-2, creating compressed implicit columns. Replaced with a bounded overflow-x:auto region, readable 9rem minimum columns, keyboard focus outline and scroll hint. Receipt metrics use the same layout; worker registration badge wraps instead of clipping. UX governing document updated before implementation. Extension build and suites PASS: runtime/verification/20260909T050226Z-c4ee928f/report.json. Visual acceptance in Brave remains pending extension/panel reload; browser tools previously blocked extension URL access.

## Live Brave single-page evidence — 2026-09-09

User-operated Capture on https://shopee.co.th/search?keyword=ssd with worker brave-program1-01 produced receipt 7c56fced-13e9-4408-be21-d49be053b478. Read-only SQLite verification found accepted_count=20, received_count=20 and 20 observations for the worker. User screenshot confirms receipt and horizontal telemetry scrolling. This closes single-page manual ingestion/display evidence only; it does not establish live pagination, restart/recovery, duplicate replay, image extraction or production profile promotion.
