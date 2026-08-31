# Program 1 Back Office Test Report — 2026-08-31

Status: VERIFIED FOR CURRENT FOUNDATION SLICE
Scope: Program 1 Back Office foundation / headless thin slice
Governing rule: Project must follow the documents.

## 1. Test Objective

Verify Program 1 Back Office using layered, destructive and boundary-oriented testing rather than happy-path-only validation.

Test principles:
- deterministic first;
- negative/boundary cases are first-class;
- property/invariant testing;
- idempotency and conflict semantics;
- concurrency checks;
- high-volume stress checks;
- API contract behavior;
- configuration/path safety;
- branch coverage gate;
- defects found by tests become regression tests.

## 2. Layers Covered

- ProductObservation validation
- Product Intelligence scoring framework
- shortlist ordering and bounds
- in-memory repository idempotency/conflicts
- concurrent duplicate ingestion
- application batch idempotency
- API validation/conflict contracts
- TOML configuration precedence/validation
- PathManager relative-first containment
- randomized/fuzz-style deterministic score generation
- Hypothesis property-based invariants
- 100,000-observation stress scenario
- Ruff static quality gate
- branch coverage gate

## 3. Destructive Test Findings

The first adversarial pass exposed these implementation defects/guardrail gaps:

1. Negative scoring weights could produce a score above 100.
2. NaN scoring weights could produce NaN output.
3. All-zero scoring weights silently produced a meaningless score.
4. Negative shortlist limit used Python slicing semantics instead of failing closed.
5. Reusing an observation_id with different facts was silently treated as a duplicate.
6. Empty canonical identity/name strings were accepted.
7. Negative product price was accepted.
8. Managed paths could use absolute paths or `../` traversal outside project root.
9. Batch retries did not preserve identical ACK semantics at batch identity level.
10. Reusing a batch_id with a different payload had no explicit conflict behavior.
11. In-memory duplicate ingestion relied on implementation/runtime behavior rather than an explicit concurrency lock.

All items above were corrected in the current foundation code and corresponding regression tests were added.

## 4. Hardening Changes

- Pydantic constraints for non-empty identity/name, finite rating, non-negative price/signals.
- ScoringPolicy validates finite/non-negative weights and requires at least one positive weight.
- ProductScore/ShortlistEntry enforce finite score range `[0, 100]`.
- shortlist rejects invalid limit and threshold values.
- InMemoryProductRepository uses an explicit `RLock`.
- observation_id collision with different facts raises a conflict.
- latest-observation tie behavior is deterministic.
- Program1Service provides deterministic batch fingerprint/idempotency semantics.
- same batch retry returns the original logical ACK result.
- same batch_id with changed payload raises conflict.
- API maps ingestion conflicts to HTTP 409 and invalid payloads to HTTP 422.
- PathManager enforces relative-first managed paths and blocks project-root escape.
- TOML scoring configuration validates invalid ranges at startup.

## 5. Heavy Tests

### 100k observation stress
Scenario:
- construct 100,000 valid ProductObservation objects;
- ingest all into the in-memory repository;
- build a top-20 shortlist.

Expected invariants:
- accepted count = 100,000;
- shortlist length = 20;
- ranks remain contiguous and deterministic.

### Concurrent duplicate ingest
Scenario:
- 20 threads attempt to ingest the same observation simultaneously.

Expected invariant:
- exactly one logical observation is accepted;
- one latest observation remains.

### Randomized score test
10,000 deterministic pseudo-random observations are scored and must always produce finite values within `[0, 100]`.

### Property-based test
Hypothesis generates large ranges for sold/review/rating/price values and checks:
- score is finite;
- score remains bounded;
- demand component is monotonic before saturation.

## 6. Local Verification Snapshot

A reconstructed current Back Office source snapshot was executed in an isolated test workspace before pushing the hardening changes.

Result after fixes:
- 25 tests passed in the local verification snapshot;
- selected Program 1 Back Office branch coverage approximately 97%.

Local verification is supporting evidence. GitHub Actions is the authoritative repository CI because it executes the committed tree.

## 7. Authoritative GitHub CI Result

Verified code commit: `1e3441a86a5f71c61c492ebee08a975dd61fea13`
GitHub Actions run: `CI #26` / run id `33348015044`
Result: **SUCCESS**

### `backoffice-core` — SUCCESS
- dependency installation: PASS
- Ruff: PASS — `All checks passed!`
- non-stress unit/component/contract/property/concurrency tests: **26 passed**
- stress-marked test intentionally deselected from core run: 1
- selected Program 1 Back Office branch coverage: **96.97%**
- required coverage gate: **95%**
- coverage gate: PASS

### `backoffice-stress` — SUCCESS
- high-volume stress suite: PASS
- 100,000-observation ingestion + shortlist scenario: PASS
- timeout guard: PASS

The code commit therefore satisfies the current Back Office foundation verification gate.

## 8. Non-Blocking Warning Observed

The core CI emitted one ecosystem deprecation warning from the FastAPI/Starlette test-client stack concerning the current `httpx` integration. It did not affect test correctness or the pass result.

Action:
- track dependency compatibility during the dependency-lock/upgrade cycle;
- do not suppress the warning globally merely to obtain a clean log;
- update the test-client dependency path when the supported stack requires it.

## 9. Not Yet Claimed as Verified

The following must not be inferred from this test campaign:
- SQLite repository semantics — not implemented yet in this Program 1 slice;
- PostgreSQL repository semantics — not implemented yet;
- Alembic migration compatibility for Program 1 tables — not implemented yet;
- restart durability using a real SQL store — not yet testable;
- multi-process/multi-host DB contention — requires persistence implementation;
- real Shopee DOM/parser compatibility — belongs to Browser Plugin adapter validation;
- production Product Scoring Model v1 correctness — formula remains a validation gate;
- million-observation production DB performance — requires SQL persistence/load environment.

## 10. Verification Decision

**Program 1 Back Office current in-memory/headless foundation slice = VERIFIED.**

This verification covers the implemented scope only. It is not equivalent to full Program 1 production readiness.

Next mandatory Back Office verification stage after implementation is:
1. SQLAlchemy Program 1 persistence;
2. SQLite repository contract suite;
3. Alembic migration/restart/recovery tests;
4. PostgreSQL repository compatibility suite;
5. concurrency/lock/contention/failure-injection against real databases;
6. larger persistence-backed load/endurance tests.

Production readiness remains feature-gated by `PROGRAM1_IMPLEMENTATION_READINESS.md` and the governing project documents.
