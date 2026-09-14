# Program 1 job monitor implementation plan

**Goal:** Show durable discovery job status in Back Office; defer controls until cooperative pause conforms to its specification.

**Architecture:** Program1 application filters the JobRepository read model. Vue renders facts from the API. No worker lease secrets appear in list responses.

**Tech Stack:** Python/FastAPI, Vue 3, daisyUI, Node tests, SQLite.

## Constraints

Follow PROGRAM1_OPERATOR_JOBS_CONTRACT.md. Approved existing .venv only. Preserve 95% gates and existing changes. No Shopee assumptions, Program2/3 feature changes, or UI lifecycle authority.

## Task 1: Bounded read model and contract tests

- [x] Add `list_discovery_jobs(*, limit=20, offset=0)` to application/program1_jobs.py: validate bounds, filter domain/type, sort `(created_at, job_id)` descending, return page/total.
- [x] Add GET route to interfaces/api/shared_jobs.py with Query bounds; serialize items excluding lease_token.
- [x] Test two pages, empty result, invalid bounds, unrelated domains/types and no lease_token in tests/contract/test_shared_job_api_contract.py. Run `.venv/Scripts/python.exe -m pytest tests/contract/test_shared_job_api_contract.py`.

## Task 2: Operator monitor

- [x] Create src/ui/jobMonitor.mjs: state labels, guidance, GET page, read failure reporting with no mutations.
- [x] Create src/ui/JobMonitor.vue: loading/error/empty/table states, diagnostics, page navigation and explicit refresh. Mount in BackOffice.vue.
- [x] Add Node tests for mapping and network failure handling; run the extension stage of tools/program1_verify.py.

## Task 3: Verify and handoff

- [x] Run full tools/program1_verify.py with the approved venv; retain failed/environment-gated stages honestly.
- [x] Inspect localhost in visible Brave; do not mutate existing user jobs for testing.
- [x] Update Kanban and verification with exact reports/CI and remaining creation/live-evidence gaps; commit/push coherent slice.


