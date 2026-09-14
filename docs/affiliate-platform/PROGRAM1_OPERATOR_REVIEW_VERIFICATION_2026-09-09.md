# P1-UI-READ verification — 2026-09-09

Read-only operator page: http://127.0.0.1:8001/program1/ui/backoffice.html. Shares existing Vue/daisyUI build with a separate entrypoint; no chrome APIs or business mutations. Latest product API uses existing repository/application boundaries. Contract/UML and CURRENT_STATE priority amendment precede implementation.

Live Brave existing profile: page loads stored 751 product keys, first product history reads an actual observation and worker w00001. Visual inspection shows readable columns; horizontal overflow region and keyboard focus are present. Narrow viewport behavior is specified in CSS but not separately measured. Latest UI adds scrolling to selected history. Missing price/rating/image is explicitly unknown, not zero.

Back Office was restarted onto current source after SQLite backup runtime/backups/program1-before-review-20260909T053805Z.db. Migration to image-reference schema preserves 2967 observations, 751 keys and 20 observations belonging to brave-program1-01. These counts are existing database evidence, not newly scraped totals.

Local full report runtime/verification/20260909T053816Z-f4cf47bc/report.json: static PASS; core 297 passed/95.08%; SQLite 60 passed + 1 skipped/96.24%; stress and extension PASS. Local Playwright browser launch fails; full local gate remains FAILED. Extension rebuilt after history scrolling change: runtime/verification/20260909T053918Z-e3f08c74/report.json PASS. Current CI pending.

Remaining: live image extraction, worker/job management UI, real pagination/restart acceptance, product-level search/filter and database-level pagination. This screen is not the complete Program1 application.

Code commit 0be398b0fb4b7c8b6b9bb07952c2e8d5bb33fa49 CI PASS: https://github.com/idev006/MTAffiliatePlatform/actions/runs/34315858473. Draft PR #45. Read-only review slice verified; broader Program1 acceptance remains open.

## P1-UI-FIND — 2026-09-14

Added literal case-insensitive latest-product search by name/platform/shop/item. Applied query persists across paging/refresh and resets offset on explicit search. Unknown result is distinguished from read failure. Contract amendment precedes code; sequence is described in PROGRAM1_OPERATOR_REVIEW_CONTRACT.md.

Tests: API cases cover Thai, case, literal %, latest-only search, bounded query, count-before-page. Core 298 passed/95.09%; SQLite, stress, extension and static pass in runtime/verification/20260914T064632Z-761b7b37/report.json. Local Chromium fails spawn UNKNOWN; full local report remains FAILED. Final extension build/suites pass in runtime/verification/20260914T064804Z-7dfa0ec8/report.json.

Actual Brave existing profile: initial 751 product keys, query 44250274664 returns exactly one stored product, nonmatching query returns zero with explicit query text. Back Office started on port 8001 using approved .venv. No database changes/migration or Shopee collection in this slice.

Code commit 247bbb45ef7c0a6831de137ff428d032244106c7: CI #679 completed successfully, freshly verified on 2026-09-14: https://github.com/idev006/MTAffiliatePlatform/actions/runs/34815019063. This verifies the search implementation; the local browser launch failure remains an explicit environment limitation, not a local full PASS. Search is implemented and CI-verified; Kanban remains IN VERIFY until the documented local gate limitation is resolved. No new RCA/CAPA defect was established during this evidence reconciliation.

Continuation: database-level filtering/pagination remains a scalability gap; worker/job management UI and real Shopee image/pagination acceptance remain separate incomplete slices. Do not infer Program 1 completion from this read-only screen.
