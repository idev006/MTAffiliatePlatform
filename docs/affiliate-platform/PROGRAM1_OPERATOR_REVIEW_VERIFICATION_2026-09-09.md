# P1-UI-READ verification — 2026-09-09

Read-only operator page: http://127.0.0.1:8001/program1/ui/backoffice.html. Shares existing Vue/daisyUI build with a separate entrypoint; no chrome APIs or business mutations. Latest product API uses existing repository/application boundaries. Contract/UML and CURRENT_STATE priority amendment precede implementation.

Live Brave existing profile: page loads stored 751 product keys, first product history reads an actual observation and worker w00001. Visual inspection shows readable columns; horizontal overflow region and keyboard focus are present. Narrow viewport behavior is specified in CSS but not separately measured. Latest UI adds scrolling to selected history. Missing price/rating/image is explicitly unknown, not zero.

Back Office was restarted onto current source after SQLite backup runtime/backups/program1-before-review-20260909T053805Z.db. Migration to image-reference schema preserves 2967 observations, 751 keys and 20 observations belonging to brave-program1-01. These counts are existing database evidence, not newly scraped totals.

Local full report runtime/verification/20260909T053816Z-f4cf47bc/report.json: static PASS; core 297 passed/95.08%; SQLite 60 passed + 1 skipped/96.24%; stress and extension PASS. Local Playwright browser launch fails; full local gate remains FAILED. Extension rebuilt after history scrolling change: runtime/verification/20260909T053918Z-e3f08c74/report.json PASS. Current CI pending.

Remaining: live image extraction, worker/job management UI, real pagination/restart acceptance, product-level search/filter and database-level pagination. This screen is not the complete Program1 application.
