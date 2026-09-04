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
- Status: FIXED / FINAL CI VERIFICATION PENDING
- Symptom: verified headless slice used only an in-memory repository, so restart durability and migration behavior were unproven.
- Expected behavior: Portable mode persists Program 1 observations durably using SQLite behind the same repository contract, with Alembic migration governance.
- Actual behavior: no SQL-backed Program 1 repository existed in the first foundation slice.
- Impact: foundation logic was verified but could not yet claim durable Back Office readiness.
- Root cause: deliberate vertical-slice staging; persistence was scheduled as the next verification stage rather than hidden inside the first proof.
- Corrective action: implemented SQLAlchemy ProductRepository, SQLite managed URL resolution, Alembic schema, portable composition root, restart tests and atomic durable batch ingestion.
- Preventive action: every persistence-reliant feature must include real DB adapter + migration + restart test before durable-readiness claims.
- Regression test / monitoring: `tests/integration/sqlite/`; CI `backoffice-sqlite` with layer-specific branch coverage gate.
- Documents/ADR/config updated: Development Cycle Standard; ADR-042; this register.
- Owner: Program 1 Back Office
- Verification evidence: SQLite integration and stress gates have passed on intermediate committed trees; final current-tree verification pending.
- Lesson learned: fake/in-memory verification is essential but must never be confused with durable-store verification.
- Cross-program applicability: YES — all persistence-backed domains.

---

## PL-2026-004 — SQLite timezone round-trip changed semantic equality
- Date: 2026-08-31
- Program/Component: Program 1 / SQLAlchemy SQLite adapter
- Severity: HIGH contract defect found before release
- Detection source: real SQLite repository integration test
- Status: FIXED / REGRESSION COVERED
- Symptom: resending an identical observation was classified as an `observation_id` conflict after SQLite round-trip.
- Expected behavior: identical durable observation retry is idempotent and accepts zero new facts without conflict.
- Actual behavior: SQLite returned `collected_at` without timezone metadata; direct Pydantic model equality compared the naive persisted timestamp to the UTC-aware incoming timestamp and reported inequality.
- Impact: valid worker retries could be rejected after durable persistence.
- Evidence/Reproduction: failed `test_sqlite_repository_matches_duplicate_and_conflict_contract` in CI during the SQLite implementation cycle.
- Immediate containment: SQLite persistence was not promoted while the contract test was failing.
- Root cause: SQLite datetime storage/driver semantics do not preserve timezone metadata in the same way as the in-memory Python object.
- Contributing factors: the in-memory fake could not reveal database-dialect serialization semantics.
- Corrective action: normalize a naive persisted timestamp to UTC at the SQL repository/batch-ingestion boundary before reconstructing the domain observation.
- Preventive action: repository contract suites must execute against every Tier-1 database; persistence adapters own dialect normalization and domain models remain dialect-free.
- Regression test / monitoring: SQLite duplicate/restart tests remain mandatory; PostgreSQL will run equivalent repository contracts.
- Documents/ADR/config updated: Development Cycle Standard and this register.
- Owner: Program 1 Persistence
- Verification evidence: subsequent SQLite repository/Alembic CI gate passed after the normalization change.
- Lesson learned: a fake proves business semantics, but only a real adapter proves serialization/dialect semantics. Both test layers are mandatory.
- Cross-program applicability: YES — all database adapters.

---

## PL-2026-005 — Durable ACK receipt initially had a split transaction boundary
- Date: 2026-08-31
- Program/Component: Program 1 / ingestion reliability
- Severity: HIGH reliability design defect found during review
- Detection source: senior design review while adding restart tests
- Status: FIXED / REGRESSION COVERED
- Symptom: an early persistence design stored ProductObservations and the batch ACK/idempotency receipt in separate operations.
- Expected behavior: once a worker receives an ACK, the server must be able to reproduce the same logical ACK after restart; crash boundaries must not create ambiguous durable state.
- Actual behavior: a process failure after committing observations but before persisting the receipt could make a retry return a different `accepted_count` or lose the batch identity.
- Impact: violated the intended persist-before-ACK / deterministic retry contract and could confuse Browser Worker outbox handling.
- Root cause: initial persistence refactor mapped existing in-memory structures too literally rather than re-evaluating the transaction boundary required by acknowledgement semantics.
- Corrective action: replaced separate BatchStore behavior with `IngestionBatchIngestor`; SQL implementation claims batch identity, validates/inserts observations and finalizes receipt inside one transaction.
- Preventive action: any durable ACK design must document and test the atomic state/receipt boundary; added ADR-042 and sequence diagram.
- Regression test / monitoring: restart retry must return original ACK; changed payload under same batch ID remains conflict after restart.
- Documents/ADR/config updated: ADR-042; `DEVELOPMENT_CYCLE_DIAGRAMS.md`; this register.
- Owner: Program 1 Back Office / Persistence
- Verification evidence: `tests/integration/sqlite/test_program1_durable_batch.py`; final current-tree CI pending.
- Lesson learned: transaction boundaries must follow business acknowledgement semantics, not repository class boundaries.
- Cross-program applicability: YES — job ACKs, publishing ledger, exports and other retryable durable commands.

---

## PL-2026-006 — Coverage gate exposed unverified composition-root code
- Date: 2026-08-31
- Program/Component: Program 1 / CI + bootstrap
- Severity: MEDIUM
- Detection source: 95% branch coverage CI gate
- Status: FIXED / FINAL CI VERIFICATION PENDING
- Symptom: all 26 core tests passed and Ruff passed, but core CI failed because selected coverage fell to 90.83%.
- Expected behavior: newly introduced executable production paths have an explicit test layer and retain the required quality gate.
- Actual behavior: `bootstrap/migrations.py` and `bootstrap/program1.py` were included by a broad core coverage target while their correct tests belong to the real SQLite integration layer; both showed 0% in the core-only run.
- Impact: correctly prevented declaring the new committed tree verified without composition/migration tests.
- Root cause: source modules were added before CI coverage ownership was explicitly mapped to their appropriate test layer.
- Corrective action: added integration tests for migration bootstrap and durable Program 1 composition; split coverage by test layer while retaining 95% gates rather than lowering the threshold.
- Preventive action: every new implementation module must declare its primary verification layer before merge; CI coverage scopes mirror architecture/test layers.
- Regression test / monitoring: `backoffice-core` 95% selected core coverage; `backoffice-sqlite` 95% selected persistence/composition branch coverage.
- Documents/ADR/config updated: Development Cycle Standard; this register.
- Owner: Program 1 / Engineering Quality
- Verification evidence: final current-tree CI pending.
- Lesson learned: coverage is useful when it identifies unverified execution paths, but coverage ownership should follow test-layer responsibility rather than one undifferentiated percentage.
- Cross-program applicability: YES.

---

## PL-2026-007 — Windows SQLite absolute URL was misclassified as managed relative path
- Date: 2026-08-31
- Program/Component: Program 1 / SQLAlchemy SQLite bootstrap and path resolution
- Severity: MEDIUM
- Detection source: local Program 1 SQLite integration test on Windows
- Status: FIXED / REGRESSION COVERED
- Symptom: Program 1 bootstrap migration tests failed when using a temporary SQLite database URL shaped as `sqlite:///C:/...`.
- Expected behavior: explicit absolute SQLite URLs supplied by the test/infrastructure boundary should pass through unchanged, while managed project-owned SQLite paths remain relative-first and escape-checked.
- Actual behavior: the resolver treated the Windows absolute path after `sqlite:///` as a managed relative path and rejected it before migration bootstrap.
- Impact: Portable-mode SQLite bootstrap was blocked in Windows temp-path based tests, even though the production path policy itself was still correct.
- Evidence/Reproduction: `tests/integration/sqlite/test_program1_bootstrap.py` failed before the resolver fix.
- Immediate containment: do not treat the local Program 1 SQLite gate as green until the resolver regression and full SQLite suite pass.
- Root cause: SQLite URL handling recognized `sqlite:////...` absolute paths but missed the valid Windows form `sqlite:///C:/...`.
- Contributing factors: URL/path boundary behavior differs by platform and was not explicitly covered by a regression test.
- Corrective action: classify Windows absolute SQLite paths with `PureWindowsPath(...).is_absolute()` and pass them through before applying managed-relative containment checks.
- Preventive action: keep cross-platform SQLite URL boundary cases in the integration suite; add platform-specific path forms when resolver behavior changes.
- Regression test / monitoring: `test_database_url_resolution_boundary_cases` now covers `sqlite:///C:/runtime/program1.db`; Program 1 bootstrap and SQLite integration suites pass locally.
- Documents/ADR/config updated: this register.
- Owner: Program 1 Persistence
- Verification evidence: local `.venv` verification on 2026-08-31: Ruff PASS; Program 1 SQLite integration `14 passed, 1 skipped`; full SQLite integration `22 passed, 1 skipped`; stress `1 passed`.
- Lesson learned: path policy tests must cover URL syntax as well as filesystem semantics, especially where SQLAlchemy accepts platform-specific absolute SQLite forms.
- Cross-program applicability: YES — all SQLite-backed portable-mode components.

---

## PL-2026-008 — Program 1 side panel left Chrome message-port errors visible
- Date: 2026-08-31
- Program/Component: Program 1 / Browser Worker extension
- Severity: MEDIUM usability and testability defect
- Detection source: user acceptance test in Brave extension side panel
- Status: FIXED / REGRESSION COVERED
- Symptom: the extension errors page reported `Unchecked runtime.lastError: The message port closed before a response was received` with context `src/sidepanel.html`.
- Expected behavior: all extension transport failures should be consumed at the browser API boundary and shown as deterministic process-state errors in the side panel.
- Actual behavior: background runtime messaging was normalized, but active-tab capture still used a direct `chrome.tabs.sendMessage` callback path that could expose closed-port errors.
- Impact: user testing looked broken even when the backend was healthy, and the side panel did not consistently explain whether the failure was backend, page support, permission, or content-script transport.
- Evidence/Reproduction: Brave extension error surfaced after backend `/health` and root endpoint both returned OK on `http://127.0.0.1:8000/`.
- Root cause: extension transport handling was split between runtime messages and tab messages; only the runtime path had a Promise wrapper that consumed `chrome.runtime.lastError`.
- Corrective action: added `sendTabMessage(tabId, message)` wrapper, routed active-tab capture through `await`, normalized missing responses, preserved visible process-state errors, and bumped the extension manifest to `0.1.2` for reload verification.
- Preventive action: every Chrome/Brave messaging boundary must use a local wrapper that reads `chrome.runtime.lastError` inside the callback and returns an explicit `{ ok: false, error }` shape.
- Regression test / monitoring: `browser_plugin/program1/tests/sidepanel.test.cjs` now covers closed-port errors for both runtime messages and tab messages.
- Documents/ADR/config updated: Program 1 extension message-port reliability implementation plan and this register.
- Owner: Program 1 Browser Worker
- Verification evidence: local Node extension tests passed on 2026-08-31: `24 passed, 0 failed`; `node --check` passed for `sidepanel.js` and `background.js`; backend health returned `ok`.
- Lesson learned: Manifest V3 extension APIs have multiple transport surfaces; reliability policy must cover each browser callback boundary, not just the background service-worker channel.
- Cross-program applicability: YES — all browser extensions and side-panel workers.

---

## PL-2026-009 — Program 1 outbox poison-message head-of-line blocking and cross-realm error normalization
- Date: 2026-09-05
- Program/Component: Program 1 / Browser Worker delivery reliability
- Severity: HIGH reliability finding
- Detection source: senior audit + CI CAPA rounds
- Status: VERIFIED
- Symptom: the original outbox drain stopped at the first permanent-invalid message, so one poison payload could block every later valid batch. Transport failures were represented only as error strings and there was no durable quarantine.
- Expected behavior: clearly permanent payload defects are isolated for operator review; transient/auth/network/ACK ambiguity remains fail-closed and retains durable work; current-batch checkpoint occurs only after an authoritative matching ACK.
- Actual behavior: all errors stopped the queue and the first item remained active indefinitely.
- Impact: a single permanent-invalid batch could cause persistent delivery head-of-line blocking and degrade worker throughput/recoverability.
- Root cause: initial durable-outbox slice implemented conservative stop-on-error semantics before failure taxonomy/quarantine ownership was formalized.
- Corrective action: added pure delivery-reliability policy; durable quarantine storage; conservative HTTP/ACK failure classification; current-message sent/quarantined tracking; process-status quarantine telemetry; worker health remains DEGRADED when quarantine requires attention.
- Preventive action: delivery policy is framework-free and unit-tested; permanent quarantine is intentionally limited to explicit payload/semantic statuses; ambiguous/transient/auth/config errors never delete the message.
- Regression test / monitoring: `delivery_reliability.test.mjs`, `background_transport.test.cjs`, full extension CI suite.
- Additional CI finding: the VM background harness initially failed because it stripped only the old static import shape; CAPA updated the dependency-injection harness instead of hiding the new module boundary.
- Additional robustness finding: VM/cross-realm errors failed `instanceof Error`; production and harness now use structural `error.message` normalization.
- Documents/ADR/config updated: Program 1 README, Program 1 Kanban, this CAPA register.
- Owner: Program 1 Browser Worker
- Verification evidence: CI run `33929170024` passed Program 1 extension, core/conformance, SQLite and stress after CAPA round 3.
- Lesson learned: durable delivery needs failure taxonomy and isolation, and JavaScript error normalization at extension/VM boundaries should be structural rather than realm-dependent.
- Cross-program applicability: YES — browser/worker outboxes and any JavaScript plugin boundary.
