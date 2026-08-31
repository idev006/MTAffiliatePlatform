# Program 2 + Program 3 Problem / Lesson Learned / CAPA Record

Date: 2026-08-31
Status: ACTIVE VERIFICATION RECORD
Parent policy: `DEVELOPMENT_CYCLE_STANDARD.md`
Parent register: `PROBLEM_LESSON_AND_CAPA_LOG.md`

## P23-PL-001 — A configurable safety bypass contradicted the publishing invariant
- Program/Component: Program 3 / configuration + publishing guard
- Severity: HIGH design-quality finding before release
- Detection source: architecture/code consistency review
- Status: FIXED / REGRESSION COVERED
- Symptom: early Program 3 typed settings exposed `block_ambiguous_outcomes`, implying an operator could disable blocking after an uncertain publish outcome.
- Expected behavior: `POST_OUTCOME_UNKNOWN` / ambiguous irreversible outcome always prevents blind repost until reconciliation evidence resolves it.
- Actual risk: a configuration flag could have become a future bypass around the governing duplicate/reconciliation invariant.
- Root cause: configurable-policy thinking was applied too broadly to a correctness/safety invariant.
- Corrective action: removed the toggle from typed settings and TOML; the engine always fails closed for ambiguous publish outcomes.
- Preventive action: configuration reviews must classify each value as tunable policy vs non-bypassable invariant. Safety invariants cannot be disabled by ordinary deployment config.
- Regression evidence: Program 3 duplicate and reconciliation tests; typed config tests.
- Documents affected: Program 3 design/readiness; verification report; this CAPA record.
- Lesson learned: "no hard-code" does not mean "everything is configurable". Some behavior belongs as a hard invariant enforced by domain/engine code.
- Cross-program applicability: YES.

## P23-PL-002 — Static quality gates caught rapid parallel-development drift
- Program/Component: Program 2 + Program 3 / CI
- Severity: MEDIUM
- Detection source: Ruff CI gate
- Status: VERIFIED
- Symptom: import-order, modern-Python import location and mutable class-constant issues stopped Core CI before tests.
- Expected behavior: new Program 2/3 foundation code conforms to the same static quality baseline as Program 1.
- Actual behavior: rapid parallel foundation commits temporarily introduced lint violations.
- Root cause: implementation was intentionally moving in small vertical commits, while formatting/static normalization lagged some commits.
- Corrective action: fixed artifacts; changed mutable class sets to immutable `ClassVar[frozenset]`; used modern import locations; normalized imports.
- Preventive action: retain Ruff before pytest in CI; never suppress or weaken the rule simply to pass.
- Regression evidence: CI run #155 passed Ruff and all downstream gates.
- Lesson learned: early static failure is cheaper than letting low-level quality drift mix with behavioral failures.
- Cross-program applicability: YES.

## P23-PL-003 — Cross-program parallelism requires contracts and fakes, not waiting
- Program/Component: Program 1 -> Program 2 -> Program 3 integration
- Severity: POSITIVE LESSON / PROCESS
- Detection source: implementation cycle
- Status: ADOPTED
- Assumption tested: Program 3 might have to wait for Program 2 and Program 2 might have to wait for real Shopee workers.
- Evidence: Program 2 selection and Program 3 publishing foundations were implemented and tested in parallel using versioned handoff contracts, in-memory repositories, fake Offer workers and scripted Android adapters.
- Design/process change: versioned DTO/contracts + deterministic fakes are mandatory for unfinished external/upstream dependencies.
- Enforcement: ADR-045, implementation Kanban dependency rules, component/contract tests.
- Lesson learned: waiting for a full upstream implementation creates unnecessary coupling; contract-first fake-driven vertical slices provide earlier defect discovery.
- Cross-program applicability: YES.

## P23-PL-004 — Durable state must be verified after process/repository recreation
- Program/Component: Program 2 Offer selection + Program 3 Publishing Ledger
- Severity: HIGH readiness principle
- Detection source: persistence verification design
- Status: VERIFIED FOR SQLITE FOUNDATION
- Risk: in-memory success could be mistaken for durable correctness.
- Corrective action: added SQLAlchemy repositories, Alembic revision `0002_program2_program3`, and restart/repository-recreation integration tests.
- Preventive action: any capability whose correctness depends on history must have a real-database restart test before a durable-readiness claim.
- Regression evidence: SQLite CI gate in run #155.
- Lesson learned: duplicate prevention, selection provenance and retry semantics only become trustworthy when their authoritative history survives restart.
- Cross-program applicability: YES.

## P23-PL-005 — Real-platform uncertainty belongs behind adapters and evidence gates
- Program/Component: Program 2 Browser Worker + Program 3 Android Worker
- Severity: HIGH architectural principle
- Detection source: implementation-readiness review
- Status: ADOPTED
- Risk: hard-coding assumed Shopee Offer identity, DOM selectors, Android coordinates, basket limits or scene signatures before controlled evidence would create fragile false certainty.
- Corrective action: implemented worker/scene/device behavior with contracts, fake workers, scripted snapshots, logical scene signatures and adapter ports only. Real platform specifics remain validation gates.
- Preventive action: every external-platform assumption must have evidence source/version/profile before it can become a production adapter rule.
- Regression evidence: engines and application services run without browser/device/network; real-platform constants are absent from core domain logic.
- Lesson learned: the highest-value foundation work is to make uncertain external behavior replaceable and testable, not to guess it early.
- Cross-program applicability: YES.

## Closure Rule
These records are considered adopted because each lesson changed at least one durable artifact: code guardrail, test, CI rule, contract, configuration schema or governing documentation.
