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

