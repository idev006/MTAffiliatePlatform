# Codex Next Work Queue — MTAffiliatePlatform

Date: 2026-08-31
Status: ACTIVE CONTINUATION QUEUE
Audience: Codex Work Desktop / developers

This queue is ordered for efficient continuation from the current repository state. Re-check current HEAD, CI and Kanban before starting; if the repository moved, preserve the intent but reconcile with the latest evidence.

## P0 — Restore and Prove Current-Tree Green Baseline

### Goal
Make the latest `main` HEAD verifiably green before declaring the newest Program 2 parser and Program 3 full scripted workflow laboratory slices verified.

### Known context
CI #165 on head `7d45b77e7810c9d08bdb2988ebfc138138116cdb` failed only at Ruff. SQLite and Stress passed. The Ruff findings were subsequently corrected in source/tests.

### Actions
1. inspect latest HEAD and latest CI run;
2. run `ruff check src tests migrations` locally;
3. run core/component/contract suite;
4. run SQLite integration suite;
5. run stress suite;
6. fix legitimate failures without lowering gates;
7. update `PROGRAM2_PROGRAM3_VERIFICATION_REPORT_2026-08-31.md` with the newly verified head/run if all green;
8. update Program 2/3 Kanban slice status for parser/full scripted workflow;
9. record a CAPA item only if a new meaningful defect/root-cause pattern is found.

### Exit criteria
- Ruff PASS;
- core selected branch-coverage gate PASS;
- SQLite/Alembic integration PASS;
- stress PASS;
- verification report references the verified current-tree head/run.

---

## P1 — Program 2 Export/Link Laboratory Completion

### Goal
Finish P2-VS4 laboratory behavior without claiming a real Shopee export format.

### Scope
- strengthen `OfferExportParserPort` contract;
- add versioned synthetic/golden fixtures;
- validate artifact SHA-256 before parsing where the governing contract requires it;
- validate account/product/offer provenance;
- define duplicate-link/idempotent ingest semantics;
- define stale/fresh link decision semantics behind a versioned policy;
- add malformed/schema-drift fixture classifications;
- persist link/artifact records if the current data-model/DoR authorizes the slice;
- add restart tests if persistence is added.

### Do not do
- do not name a synthetic fixture a Shopee production schema;
- do not freeze a real export column/layout without evidence;
- do not embed browser selectors in domain/application layers.

### Suggested tests
- valid synthetic fixture;
- malformed JSON/content;
- wrong root/schema;
- cross-account record;
- checksum mismatch;
- duplicate artifact/link replay;
- same identity with changed payload conflict;
- parser profile version mismatch;
- stale link policy boundary.

---

## P1 — Program 3 Full Scripted Publishing Laboratory Completion

### Goal
Turn the full scripted workflow into a strong fake E2E/resilience laboratory before physical-device work.

### Scope
- full Scene sequence from VIDEO_SOURCE to PUBLISH_SUCCESS;
- negative transition fixtures at every Scene boundary;
- UNKNOWN and AMBIGUOUS Scene behavior;
- action failure before submit;
- transition verification failure;
- checkpoint replay/resume;
- worker restart at safe boundaries;
- destructive `SUBMIT_POST` ambiguity;
- reconciliation to CONFIRMED / NOT_PUBLISHED / NEEDS_HUMAN;
- device disconnect/reconnect simulated through ports;
- app-restart policy simulation without real selectors;
- worker-event ordering/idempotency tests;
- no double action after replay.

### Exit criteria
A deterministic fake E2E suite demonstrates that the workflow never crosses an irreversible boundary blindly and can resume/reconcile according to documents.

---

## P1 — Shared Job Engine Integration into Program 2/3

### Goal
Ensure Program 2/3 domain-specific lifecycle does not become an independent lifecycle SSOT.

### Scope
Audit existing Shared Job Engine implementation first. Then integrate Program 2 worker commands/results and Program 3 publishing work with the shared job/lease/event authority through ports/application contracts.

Required invariants:
- one active job lease;
- idempotent result/event admission;
- worker heartbeat/lease expiry;
- checkpoint references;
- safe reassignment where external side-effect history permits it;
- no reassignment/blind replay across ambiguous irreversible publish state;
- append-oriented event history;
- Back Office owns canonical transitions.

Do not duplicate lease/retry authority inside Offer or Publishing domain tables.

---

## P2 — PostgreSQL Tier-1 Compatibility Harness

### Goal
Prove the Farm Mode database target without redesigning domain/application code.

### Scope
- run repository contract suites against PostgreSQL;
- migration upgrade from empty DB;
- transaction/isolation behavior;
- timezone/serialization parity;
- unique/idempotency constraints;
- optimistic concurrency/conflict handling;
- deadlock/serialization retry boundaries where applicable;
- SQLite/PostgreSQL semantic parity tests.

If PostgreSQL is unavailable in the current environment, prepare container/test configuration and mark execution as environment-gated; do not fake a PostgreSQL PASS.

---

## P2 — Architecture Dependency Tests

### Goal
Prevent future framework leakage into domain/engine layers.

### Scope
Add automated import/dependency checks if not already comprehensive.

Rules to enforce:
- `domain` and `engines` cannot import FastAPI/SQLAlchemy/PySide6/ADB/uiautomator2/Appium/scrcpy/browser-specific implementations;
- adapters may depend inward on ports/domain/application contracts as designed;
- interfaces compose/application-call but do not own domain policy;
- Program 3 must not depend directly on Program 2 persistence implementations.

A dependency violation should fail CI early.

---

## P2 — Configuration / Ruleset Versioning

### Goal
Make policy changes traceable and replayable without converting safety invariants into toggles.

### Scope
- versioned scoring-policy snapshot references;
- duplicate-policy version references;
- parser/selector profile versions;
- configuration validation;
- running job retains the policy/config snapshot it started with;
- changes affect new jobs unless an explicit migration/replan contract exists.

Test concurrent config change while a job is running.

---

## P2 — Failure Injection and Recovery Matrix Automation

### Goal
Turn documented failure/conflict matrices into executable regression tests.

Automate as many as possible without real devices:
- two workers claim same job;
- two workers claim same device;
- lease expiry + safe reassignment;
- worker process crash;
- Back Office restart;
- DB lock/contention;
- local outbox ACK loss;
- disk/outbox capacity signal;
- browser/session-required classification;
- Android UNKNOWN Scene;
- simulated device disconnect;
- simulated app crash;
- network loss before submit;
- network loss after submit -> ambiguous outcome;
- duplicate video publish attempt.

Each test should assert detection, authority owner, containment, recovery and forbidden outcome.

---

## P3 — Controlled Real Browser Evidence Spike

### Prerequisite
Foundation/laboratory CI green and explicit controlled test account/environment available.

### Goal
Capture evidence only; do not prematurely productionize.

Collect:
- Product/Offer identity evidence;
- affiliate account/session influence;
- actual export artifacts;
- page/schema drift samples;
- selectors only inside outer adapter/profile fixtures;
- screenshots/HTML snapshots where allowed and safe.

Update governing docs/ADR before freezing identity/schema behavior.

---

## P3 — Controlled Physical Android Device Spike

### Prerequisite
Fake workflow/resilience laboratory green and a controlled device/account is available.

### Goal
Validate adapter feasibility and collect Scene evidence.

Investigate:
- ADB device state discovery;
- uiautomator2 primary adapter feasibility;
- Appium alternative only where justified;
- package/activity behavior;
- real Scene inventory;
- logical element evidence;
- selector stability hierarchy;
- Safe Anchor candidates;
- publish-submit ambiguity/reconciliation signals.

No scale claim and no blind irreversible automation during the evidence spike.

---

## P4 — Device Host Capacity / Streaming Benchmarks

Only after the physical-device adapter is stable.

Benchmark separately:
- device control throughput;
- CPU/RAM;
- USB/ADB contention;
- screen streaming;
- disk/outbox;
- network;
- Focus vs Overview streaming quality.

Run 10-device evidence first; only progress toward 20/50/100 when earlier levels are stable. Do not extrapolate production claims from a single-device test.

---

## Deferred Until Stable Commands/Read Models — PySide6 UI

UI is intentionally not the next priority unless operator workflow needs it.

When started:
- UI calls application/API commands and queries;
- UI does not own policy/state transition/retry/DB writes;
- UI closing must not invalidate durable work;
- operator takeover/approval is explicit and auditable.

---

## Recommended Codex Session Size

Prefer one session/branch around one vertical outcome, for example:
- `fix/current-ci-baseline`
- `p2/export-artifact-integrity`
- `p3/scripted-recovery-matrix`
- `shared/job-engine-p2-p3-integration`
- `db/postgresql-contract-suite`

Avoid a branch named “finish everything”; it makes review, rollback and RCA harder.

## Stop Conditions

Stop implementation and mark `NEEDS_REAL_DATA`, `NEEDS_DEVICE_LAB` or `NEEDS_DECISION` when:
- the next correct behavior depends on unseen Shopee facts;
- an irreversible action cannot be proven safe;
- an identity/schema/selector must be guessed;
- a production threshold would be invented from no evidence;
- a governing document has unresolved CRITICAL/HIGH conflict.

Stopping at an evidence boundary is correct engineering, not incomplete work.
