# Agile Kanban Implementation Plan

Status: DEVELOPMENT HANDOFF BASELINE

## Delivery Model
Document-driven Agile Kanban. Work moves only when the governing contracts for that slice are ready.

## Board
`BACKLOG -> ANALYSIS -> DESIGN/CONTRACT -> READY -> IN DEV -> CODE REVIEW -> VERIFY -> DONE`

Blocked work is visibly marked `BLOCKED` with blocker owner/reason; it must not be hidden inside IN DEV.

## Definition of Ready
A card may enter READY only when applicable items pass:
- objective/input/output/acceptance criteria defined
- governing SSOT docs identified
- API/data/state contracts defined
- owner and component boundary clear
- error/recovery semantics defined
- security/compliance considerations reviewed
- test cases identified
- dependencies resolved or explicitly stubbed
- unresolved CRITICAL/HIGH design issues = 0 for that slice

## Definition of Done
- code conforms to governing documents
- automated tests pass
- contract/migration tests pass when applicable
- telemetry/audit added for important state transitions
- negative/recovery tests pass
- docs/ADR updated for any material change
- no secrets/test data committed
- reviewer confirms acceptance criteria

## WIP Policy
Prefer low WIP and complete vertical slices. Suggested initial WIP:
- ANALYSIS: 3
- DESIGN/CONTRACT: 3
- IN DEV: 3
- CODE REVIEW: 2
- VERIFY: 2

Adjust from measured cycle time, not intuition.

## Epics
### E0 — Repository / Engineering Foundation
- project skeleton
- CI/lint/test baseline
- configuration model
- logging/correlation
- packaging skeleton

### E1 — Shared Core
- FastAPI API core
- SQLAlchemy repositories
- Alembic migrations
- Worker Registry
- Job lifecycle/leasing
- idempotency
- audit/job events
- outbox/ACK

### E2 — Step 1 Product Discovery
- browser worker enrollment
- campaign/shard/job contracts
- observation ingestion
- canonical product normalization/dedupe
- scoring interface and shortlist

### E3 — Step 2 Affiliate Offers
- offer campaign/jobs
- account/session provenance
- candidate observations
- ranking/filter interfaces
- selection/export/import
- freshness

### E4 — Step 3 Device Host Foundation
- ADB device registry
- Device Host Manager
- worker process supervisor
- resource/admission manager
- health/heartbeat
- screen stream adapter interface

### E5 — Step 3 Scene Runtime
- Scene registry/signatures
- Scene recognizer
- process/action executor
- logical element resolver
- selector profiles
- transition verification
- recovery engine

### E6 — Publishing
- video registry/fingerprint
- product/video/offer matching
- duplicate gate
- publishing planner
- Shopee happy path
- post-submit reconciliation
- Publishing Ledger

### E7 — Scale / Reliability
- failure injection
- 10-device benchmark
- multi-host test
- resource budgets
- endurance 8h/24h/72h progression

### E8 — Analytics / Learning Loop
- performance observations
- attribution
- feedback to Product/Offer scoring

## First Development Queue
1. Repo/application skeleton and CI.
2. Shared contract package (Pydantic DTOs/versioning).
3. Storage abstraction + SQLite + Alembic reference migration.
4. Job + Worker Registry reference slice.
5. Heartbeat/lease/outbox idempotency tests.
6. Step 1 thin slice.
7. Step 2 thin slice.
8. Device Host laboratory slice with one Android device.
9. Scene engine against a controlled test app.
10. Real Shopee Scene discovery/validation spike.

## Spike Policy
Use time-boxed validation cards for unknowns that could invalidate design, including:
- product/offer identity
- scoring formulas
- Shopee Scene/selector stability
- screen-stream capacity
- video fingerprint thresholds
- post-submit reconciliation

Spike output must be evidence + decision + doc/ADR update, not production code disguised as research.

## Change Control
Material design change flow:
`Issue -> governing document -> ADR/contract update -> review gate -> implementation -> conformance verify`.
