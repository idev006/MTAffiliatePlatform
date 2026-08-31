# Logical Architecture

## Architectural Style

The platform is organized as **three business domains plus one shared control plane**.

```text
                         ┌──────────────────────────┐
                         │   PYTHON CONTROL PLANE   │
                         │  Shared Core / Backoffice│
                         └─────────────┬────────────┘
                                       │
                  ┌────────────────────┼────────────────────┐
                  │                    │                    │
                  ▼                    ▼                    ▼
       Product Intelligence   Affiliate Offer Automation   Content Publishing
                  │                    │                    │
                  ▼                    ▼                    ▼
          Discovery Workers     Affiliate Workers      Publishing Workers
```

## Domain A — Product Intelligence
Responsibilities:
- ingest product observations
- normalize and deduplicate
- maintain historical snapshots
- score opportunities
- create explainable shortlists

Must not depend directly on one scraper/extension implementation.

## Domain B — Affiliate Offer Automation
Responsibilities:
- accept approved product candidates
- create offer-discovery jobs
- coordinate browser workers
- ingest platform exports/results
- rank and refresh multiple offers per product

Browser extension workers are **thin execution agents**.

## Domain C — Content Publishing
Responsibilities:
- video registry
- video fingerprints
- product/video/offer matching
- account/device allocation
- publishing job creation
- duplicate gates
- dispatch/recovery
- publishing ledger

Existing MTShopeeMobile implementation is treated as a candidate/reference Publishing Execution component, not the whole platform.

## Shared Core

### Control Plane
Python back office owns:
- rules
- job state
- worker registry
- decisions
- data contracts
- audit records
- monitoring
- analytics

### Worker Plane
Workers may be:
- browser extensions
- Android device workers
- future authorized API adapters
- import/file workers

Worker contract:
`receive job → execute bounded action → report observation/result`.

Workers must not become the source of truth.

## Core Services

```text
Backoffice
├── Product Catalog Service
├── Product Scoring Service
├── Offer Service
├── Video Registry Service
├── Fingerprint Service
├── Matching Service
├── Publishing Planner
├── Job Orchestrator
├── Worker Registry
├── Rules Engine
├── Audit Service
├── Analytics Service
└── Adapter Gateway
```

## API-as-Core
Component communication uses versioned business contracts. REST/HTTP is the baseline authoritative command/query surface; WebSocket is used for live telemetry/updates where useful. Durable business state remains in the central database and acknowledged delivery uses outbox/ACK semantics.

## Adapter Boundaries

### Product Source Adapter
Converts arbitrary product observations into the canonical ProductObservation contract.

### Affiliate Browser Adapter
Converts business commands such as `SEARCH_OFFERS` and `EXPORT_OFFERS` into the currently supported user-interface workflow.

### Publishing Adapter
Converts a validated PublishJob into an execution workflow for Android/browser/API target.

### Android Control Adapters
Device transport, UI automation, screen streaming and input control are separate replaceable adapters.

### Database / Repository Adapter
Domain/application services do not depend directly on SQLite/PostgreSQL-specific SQL. SQLAlchemy/Repository implementations provide persistence boundaries and Alembic governs schema migration.

### Analytics Adapter
Imports available post-performance data into the canonical PerformanceObservation contract.

## Communication
Business-level messages only. Avoid screen-coordinate commands as public contracts.

Examples:
- `DISCOVER_PRODUCTS`
- `SEARCH_AFFILIATE_OFFERS`
- `IMPORT_OFFER_EXPORT`
- `PUBLISH_VIDEO`
- `REPORT_JOB_RESULT`
- `HEARTBEAT`
- `SCENE_CHANGED`

## Worker Registration
Each worker reports:
- worker_id
- worker_type
- version
- capabilities
- status
- current_job_id
- last_heartbeat

Typical statuses:
`ONLINE_IDLE`, `BUSY`, `DEGRADED`, `OFFLINE`, `NEEDS_ATTENTION`.

## Orchestration Boundaries
- Back Office Orchestrator: global job/business orchestration.
- Device Host Manager: local Android device discovery, worker lifecycle and resource ownership.
- Worker Runtime: scene/process/action execution for one active Android device.

## Reliability Requirements

1. Job idempotency key.
2. Durable job state before execution.
3. Final duplicate check before publish dispatch.
4. Worker heartbeat and lease timeout.
5. Retry classification: retryable vs non-retryable vs needs-human.
6. Result acknowledgements.
7. Recovery after backoffice or worker restart.
8. Audit event for each important transition.
9. Short database transactions; never hold SQL transactions while waiting on external UI/network work.
10. Controlled degradation and admission control under resource pressure.

## Security / Compliance Boundary
Architecture must not require bypassing platform authentication, access controls, anti-bot controls, or rate limiting. Adapters are replaceable so permitted workflows can change without rewriting business logic.

## Scaling Model
Scale by adding workers/hosts, not duplicating business logic.

```text
Control Plane
   │
   ├── Discovery Worker 01..N
   ├── Affiliate Worker 01..N
   └── Device Host 01..N
          └── Android Worker 01..N
```

The initial target may be approximately 10 publishing devices, but the architecture must not hard-code that number.
