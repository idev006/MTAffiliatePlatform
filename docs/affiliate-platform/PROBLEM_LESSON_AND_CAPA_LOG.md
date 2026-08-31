# Problem, Lesson Learned and CAPA Register

Status: ACTIVE PROJECT RECORD
Governing policy: `DEVELOPMENT_CYCLE_STANDARD.md`

## Usage Rule

Every meaningful defect, near miss, design miss, CI gate failure or operational issue is recorded here or in a linked issue with equivalent fields. HIGH/CRITICAL items require explicit root-cause analysis and preventive action.

## Record Template

### PL-YYYY-NNN — Title
- Date:
- Program/Component:
- Severity: LOW | MEDIUM | HIGH | CRITICAL
- Detection source:
- Status: OPEN | CONTAINED | FIXED | VERIFIED | CLOSED
- Symptom:
- Expected behavior:
- Actual behavior:
- Impact:
- Evidence/Reproduction:
- Immediate containment:
- Root cause:
- Contributing factors:
- Corrective action:
- Preventive action:
- Regression test / monitoring:
- Documents/ADR/config updated:
- Owner:
- Verification evidence:
- Lesson learned:
- Cross-program applicability:

---

## PL-2026-001 — Back Office input and policy guardrails were incomplete
- Date: 2026-08-31
- Program/Component: Program 1 / Back Office foundation
- Severity: HIGH design-quality finding before production
- Detection source: destructive/adversarial test campaign
- Status: VERIFIED for current foundation slice
- Symptom: invalid/ambiguous values could pass into scoring, identity, path and ingestion behavior.
- Expected behavior: invalid inputs fail closed; retries/conflicts are deterministic; managed paths remain inside project root.
- Actual behavior: negative/NaN weights, all-zero weights, invalid shortlist bounds, blank identity, negative price and path escape were not all rejected. Batch-level idempotency and collision semantics were incomplete.
- Impact: incorrect scores, ambiguous ACK behavior and unsafe path configuration were possible in the early skeleton.
- Evidence/Reproduction: `PROGRAM1_BACKOFFICE_TEST_REPORT_2026-08-31.md`.
- Immediate containment: do not promote the initial skeleton beyond development verification.
- Root cause: initial thin slice emphasized architecture proof and happy-path behavior before the adversarial verification layer was executed.
- Contributing factors: production scoring formula intentionally unfrozen; early in-memory adapter simplicity; missing batch-idempotency implementation in first pass.
- Corrective action: strengthen Pydantic/domain constraints, scoring validation, repository collision handling, PathManager containment, application batch fingerprint/idempotency and API conflict mapping.
- Preventive action: make adversarial/negative/property/idempotency tests a mandatory cycle gate; maintain 95% selected branch-coverage gate as supporting evidence; record defects as regression tests.
- Regression test / monitoring: unit hardening, Hypothesis properties, API contract, concurrency and 100k stress suites.
- Documents/ADR/config updated: Test Report; Development Cycle Standard; governing test strategy remains applicable.
- Owner: Program 1 Back Office
- Verification evidence: GitHub CI #26 success for code commit `1e3441a86a5f71c61c492ebee08a975dd61fea13`.
- Lesson learned: a thin slice must be treated as a hypothesis until adversarial verification attacks its assumptions. Validation belongs in the model/contract boundary, not only in UI or caller discipline.
- Cross-program applicability: YES — all Programs and Shared Core.

---

## PL-2026-002 — CI lint gate caught quality drift before test execution
- Date: 2026-08-31
- Program/Component: Program 1 / CI
- Severity: MEDIUM
- Detection source: Ruff CI gate
- Status: VERIFIED
- Symptom: 14 style/modern-Python violations stopped CI before pytest.
- Expected behavior: committed source/tests conform to project lint rules.
- Actual behavior: newly added hardening tests/source had import-order and modernization violations.
- Impact: no product defect escaped; CI feedback delayed verification.
- Root cause: rapid hardening changes were pushed before lint-normalization of every touched file.
- Corrective action: update source/tests to satisfy existing Ruff rules without weakening the rules.
- Preventive action: run lint before full test campaign in developer/pre-push workflow; keep CI order static quality -> tests.
- Regression test / monitoring: CI Ruff job remains mandatory.
- Documents/ADR/config updated: Development Cycle Standard explicitly forbids weakening legitimate gates just to obtain green CI.
- Verification evidence: CI #26 Ruff `All checks passed!`.
- Lesson learned: quality gates should fail early and visibly; the correct response is to fix the artifact, not lower the gate.
- Cross-program applicability: YES.

---

## PL-2026-003 — Durable persistence was missing from the first Program 1 slice
- Date: 2026-08-31
- Program/Component: Program 1 / Persistence
- Severity: HIGH readiness gap, intentionally scoped
- Detection source: Back Office verification review
- Status: IN IMPLEMENTATION / VERIFICATION
- Symptom: verified headless slice used only an in-memory repository, so restart durability and migration behavior were unproven.
- Expected behavior: Portable mode persists Program 1 observations durably using SQLite behind the same repository contract, with Alembic migration governance.
- Actual behavior: no SQL-backed Program 1 repository existed in the first foundation slice.
- Impact: foundation logic was verified but could not yet claim durable Back Office readiness.
- Root cause: deliberate vertical-slice staging; persistence was scheduled as the next verification stage rather than hidden inside the first proof.
- Corrective action: implement SQLAlchemy ProductRepository, SQLite path resolution, initial Alembic migration, restart and repository-contract integration tests.
- Preventive action: every persistence-reliant feature must include real DB adapter + migration test before durable-readiness claims.
- Regression test / monitoring: `tests/integration/sqlite/` repository and Alembic suites; CI `backoffice-sqlite` gate.
- Documents/ADR/config updated: Development Cycle Standard; this register.
- Owner: Program 1 Back Office
- Verification evidence: pending current CI run.
- Lesson learned: fake/in-memory verification is essential but must never be confused with durable-store verification.
- Cross-program applicability: YES — all persistence-backed domains.
