# API Communication and Plugin Architecture

Status: DEVELOPMENT HANDOFF BASELINE

## 1. Goal
Use API-as-core so Back Office, browser workers, device hosts, Android workers and future adapters can evolve independently while preserving versioned contracts and one business SSOT.

## 2. Communication Surfaces

### REST/HTTP — authoritative operations
Use for:
- worker enrollment/registration
- capability advertisement
- job lease/claim/renew/release
- observation/result batch submission
- ACK/checkpoint persistence
- administrative queries/commands
- configuration retrieval

### WebSocket — live telemetry, not authoritative state
Use for:
- worker/device online state
- live Scene/process telemetry
- dashboard updates
- bounded operator-control notifications
- fast health changes

A WebSocket disconnect must never imply a business job transition by itself.

### Durable Database — SSOT
Authoritative for:
- Product/Offer/Video identity/history
- jobs/job_events
- leases/checkpoints
- publishing ledger
- configuration/ruleset versions
- acknowledged results

### Local Outbox — delivery reliability
Each remote worker/host persists outbound facts before sending. Delete/mark delivered only after Back Office ACK.

## 3. API Versioning
Baseline path: `/api/v1/...`.

Messages include `schema_version` where payload evolution may occur. Breaking contract changes require a new API/schema version and compatibility plan.

## 4. Common Envelope
Conceptual fields:
- message_id
- schema_version
- emitted_at
- source_type
- source_id
- correlation_id
- job_id (nullable)
- sequence_no (where ordered delivery matters)
- payload

## 5. Worker Registration
Worker reports:
- worker_id
- worker_type
- installation_id
- machine_id/device_host_id when relevant
- version
- capabilities[]
- browser/app/runtime versions where relevant
- health/status

Worker ID is identity, not authentication.

## 6. Enrollment / Authentication
- one-time enrollment token may bootstrap worker credentials
- Back Office issues revocable worker credential
- secrets never live in canonical Product/Offer records
- credential rotation/revocation supported

## 7. Job Lease Contract
Shared Core `jobs` is lifecycle SSOT.

Baseline states:
`CREATED -> QUEUED -> LEASED/ASSIGNED -> IN_PROGRESS -> VERIFYING -> COMPLETED`

Alternative terminal outcomes:
`FAILED | NEEDS_HUMAN | CANCELLED | SKIPPED_DUPLICATE`

Lease fields:
- assigned_worker_id
- lease_token
- lease_until
- attempt_no
- job_version

No two valid active leases may exist for the same executable job.

## 8. Idempotency
All side-effecting commands/results use idempotency keys. Re-sending after timeout must not create a second logical job/result/post.

## 9. ACK and Sequence
Observation/result batches contain `batch_id` and sequence information. Back Office ACK is durable only after transaction commit. No ACK means sender retains data and may retry with same idempotency identity.

## 10. Heartbeat
Heartbeat communicates liveness/health, not durable job truth.

Candidate content:
- worker_id
- current_job_id
- status
- health metrics
- capabilities/effective version
- last successful external interaction

Exact interval is configuration/benchmark driven.

## 11. Plugin / Adapter Contract
Core application code depends on ports such as:
- ProductSourceAdapter
- AffiliateBrowserAdapter
- WorkerTransportAdapter
- DeviceTransportAdapter
- UIAutomationAdapter
- ScreenStreamAdapter
- InputControlAdapter
- AnalyticsAdapter
- NotificationAdapter

Adapters translate business-level operations to tool/platform-specific implementation details.

## 12. Error Contract
Errors are classified:
- RETRYABLE
- NON_RETRYABLE
- SESSION_REQUIRED
- SCHEMA_CHANGED
- RESOURCE_EXHAUSTED
- CONFLICT
- NEEDS_HUMAN
- OUTCOME_UNKNOWN

Error records include code, safe message, component, correlation/job IDs, retryability, evidence reference and adapter/version metadata.

## 13. Backpressure
Back Office and Device Host Manager may reject/defer new work when resource budgets or queue/outbox high-watermarks are exceeded. Workers must pause admission rather than grow unbounded memory/disk usage.

## 14. Security Boundary
Do not design contracts around bypassing authentication, CAPTCHA, access control, anti-abuse or platform safeguards. Session-required states are explicit and may require operator intervention.
