# Program 1 Development Pipeline

Date: 2026-09-08
Card: P1-DEV — Standard development and verification pipeline
Scope: Program 1/browser plugin; existing shared repository regression gates retained.

## Development flow

`AGENTS / handoff / current CI -> one card -> Definition of Ready -> contract -> implementation + regression tests -> narrow verification -> full gates -> review -> evidence / Kanban / CAPA -> commit / push / CI -> controlled acceptance`

The governing development cycle still applies. The runner automates verification; it does not replace design review, operator acceptance, or live evidence promotion.

## Commands

Invoke the approved existing virtual environment explicitly, from the repository root:

```powershell
.\.venv\Scripts\python.exe tools/program1_verify.py --list --profile full
.\.venv\Scripts\python.exe tools/program1_verify.py --profile fast
.\.venv\Scripts\python.exe tools/program1_verify.py --stage core
.\.venv\Scripts\python.exe tools/program1_verify.py --profile full
```

The runner resolves paths from its own file independently of shell cwd. It never creates, installs, or switches Python environments. CI uses setup-python. Missing Node/dependencies/browsers fail with a saved diagnostic; dependency installation remains an explicit bootstrap action.

`config/quality-gates.toml` is the shared local/CI command registry:

| Stage | Evidence |
|---|---|
| static | Ruff and existing Program 1/2/3 conformance controls |
| core | Unit/component/contract suites with original 95% branch coverage scopes |
| sqlite | SQLite, migrations, restart/concurrency with original 95% coverage scopes |
| stress | Existing stress suite |
| extension | Vite/daisyUI build and Node extension tests |
| browser | Deterministic Chromium MV3 persistent-profile restart/reconcile laboratory |

`fast` runs static and extension only. Run narrow tests for the affected behavior first. Only all stages passing in `full` is full local verification. Shared regression coverage does not authorize Program 2/3 feature work.

CI retains five jobs, dependency setup and Xvfb. Each job uploads `runtime/verification/` using `if: always()` so failures retain evidence.

## Evidence and recovery

Each invocation creates a unique ignored `runtime/verification/<UTC-id>/` with step logs and atomic `report.json`: HEAD, branch, dirty-tree status, Python/tool versions, arguments, durations and exit codes.

Reports begin RUNNING. Failed/timeout steps stop subsequent stages, which remain NOT_RUN. Partial success never sets `full_verification`. Interrupted/crashed runs are not success. Fix the cause, rerun the narrow gate, then run full verification on the final tree. Do not combine unrelated scoped reports into a full PASS.

Local verification is sequential to avoid coverage-file contention; CI isolates parallel jobs. Timeouts are development budgets, not Shopee pacing policy.

## Live acceptance boundary

The browser stage uses Chromium/local fixtures with mock job lifecycle. The P1-C-ACK follow-up adds real SQLite ingestion/receipt replay and panel receipt restoration to this laboratory. It is not visible Brave acceptance or Shopee profile promotion. Reports explicitly record `live_brave_shopee_acceptance: NOT_RUN`.

For runtime/product slices, separately test in visible Brave using the existing user profile. Verify saved observations/receipts/checkpoints and distinguish new product identities, new observations, exact duplicate observations and delivered batches. Never infer these from UI counters. Pagination/DOM changes require real sanitized evidence and fail closed on access-control challenges.

## Definition of Ready and acceptance

- Foundation rationale: repeatable verification and attributable failures without local/CI command drift.
- Owner: development tooling; business/job authority unchanged.
- Input: versioned registry and explicit runtime. Output: logs/report and exit status.
- Failure contract: nonzero exit, unavailable executable, timeout or interruption cannot produce PASS.
- Persistence/config: unique report directories, atomic replacement, typed argument arrays/TOML; no DB migration or machine-specific source paths.
- Tests: actual subprocess failure/timeout, cwd/interpreter reuse, partial/full distinction and persisted evidence.
- Review: no unresolved CRITICAL/HIGH design issue; no platform assumptions introduced.
- Rollback: restore prior CI command invocations; evidence does not affect business state.
- Next slice: P1-C duplicate-observation ACK accounting regression, followed by durable-result presentation. Preserve changed-payload conflict rejection.
