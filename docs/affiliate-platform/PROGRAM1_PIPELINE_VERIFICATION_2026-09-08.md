# Program 1 Pipeline Verification — 2026-09-08

Card: P1-DEV
Status: VERIFIED IN CI / LOCAL BROWSER ENVIRONMENT BLOCKED
Baseline: `23ca5560bcc6e347b995084e39a36dd701eabcd2`, clean `main` before work.
Branch: `codex/program1-development-pipeline`
Baseline CI: https://github.com/idev006/MTAffiliatePlatform/actions/runs/33931865359 (success).

## Verified implementation

Code commit: `3c3e50d102df3932bb9a11495c31262bbd560557`.
PR: https://github.com/idev006/MTAffiliatePlatform/pull/42 (not merged).
CI: https://github.com/idev006/MTAffiliatePlatform/actions/runs/34192148182 — all five jobs PASS, including real Chromium MV3 restart/reconcile. Every job successfully uploaded verification evidence. Subsequent documentation-only changes record this verified code baseline; their own HEAD CI remains separately observable.

## Delivered

- Shared versioned gate registry and explicit-runtime verification command.
- Existing five CI jobs call the registry and upload per-job evidence on success/failure.
- Fail-fast step logs and atomic report; partial verification never appears as full PASS.
- Eight runner tests including failure, timeout, interruption and environment rejection.
- Four baseline lint corrections, with no business-policy change. Program 2/3 edits are limited to shared-gate lint cleanup.
- Program 1 pipeline runbook, Kanban/handoff, plan and CAPA PL-2026-012.

## Local evidence

Interpreter: repository `.venv`, Python 3.12.10; Ruff 0.16.5.

Full attempt: `runtime/verification/20260908T054451Z-c7a3f610/report.json`.

| Gate | Result |
|---|---|
| Ruff/conformance | PASS |
| Core | 280 passed; 95.00% branch coverage in final static/core rerun |
| SQLite | 56 passed, 1 skipped; 96.07% branch coverage |
| Stress | 1 passed |
| Extension | build PASS; 94 tests passed |
| Browser | FAILED: Playwright Chromium `spawn UNKNOWN` before registration/lease/observations |
| Runner narrow final | 8 passed |

The full attempt correctly returns failure and `full_verification: false`. Its browser diagnostic records zero leases and zero observations, so it cannot be mistaken for data-collection success. The SQLite skip remains visible and is not counted as a pass.

Final static/core rerun: `runtime/verification/20260908T054850Z-dc277135/report.json` (scoped PASS). A direct argument comparison against baseline CI confirmed identical core/SQLite selection and coverage scopes.

## Boundaries / next work

No migration, pagination, selector, UI, delay slider or extension version change. Existing daisyUI and dual-thumb delay control remain unaffected.

Visible Brave with the existing user profile and live Shopee acceptance were not run in this tooling slice. Chromium laboratory evidence is separate. Production profile promotion remains gated.

Next runtime card: reproduce P1-C exact duplicate observation/new-batch ACK behavior against persisted receipts, preserve conflict handling, and expose trustworthy result categories. This card is recorded, not implemented by this pipeline slice.
