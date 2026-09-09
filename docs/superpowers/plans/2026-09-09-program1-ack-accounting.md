# Program 1 ACK Accounting Implementation Plan

**Goal:** Account for duplicate observations safely and display the validated receipt after restart.
**Architecture:** Existing atomic Back Office receipts remain authoritative; additive v2 fields project their counts. Extension validates, persists display evidence and checkpoints only the current batch.
**Tech Stack:** Python 3.12/FastAPI/SQLite, MV3 JavaScript, Vue/daisyUI.

## Tasks

- [x] Add failing SQLite/API/worker tests for v2 mixed/duplicate counts and source_job_id persistence.
- [x] Implement additive result fields and persistence mapping correction; preserve all conflicts.
- [x] Validate v2/legacy ACKs; carry individual receipts through drain/checkpoint; persist latest receipt with serialized outbox changes.
- [x] Display receipt categories with explicit observation/product distinction and reload-safe status.
- [x] Run narrow tests and required pipeline; record local/CI/Brave boundaries.
- [x] Update Kanban, UML D5/D6, verification/CAPA, commit/push focused branch.

Governing acceptance: `PROGRAM1_ACK_ACCOUNTING_CONTRACT.md`. Work in the requested checkout and existing virtual environment. No guessed DOM, pagination, scoring or historical provenance repair.

