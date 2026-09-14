# P1-UI-JOBS verification — 2026-09-14

Implemented bounded, Program1-only discovery job listing and read-only daisyUI monitor. Tests cover filtering before count/page, deterministic order, bounds, no lease-token exposure, Thai unknown/recovery mapping and read failure without mutations/retries. Existing job commands unchanged.

Contract tests: 14 passed. Full pipeline report: runtime/verification/20260914T070125Z-581babbb/report.json. Static/core/SQLite/stress/extension PASS; browser FAILED with local Chromium spawn UNKNOWN before worker registration. This is not a full local PASS. Current implementation CI pending.

Visible Brave existing Personal profile, tab 651739447: refreshed http://127.0.0.1:8001/program1/ui/backoffice.html. Monitor displays 0 discovery jobs and an explicit empty explanation; existing products still display 751 keys. The monitor does not synthesize jobs from manual captures. Populated job table and narrow layout remain browser acceptance gaps; API and presentation tests cover their underlying contracts. Runtime restarted with approved .venv, no schema change or user-job mutation.

Design finding: cooperative operator pause remains HIGH/open, CAPA PL-2026-015. Do not enable controls or mark full Program1 complete until resolved. Next required implementation: durable pause request and worker safe-unit acknowledgement, then creation/control UX. Live images/profile promotion and downstream outcome validation remain evidence-gated.
