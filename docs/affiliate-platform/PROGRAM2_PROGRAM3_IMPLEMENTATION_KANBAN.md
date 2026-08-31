# Program 2 + Program 3 Implementation Kanban

Status: ACTIVE IMPLEMENTATION PLAN
Date: 2026-08-31

## Delivery Principle
Both programs are developed as independent bounded capabilities over Shared Core, but integration is proven continuously through versioned handoff contracts.

No team waits for full Program 2 completion before Program 3 foundation work begins. Fake/contract-driven vertical slices allow safe parallel development.

## Program 2 Epics
### P2-E1 Domain & Contract Foundation — VERIFIED FOUNDATION
- Offer identity/value objects
- OfferObservation
- AffiliateAccountContext
- eligibility/ranking/selection contracts
- Program1->Program2 DTO v1

### P2-E2 Offer Intelligence Engine — VERIFIED FRAMEWORK / BUSINESS MODEL V1 GATED
- eligibility engine
- configurable scoring policy framework
- preferred/backup selection
- deterministic explanation/evidence
- HOLD: production Offer Scoring Model v1 formula

### P2-E3 Persistence — SQLITE VERIFIED / POSTGRESQL NEXT
- repository ports
- in-memory adapter
- SQLAlchemy SQLite adapter
- Alembic migration
- restart/idempotency
- PostgreSQL compatibility — NEXT
- additional concurrent selection/link acquisition — NEXT

### P2-E4 Worker/API Protocol — FOUNDATION VERIFIED
- worker command/result DTOs
- deterministic fake worker
- local atomic filesystem outbox
- account/product/platform context validation
- API observation/rank/selection contracts
- real schema-change/session-required browser classification — controlled-browser gate

### P2-E5 Export/Link Pipeline — CONTRACT FOUNDATION VERIFIED
- AffiliateLink contract
- OfferExportArtifact contract
- selected-link validation
- parser interface/profile evidence — NEXT
- golden real export fixtures — NEEDS_REAL_DATA

### P2-E6 Real Browser Evidence — NEEDS_REAL_DATA
- controlled Shopee evidence collection
- Offer identity validation
- account-context validation
- schema/selector profiles

## Program 3 Epics
### P3-E1 Publishing Domain — VERIFIED FOUNDATION
- PublishPlan
- PublishingLedger
- duplicate-policy engine
- Program2->Program3 DTO v1
- conservative reconciliation contract

### P3-E2 Scene Runtime Core — VERIFIED DETERMINISTIC LAB FOUNDATION
- SceneSignature
- recognizer
- transition validator
- bounded recovery engine
- headless action executor
- checkpoint behavior
- real Scene signatures — NEEDS_DEVICE_LAB

### P3-E3 Device Host Core — VERIFIED DOMAIN FOUNDATION / HOST RUNTIME NEXT
- device identity/status model
- device lease/ownership admission
- ADB unauthorized human gate
- resource pressure/admission model
- worker supervisor/process runtime — NEXT
- durable Device Registry repository — NEXT

### P3-E4 Worker/API Protocol — FOUNDATION VERIFIED / EXTENSION NEXT
- publishing worker event/outcome DTOs
- PublishPlan duplicate evaluation API
- publishing status API
- ambiguous outcome model
- durable worker event/checkpoint delivery — NEXT

### P3-E5 Fake Android E2E — VERIFIED ACTION-LOOP FOUNDATION / FULL WORKFLOW NEXT
- replaceable Android adapter ports
- scripted fake Android adapter
- fake scene snapshots
- Observe -> Recognize -> Validate -> Act -> Verify -> Checkpoint tested
- POST_OUTCOME_UNKNOWN reconciliation engine tested
- full multi-scene publish workflow simulation — NEXT

### P3-E6 Physical Device Lab — NEEDS_DEVICE_LAB
- ADB adapter spike
- uiautomator2 adapter spike
- real Scene inventory
- selector evidence
- Safe Anchor/recovery

### P3-E7 Scale/Observability — FOUNDATION RESOURCE POLICY / BENCHMARK GATED
- resource admission policy foundation
- screen-stream adapter benchmark — NEEDS_DEVICE_LAB
- 10/20/50/100-device benchmark — NEEDS_DEVICE_LAB
- endurance/recovery evidence — NEEDS_DEVICE_LAB

## Verified Vertical Slices
### Program 2
- P2-VS1 — Contract-driven Offer selection with fakes — DONE / VERIFIED
- P2-VS2 — SQLite durable Offer observations/selections — DONE / VERIFIED
- P2-VS3 — Worker protocol/outbox fake — DONE / VERIFIED
- P2-VS4A — Affiliate Link/export contracts + selection-link validation — DONE / VERIFIED

### Program 3
- P3-VS1 — PublishPlan + duplicate gate + PublishingLedger — DONE / VERIFIED
- P3-VS2 — Scene engine fixture-driven workflow — DONE / VERIFIED
- P3-VS3 — Device ownership/lease + resource admission with fake devices — DONE / VERIFIED
- P3-VS4A — scripted Android action loop + ambiguous-outcome reconciliation — DONE / VERIFIED

## Current READY / IN-DEV Queue
### Program 2
- P2-VS4B — parser port + synthetic fixture harness, then real golden fixtures when available
- P2-VS2B — PostgreSQL repository compatibility and concurrency contract
- P2-VS5 — controlled real-browser evidence spike

### Program 3
- P3-VS3B — durable Device Registry + Worker Supervisor contracts
- P3-VS4B — full scripted multi-scene publish workflow and event/checkpoint delivery
- P3-VS6 — controlled physical-device ADB/uiautomator2 spike
- P3-VS7 — capacity/endurance benchmark only after device-lab foundation

## Dependency Rules
- P2 and P3 domain/engines depend inward only.
- Program 3 may depend on Program 2 contracts, never Program 2 persistence implementation.
- Android/browser concrete adapters remain outer infrastructure.
- Shared Core owns cross-program job lifecycle and common envelopes.
- No domain imports FastAPI, SQLAlchemy, ADB, uiautomator2, Appium or scrcpy.

## Verification Gates Before DONE
Every slice requires:
1. governing document/contract alignment;
2. unit/property tests;
3. component/contract tests;
4. negative/idempotency/concurrency tests as applicable;
5. integration test when concrete persistence/adapter exists;
6. no unresolved CRITICAL/HIGH issue;
7. Problem/Lesson/CAPA update for meaningful defects;
8. CI evidence.

## Current Evidence
- Program 2/3 verification report: `PROGRAM2_PROGRAM3_VERIFICATION_REPORT_2026-08-31.md`.
- Problem/Lesson/CAPA record: `PROGRAM2_PROGRAM3_PROBLEM_LESSON_CAPA_2026-08-31.md`.
- GitHub Actions CI #155 passed Core, SQLite/Alembic and Stress gates for verified code head `4f33f3b74a5e11880922b928a7da0e383147fdb8`.

## Parallel Development Rule
Program 2 and Program 3 may proceed in parallel because contracts are versioned and fakes stand in for unfinished upstream/downstream components. A breaking handoff-contract change requires document/ADR update and compatibility tests before code changes merge.
