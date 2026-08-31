# Program 2 + Program 3 Implementation Kanban

Status: ACTIVE IMPLEMENTATION PLAN
Date: 2026-08-31

## Delivery Principle
Both programs are developed as independent bounded capabilities over Shared Core, but integration is proven continuously through versioned handoff contracts.

No team waits for full Program 2 completion before Program 3 foundation work begins. Fake/contract-driven vertical slices allow safe parallel development.

## Program 2 Epics
### P2-E1 Domain & Contract Foundation
- Offer identity/value objects
- OfferObservation
- AffiliateAccountContext
- eligibility/ranking/selection contracts
- Program1->Program2 DTO v1

### P2-E2 Offer Intelligence Engine
- eligibility engine
- configurable scoring policy
- preferred/backup selection
- deterministic explanation/evidence

### P2-E3 Persistence
- repository ports
- in-memory adapter
- SQLAlchemy SQLite adapter
- Alembic migration
- restart/idempotency/concurrency
- PostgreSQL compatibility

### P2-E4 Worker/API Protocol
- worker capabilities
- job/result DTOs
- outbox/ACK semantics
- schema-change/session-required classification

### P2-E5 Export/Link Pipeline
- artifact registry
- parser interface
- golden fixtures
- link validation/freshness

### P2-E6 Real Browser Evidence
- controlled Shopee evidence collection
- Offer identity validation
- account-context validation
- schema/selector profiles

## Program 3 Epics
### P3-E1 Publishing Domain
- PublishPlan
- VideoIdentity
- PublishingLedger
- duplicate-policy engine
- Program2->Program3 DTO v1

### P3-E2 Scene Runtime Core
- Scene/Process/Action models
- SceneSignature
- recognizer
- transition validator
- recovery engine
- checkpoint model

### P3-E3 Device Host Core
- device registry
- device lease/ownership
- worker supervisor
- resource admission
- health/state model

### P3-E4 Worker/API Protocol
- job/event DTOs
- idempotency
- checkpoint/event delivery
- ambiguous outcome model

### P3-E5 Fake Android E2E
- fake device adapter
- fake UI automation adapter
- fake scene snapshots
- full publish workflow simulation
- POST_OUTCOME_UNKNOWN reconciliation

### P3-E6 Physical Device Lab
- ADB adapter spike
- uiautomator2 adapter spike
- real Scene inventory
- selector evidence
- Safe Anchor/recovery

### P3-E7 Scale/Observability
- screen-stream adapter benchmark
- resource budgets
- 10/20/50/100-device benchmark
- endurance/recovery evidence

## Initial READY Queue
### Program 2
P2-VS1 — Contract-driven Offer selection with fakes
P2-VS2 — SQLite durable Offer observations/selections
P2-VS3 — Worker protocol/outbox fake

### Program 3
P3-VS1 — PublishPlan + duplicate gate + PublishingLedger with fake worker
P3-VS2 — Scene engine fixture-driven workflow
P3-VS3 — Device ownership/lease with fake devices

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

## Parallel Development Rule
Program 2 and Program 3 may proceed in parallel because contracts are versioned and fakes stand in for unfinished upstream/downstream components. A breaking handoff-contract change requires document/ADR update and compatibility tests before code changes merge.
