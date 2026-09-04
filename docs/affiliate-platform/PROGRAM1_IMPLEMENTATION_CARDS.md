# Program 1 — Developer Implementation Cards

Status: READY-CARD PACK
Date: 2026-09-04
Method: Agile Kanban / Small Vertical Slices

These cards translate the Program 1 architecture into development-ready work. Each card remains subject to current HEAD/CI/evidence checks before IN DEV.

---

## P1-B — Shared Job Lifecycle for Program 1

Status: READY
Priority: P1
Owner: Shared Job Engine + Program 1 Application + Browser Background Runtime

### Outcome
Program 1 long-running work survives UI closure and is controlled by canonical Back Office job state.

### Governing
- `PROGRAM1_SYSTEM_ARCHITECTURE.md` §6.3, §11, §12
- `PROGRAM1_UML_AND_RUNTIME_DIAGRAMS.md` D4, D8, D9
- `JOB_LEASE_PAUSE_RESUME_SPEC.md`
- `PROGRAM1_DEVELOPER_HANDOFF.md`

### Inputs
- DiscoveryPlan reference;
- compatible worker capabilities;
- job policy/config version.

### Outputs
- leased Program 1 job;
- durable checkpoint;
- pause/resume state;
- final result;
- job events.

### Required behavior
1. create/queue Program 1 discovery job;
2. compatible worker leases with token/version/expiry;
3. worker checkpoints after bounded collection unit;
4. pause request reaches a safe checkpoint;
5. resume uses canonical state/checkpoint;
6. job can complete without Side Panel remaining open;
7. worker restart re-registers and reconciles canonical state;
8. stale lease/result cannot overwrite newer job state.

### Forbidden
- UI-owned durable run state;
- hidden parallel lifecycle in extension;
- blind resume from volatile memory.

### Failure cases
- lease expires before checkpoint;
- worker restart;
- Back Office unavailable;
- stale result;
- pause during collection;
- cancel while paused;
- duplicate completion.

### Headless tests
- application/job component tests with fake worker;
- lease conflict;
- pause/resume;
- restart/rejoin;
- stale lease;
- duplicate result.

### Browser integration
Only after headless behavior passes.

### Acceptance
Closing Side Panel does not cancel/corrupt active durable work.

---

## P1-C — Worker Delivery Reliability

Status: READY AFTER/ALONGSIDE P1-B
Priority: P1
Owner: Program 1 Worker Transport + Ingestion Application

### Outcome
Observation delivery remains correct under retries, lost ACKs, invalid messages and restarts.

### Governing
- architecture §13;
- UML D5/D6;
- ADR-042.

### Required contracts
Define structured delivery result fields sufficient to distinguish:
- received;
- durably accounted;
- newly accepted;
- duplicate/already accepted;
- rejected/conflicting;
- ACK identity.

Exact public schema requires contract update before implementation if changed.

### Failure taxonomy
- TRANSIENT_NETWORK;
- BACKEND_UNAVAILABLE;
- RATE_LIMIT/PRESSURE;
- PERMANENT_PAYLOAD;
- CONTRACT_MISMATCH;
- ACK_AMBIGUOUS;
- NEEDS_HUMAN.

### Quarantine
Permanent/ambiguous messages must preserve evidence. No silent discard.

Queue continuation after a quarantined item must be explicit and deterministic.

### Tests
- lost ACK after DB commit;
- same batch replay;
- same batch ID/different payload;
- permanent bad payload at head of queue;
- later valid message behavior;
- restart with pending outbox;
- ACK mismatch;
- backend outage/recovery.

### Acceptance
No valid observation is lost or duplicated because of ordinary retry/restart behavior, and one permanent message cannot cause undocumented infinite head-of-line blocking.

---

## P1-D — Collection Router and Versioned Profiles

Status: READY
Priority: P1
Owner: Browser Adapter

### Outcome
Adding/changing one Shopee surface does not require modifying unrelated collection logic.

### Governing
- architecture §6.6/6.7;
- UML D7/D10/D15;
- evidence docs.

### Domain boundary
DOM logic stays outside domain/application.

### Profile metadata
- profile_id;
- version;
- platform;
- locale/context;
- surface;
- evidence_state;
- required indicators;
- supported fields;
- fixture/evidence references.

### Result
- observations;
- page classification;
- pagination facts;
- profile/version;
- evidence/schema state;
- checkpoint facts.

### Required classifications
- SUCCESS_WITH_OBSERVATIONS;
- SUCCESS_EMPTY_VALIDATED;
- PAGE_UNSUPPORTED;
- PAGE_BLOCKED_BY_ANTIBOT;
- SCHEMA_CHANGED;
- SESSION_REQUIRED;
- PARTIAL_OBSERVATION.

### Tests
Each profile:
- happy fixture;
- validated empty;
- anti-bot;
- missing indicator;
- schema change;
- malformed identity;
- pagination edge.

### Migration approach
Refactor current behavior incrementally. Preserve regression coverage before deleting old paths.

### Acceptance
Router fails closed on ambiguous/unsupported profile and each profile can be fixture-tested independently.

---

## P1-E — Opportunity Feature Snapshot

Status: READY IN PARALLEL
Priority: P1
Owner: Opportunity Feature Engine

### Outcome
Derived opportunity features become versioned, explainable artifacts separate from ProductObservation.

### Initial feature categories
May use synthetic/fake inputs:
- demand;
- momentum;
- buyer-intent context;
- price/value;
- seller confidence;
- competition/saturation;
- contentability;
- risk/uncertainty.

No real-data field is mandatory unless already evidence-approved.

### Required fields
- product identity/reference;
- campaign/context;
- feature policy version;
- reference timestamp;
- component feature values;
- evidence refs;
- data sufficiency;
- unknown state.

### Rules
- missing evidence != zero;
- feature calculation deterministic for same inputs/policy;
- raw observations never mutated into scores.

### Tests
- all evidence present;
- partial evidence;
- no evidence;
- stale evidence;
- same input deterministic;
- policy version differs;
- invalid non-finite values rejected where applicable.

### Acceptance
A fake observation history can produce a fully traceable feature snapshot without browser/UI.

---

## P1-F — Opportunity Decision and Thesis

Status: READY AFTER P1-E
Priority: P1
Owner: Qualification + Opportunity Evaluation + Ranking

### Outcome
System returns an explainable affiliate recommendation instead of only an opaque score.

### Output
- qualification;
- recommended action;
- Opportunity Thesis;
- strengths;
- risks;
- uncertainty;
- evidence freshness;
- optional component/total score;
- policy/model version.

### Actions
`TEST_NOW | WATCH | SCALE | HOLD | DEPRIORITIZE | STOP | NEEDS_EVIDENCE`

### Rules
- insufficient evidence can legitimately produce NEEDS_EVIDENCE;
- no production weights invented;
- same feature snapshot + policy/context => deterministic decision;
- past decision remains historically explainable when new decision supersedes it.

### Tests
- qualified TEST_NOW synthetic scenario;
- missing data -> NEEDS_EVIDENCE;
- risk blocks qualification;
- deterministic tie/ranking;
- policy version change;
- explanation contains evidence references.

### Acceptance
A developer/test can reconstruct why a recommendation was made from durable feature/evidence/policy references.

---

## P1-G — Program 1 -> Program 2 Handoff v1.1

Status: READY AFTER P1-F
Priority: P1/P2
Owner: Program 1 Handoff Application + Program 2 Admission

### Outcome
Only qualified opportunity candidates move to Offer discovery.

### Contract
`PROGRAM1_TO_PROGRAM2_HANDOFF_CONTRACT.md`.

### Must include
- product identity/reference;
- shortlist/opportunity decision;
- action;
- thesis summary;
- policy version;
- evidence freshness;
- source observations;
- idempotency/correlation.

### Tests
- accepted;
- duplicate same payload;
- same idempotency changed payload -> conflict;
- stale evidence;
- invalid identity;
- missing required opportunity decision;
- v1/v1.1 compatibility policy where supported.

### Acceptance
Program 2 does not need Program 1 DB internals to understand why the candidate was admitted.

---

## P1-H — Deterministic Browser E2E CI

Status: DESIGN READY / IMPLEMENT AFTER P1-B/C/D
Priority: P2
Owner: QA + Browser Automation + CI

### Outcome
Real built extension collaborates with local Back Office/fixtures unattended.

### Flow
```text
build extension
-> local Back Office
-> local fixture server
-> launch browser
-> register
-> lease
-> collect page 1
-> outbox
-> ACK
-> checkpoint
-> page 2
-> complete
-> assert durable/mock result
```

### Failure scenarios
- lost ACK;
- backend temporary outage;
- anti-bot fixture;
- schema-change fixture;
- service worker restart if harness permits;
- pause/resume.

### CI policy
Do not call live Shopee.

### Acceptance
Critical Program 1 worker flow can be regression-tested without operator clicking.

---

## P1-I — Evidence-Gated Surface Promotion

Status: NEEDS_REAL_DATA
Priority: P2
Owner: Data/Scraping + QA + Process

### Outcome
Promote only repeatedly validated Shopee fields/profiles.

### Required before promotion
- independent repeated captures;
- sanitized fixtures;
- field-boundary validation;
- negative/schema-change cases;
- evidence record;
- profile lifecycle transition review.

### Forbidden
- promotion based on one capture;
- heuristic broad selector treated as production truth;
- anti-bot bypass.

---

## Card Execution Rule

Before coding:
1. move card through ANALYSIS/DESIGN/READY;
2. verify governing docs/current HEAD;
3. confirm test path;
4. confirm no CRITICAL/HIGH issue.

During coding:
- commit/push coherent checkpoints;
- run narrow tests frequently;
- preserve headless testability.

Before DONE:
- required tests/CI;
- docs/diagram/contract update;
- Kanban status;
- verification evidence;
- push to GitHub.
