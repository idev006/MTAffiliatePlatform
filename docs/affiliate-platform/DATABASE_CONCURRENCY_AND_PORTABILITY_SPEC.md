# Database Concurrency and Portability Specification

Status: DEVELOPMENT HANDOFF BASELINE

## 1. Goal
Provide correctness under concurrent workers while remaining portable for distribution and scalable to farm deployment.

## 2. Persistence Stack
- SQLAlchemy 2.x ORM/Core
- Repository Pattern
- Alembic migrations
- SQLite: Tier-1 Portable Mode
- PostgreSQL: Tier-1 Farm/Server Mode

Application/domain logic must not depend directly on one database vendor.

## 3. Ownership Rule
Workers do not directly mutate canonical business tables.

`Worker -> API event/result -> Application Service -> Transaction -> Repository -> SQLAlchemy -> DB`

This gives one logical authority for business transitions.

## 4. Transaction Boundary
Transactions must be short and must never remain open while waiting for:
- Shopee page/app interaction
- browser navigation
- Android UI
- network upload
- human input
- external file generation/download

Pattern:
`BEGIN -> validate/lock/update -> COMMIT`, then external work, then another short transaction.

## 5. Concurrency Risks
Design explicitly handles:
- deadlock
- lock contention
- lost update
- race condition
- duplicate execution
- stale reads/state
- partial transaction
- worker/host crash mid-operation
- two workers targeting same logical resource
- DB write bottleneck

## 6. Optimistic Concurrency
Critical mutable rows should carry a revision/version where useful.

Conceptual update:
`UPDATE ... WHERE id=? AND version=?`

Zero affected rows means concurrent modification and must be reconciled, not silently overwritten.

## 7. Job Leasing
Shared Core `jobs` is lifecycle SSOT. Job claim/lease must be atomic. Lease expiry does not automatically mean an irreversible external action did not happen; reconciliation rules apply.

## 8. Idempotency
Side-effecting operations have stable idempotency keys. Duplicate requests/results must return/reconcile the prior logical result rather than create a new effect.

## 9. Database Constraints
Use portable constraints wherever possible for business invariants:
- natural/canonical identity uniqueness
- one logical batch/sequence identity
- publishing ledger duplicate protection
- valid foreign-key relationships

Where PostgreSQL supports stronger vendor features than SQLite, implement equivalent application-level invariant plus compatibility tests rather than hiding semantic differences.

## 10. Publishing Atomicity
Confirmed publish registration should atomically:
- validate job ownership/state
- insert/update publishing ledger
- set platform/video publish state
- complete/transition the publish job
- append audit/job event

An unknown outcome after external submit is never treated as ordinary retryable failure.

## 11. SQLite Portable Mode
Guidelines:
- one logical Back Office owns canonical DB writes
- WAL mode candidate/default after validation
- short transactions
- controlled busy timeout/retry
- batch high-frequency telemetry
- keep stream/frame data out of operational SQL tables
- bound logs/events/outbox retention

SQLite is not expected to coordinate direct writes from many independent worker processes.

## 12. PostgreSQL Farm Mode
Use when workload grows across multiple hosts or higher write concurrency requires server-grade locking/concurrency. Domain/services/contracts remain unchanged.

## 13. Alembic
- every released schema has an Alembic revision
- upgrade path from supported previous releases is tested
- SQLite batch migration behavior is tested
- migration code must be reviewed against all Tier-1 DB engines
- app startup must detect incompatible/newer schema revisions safely
- backup/recovery guidance is required before destructive migration

## 14. Deadlock / Serialization Retry
When the DB engine reports a retryable concurrency failure:
- rollback the whole transaction
- apply bounded retry/backoff
- re-read current state
- re-run invariant checks
- never replay an external destructive action merely because DB commit status was uncertain

## 15. Testing Gate
Before implementation-ready for affected slices:
- concurrent job claim test
- optimistic update conflict test
- duplicate result/idempotency test
- crash before/after ACK test
- deadlock/lock contention injection where engine supports it
- SQLite busy/load test
- PostgreSQL concurrent writer test
- migration upgrade test on both Tier-1 engines
- publish-ledger duplicate race test
