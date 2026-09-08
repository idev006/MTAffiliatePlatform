# Program 1 Development Pipeline Implementation Plan

**Goal:** Run existing quality gates consistently in local development and CI, with attributable failure evidence.

**Architecture:** A standard-library CLI runs argument arrays from a versioned TOML gate registry. Local runs use the explicitly invoked virtual environment; CI uses its setup-python runtime. No business authority moves and no production evidence is implied.

**Tech Stack:** Python 3.12, TOML, pytest, Ruff, Node, existing GitHub Actions.

## Global Constraints

- Work in the current repository; use its existing `.venv` locally.
- Preserve the existing 95% branch coverage gates and all CI jobs.
- Program 2/3 business behavior is outside scope; shared repository regression gates remain required.
- Browser laboratory results and visible Brave/Shopee acceptance are separate evidence.

## Task 1: Shared verification entrypoint

- [x] Extract existing CI gate commands into `config/quality-gates.toml` without changing test selection or coverage scopes.
- [x] Add `tools/program1_verify.py`: explicit stage selection, checked runtime, fixed repository cwd, bounded subprocesses, fail-fast, per-step logs, atomic JSON report with Git context.
- [x] Add `tests/unit/test_program1_verify.py`: actual child-process failure/timeout, cwd-independent execution, interpreter reuse, honest partial-run status, report persistence.
- [x] Route CI gate execution through the same registry; retain dependency setup and upload reports even on failures.
- [x] Run narrow tests, static, core, SQLite, stress, extension and browser gates. Local browser launch failed; the same browser gate passed in CI `34192148182`.
- [x] Update Program 1 Kanban/handoff and verification evidence; commit/push a recoverable checkpoint (PR #42).

## Acceptance

`python tools/program1_verify.py --profile full` runs every registered gate. A failed step returns nonzero and leaves later steps NOT_RUN in the report. Scoped success cannot be mistaken for full verification. Logs and reports never claim live Shopee/Brave acceptance.
