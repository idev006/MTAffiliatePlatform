# Development Handoff Master — Affiliate Platform

Date: 2026-08-30
Status: DEVELOPMENT HANDOFF BASELINE
Implementation authority: governed by `ENGINEERING_GOVERNANCE.md`

## 1. Governing Principle

**Project must follow the document.**

This repository is the SSOT for requirements, architecture, workflow, contracts, state models, database rules, deployment rules, test expectations and implementation decisions.

Priority of authority:
1. `PROJECT_CHARTER.md`
2. `WORKFLOW.md`
3. `ARCHITECTURE.md`
4. `ENGINEERING_GOVERNANCE.md`
5. accepted ADRs / `DECISION_LOG.md`
6. Step baselines and handoff contracts
7. domain specifications
8. data/API schemas
9. implementation source code

If code and an approved document disagree, the code is non-conforming until the discrepancy is intentionally resolved.

## 2. Reviewed Scope

### Step 1 — Product Discovery / Product Intelligence
Accepted design direction:
- distributed browser-worker farm
- Back Office owns planning, sharding, job leasing, checkpoints and canonical deduplication
- browser extension workers collect observations only
- observations are historical/append-oriented
- Product scoring remains centrally owned and explainable

### Step 2 — Affiliate Offer Automation
Accepted design direction:
- distributed affiliate-worker farm using the same Shared Core worker platform
- Product 1:N Offers
- affiliate account/session provenance is mandatory where offer facts depend on account context
- Back Office owns filters, ranking, preferred/backup selection and freshness
- Shared Core `jobs` is the sole lifecycle SSOT

### Step 3 — Content Publishing / Android Device Farm
Accepted design direction:
- Python Back Office is the Control Plane
- Device Host Manager owns local device lifecycle/resources
- one active Worker Runtime controls one Android device
- Worker is Scene-aware: `Observe -> Recognize -> Validate -> Act -> Verify -> Checkpoint`
- logical Scene/Process/Action/Element contracts are separated from Android selectors
- Screen streaming is observability/operator control, not business SSOT
- publish result ambiguity must never trigger blind repost
- global Publishing Ledger enforces duplicate policy

## 3. Platform Architecture

```text
                         PYTHON BACK OFFICE / CONTROL PLANE
                                      |
             +------------------------+------------------------+
             |                        |                        |
             v                        v                        v
     STEP 1 DOMAIN             STEP 2 DOMAIN             STEP 3 DOMAIN
 Product Intelligence       Affiliate Offers          Content Publishing
             |                        |                        |
             v                        v                        v
 Browser Workers            Browser Workers          Device Host Managers
                                                           |
                                                     Android Workers
                                                           |
                                                     Android Devices
                                                           |
                                                      Shopee App
```

Shared Core owns:
- API gateway / worker API
- rules and configuration
- job orchestration
- worker/device registry
- leases and idempotency
- database transactions
- audit/event history
- health/observability
- adapter/plugin registry

## 4. API-as-Core Rule

All major components communicate through versioned business-level contracts.

Public component boundaries must not expose brittle implementation details such as DOM paths, Android coordinates or internal ORM objects.

Baseline communication surfaces:
- REST/HTTP for commands, queries, registration, lease/ACK and administrative APIs
- WebSocket for live worker/device state, scene telemetry, operator dashboard updates and bounded control notifications
- durable database state for authoritative job/business status
- local outbox for worker-side acknowledged delivery

Message examples:
- `DISCOVER_PRODUCTS`
- `SEARCH_AFFILIATE_OFFERS`
- `PUBLISH_VIDEO`
- `HEARTBEAT`
- `JOB_CHECKPOINT`
- `JOB_RESULT`
- `SCENE_CHANGED`
- `NEEDS_HUMAN`

## 5. Component-Based / Pluggable Rule

Core business services depend on interfaces/ports, not concrete tools.

Required replaceable adapter families:
- ProductSourceAdapter
- AffiliateBrowserAdapter
- DatabaseAdapter / Repository implementations
- WorkerTransportAdapter
- DeviceTransportAdapter
- UIAutomationAdapter
- ScreenStreamAdapter
- InputControlAdapter
- AnalyticsAdapter
- NotificationAdapter

A tool replacement must not require rewriting product/offer/publishing business policy.

## 6. Runtime Ownership

| Resource | Authoritative owner |
|---|---|
| Business rules | Back Office |
| Job lifecycle | Shared Core Job Orchestrator |
| Product identity/history | Back Office DB |
| Offer identity/history | Back Office DB |
| Video identity/fingerprint | Back Office DB |
| Publishing ledger | Back Office DB |
| Device discovery/lifecycle | Device Host Manager |
| Worker process lifecycle | Worker Supervisor on Device Host |
| Scene execution state | Worker Runtime, reported to Back Office |
| Android selector profile | UI Automation Adapter registry |
| Screen-stream lifecycle | Screen Stream Manager |

No resource may have two independent lifecycle authorities.

## 7. Reliability Invariants

1. One active lease per executable Job.
2. One active automation Worker per Android Device.
3. A Worker cannot mutate canonical business tables directly; it reports facts/results through API contracts.
4. All destructive/irreversible actions require idempotency and post-action reconciliation rules.
5. No open SQL transaction may wait on browser/mobile/UI/network work.
6. Every acknowledged observation/result must survive process restart.
7. Unknown publish outcome becomes reconciliation/`NEEDS_HUMAN`, never blind retry.
8. Duplicate prevention is enforced both in application gates and database constraints where portable across supported engines.
9. Worker/Host failure must be isolated from unrelated workers.
10. System overload causes controlled degradation/admission throttling rather than whole-farm collapse.

## 8. Deployment Modes

### Portable Mode — default distribution target
- one Windows PC
- Back Office + Device Host Manager on same machine
- SQLite local central DB
- worker processes spawned locally
- bundled ADB/screen-stream dependencies where licensing permits
- packaged application distribution

### Farm Mode
- one logical Back Office
- PostgreSQL central DB
- multiple Device Hosts and browser-worker PCs
- same contracts and business services
- no redesign of domain logic

## 9. Development Package Index

Development team must read:
- `DEVELOPMENT_HANDOFF_MASTER.md`
- `SYSTEM_DIAGRAMS.md`
- `TECHNOLOGY_STACK.md`
- `API_COMMUNICATION_AND_PLUGIN_ARCHITECTURE.md`
- `DATABASE_CONCURRENCY_AND_PORTABILITY_SPEC.md`
- `AGILE_KANBAN_IMPLEMENTATION_PLAN.md`
- three Step baseline documents
- domain specs under `specs/`
- `DECISION_LOG.md`

## 10. Implementation Readiness Classification

The architecture is ready for development handoff and foundation implementation.

However, feature slices remain governed by per-component Definition of Ready. The following are validation gates before production feature completion, not permission to ignore them:
- Product Scoring Model v1 exact formula
- Offer Scoring Model v1 exact formula
- product/offer identity validation on real Shopee observations
- Step1 -> Step2 and Step2 -> Step3 final schema contracts
- real Shopee Android Scene inventory/signatures/selectors
- screen-stream/device-host capacity benchmark
- video fingerprint threshold validation
- post-submit reconciliation validation

No CRITICAL/HIGH unresolved issue may enter the implementation of the affected feature.

## 11. Development Strategy

Use vertical slices rather than implementing all infrastructure first.

Recommended order:
1. Shared Core foundation + API + storage + migration
2. Worker registration/heartbeat/job lease reference slice
3. Step 1 end-to-end thin slice
4. Step 2 end-to-end thin slice
5. Device Host + one Android Worker laboratory slice
6. Step 3 Scene Engine + controlled test app
7. Shopee Scene catalog/adapter validation
8. Publishing happy path with human gate
9. recovery/failure injection
10. multi-device scaling
11. analytics/learning loop

Every slice must include tests, telemetry, audit events and documentation conformance.
