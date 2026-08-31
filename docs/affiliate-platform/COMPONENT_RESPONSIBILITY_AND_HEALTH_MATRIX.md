# Component Responsibility and Health Matrix

Status: IMPLEMENTATION HANDOFF BASELINE
Date: 2026-08-31

## 1. Purpose

This matrix makes division of labor explicit across MTAffiliatePlatform. It complements `SYSTEM_PHYSIOLOGY_MODEL.md` by defining for each major component its responsibility, inputs/outputs, authority, health sensing and recovery boundary.

## 2. Core Matrix

| Component | Primary responsibility | Inputs | Outputs | Durable authority | Health / detection | Recovery / containment |
|---|---|---|---|---|---|---|
| Back Office / Control Plane | Global coordination and business control | operator intent, rules, worker facts, DB state | commands, plans, state transitions | business orchestration | API health, queue age, error rates, DB availability | restart from DB state, reject/defer work, fail closed |
| Shared Job Engine | job lifecycle, lease, retry classification | job command, worker claim/result | lease, state transition, checkpoint | `jobs` / `job_events` lifecycle | lease age, stale jobs, retry/error trends | lease expiry, checkpoint resume, safe requeue |
| Product Intelligence Engine | qualification/scoring/ranking | canonical observations, ruleset | scores, reasons, shortlist | product scoring decision records | missing features, stale data, model/rules version | reject/defer score, recompute with valid ruleset |
| Affiliate Offer Engine | offer eligibility/freshness/ranking | offer observations, account context, rules | preferred/backup decisions | offer selection decisions | freshness, data completeness, session provenance | refresh, reject stale offer, re-discovery |
| Content Identity Engine | video identity/duplicate classification | media metadata/hash/fingerprint | duplicate status/evidence | content identity records | metadata/fingerprint failure | exact-hash fallback, quarantine/review where ambiguous |
| Publishing Engine | publish-plan validation, guards, reconciliation | plan, product/offer/video/account state | approved/rejected job, reconciliation decision | publishing policy + ledger transition decision | freshness/duplicate/evidence status | block, reconcile, `NEEDS_HUMAN` |
| Device Host Manager | local device/resource orchestration | Back Office commands, device discovery, host resources | worker assignment, host/device health | device-host operational ownership | CPU/RAM/disk/USB/outbox/device state | throttle, drain, restart worker, quarantine device |
| Resource Manager | admission/backpressure/degradation | resource metrics, active workload | admit/defer/throttle decisions | local resource admission | thresholds/trends/high-watermarks | stop admission, degrade stream, drain workload |
| Worker Supervisor | worker process lifecycle | device assignment, job eligibility | spawned/restarted worker, process health | worker process lifecycle | PID/process exit/heartbeat | restart isolated worker, quarantine repeated failure |
| Browser Discovery Worker | collect product observations | discovery job, page/session | ProductObservation batches | none globally; local outbox only | parser success, page support, outbox depth | retry send, pause, `PAGE_CHANGED`, human/session required |
| Affiliate Browser Worker | collect/execute offer workflow | offer job, affiliate session | offer observations/export facts | none globally; local outbox only | page/session/export health | pause, retry safe step, schema/session escalation |
| Android Worker Runtime | execute one bounded device job | leased publish job, current device/UI state | scene/checkpoint/result events | volatile execution state only | heartbeat, scene confidence, action failures | scene recovery, checkpoint, controlled restart, escalate |
| Scene Engine | recognize scene and control scene/process transitions | UI observation, workflow definition | scene classification, permitted process/recovery | no global durable authority | confidence, mismatch, unknown schema | re-observe, local/anchor recovery, quarantine selector profile |
| UI Automation Adapter | translate logical elements/actions to Android | logical action/element | atomic UI effect + observation | none | selector resolution, action/verification errors | alternate selector, `SCHEMA_CHANGED`, fail closed |
| Device Transport Adapter | Android transport/control | device command | transport result | none | ADB/device connectivity | reconnect, rebind, device unhealthy |
| Screen Stream Adapter | operator visibility / stream | device stream request | video stream | none | fps/latency/decoder state | lower quality, reconnect, disable stream without stopping job |
| FastAPI Boundary | external/internal API contract | HTTP/WS requests | validated commands/queries/telemetry | none independently | request latency, auth/schema errors | reject invalid calls, reconnect WS, application-level retry |
| Repository / UnitOfWork | persistence abstraction and transaction boundary | semantic repository calls | durable commit/read | DB mutation through approved transactions | DB errors/conflicts/migration state | bounded retry, rollback, surface conflict |
| SQLite/PostgreSQL | canonical durable state | transactional writes | committed data | durable SSOT | availability, lock/conflict/storage pressure | DB recovery/backup/migration procedures |
| Local Outbox | reliable worker-to-control delivery | worker facts/results | retryable outbound messages | local acknowledged-delivery state | queue depth, age, disk quota | resend same idempotency, pause collection before overflow |
| Audit / Telemetry | traceability and operational evidence | events/metrics/logs | queryable diagnostics | append-oriented audit facts where designated | ingestion lag/drop rate | buffer/degrade noncritical telemetry, never hide critical state |
| Optional UI / CLI | operator presentation/input | read models, commands | application command/query | none | presentation/API connectivity | reconnect/refresh; UI failure must not corrupt engine state |

## 3. RACI-Like Authority Matrix

Legend: **A** authoritative owner, **R** responsible executor, **C** consulted/input, **O** observes only.

| Capability | Back Office | Engine | Device Host | Worker | Adapter | DB | UI |
|---|---:|---:|---:|---:|---:|---:|---:|
| Product/offer commercial decision | A | R |  | C | C | O | C |
| Job lifecycle | A | R | C | C |  | O | O |
| Device ownership/admission | C |  | A/R | C | C | O | O |
| Scene/process execution | C | A/R (Scene Engine in Worker) | C | R | C | O | O |
| Android atomic interaction |  | C | C | R | A/R technology execution |  | O |
| Durable canonical state | C | C |  |  |  | A/R storage | O |
| Publishing duplicate policy | A | R |  | C |  | O | C |
| Worker process lifecycle | C |  | A | R |  | O | O |
| Human override | A | C | C | C |  | O | R input |

No row should have two independent `A` authorities.

## 4. Input / Process / Output Review Template

For every new component or engine, the design document must contain:

```text
Component:
Purpose:
Owner:

INPUT
- command/event/data:
- source:
- schema/version:
- preconditions:

PROCESS
- responsibilities:
- decisions allowed:
- decisions prohibited:
- state machine/ruleset:

OUTPUT
- result/event/effect:
- destination:
- durable ACK point:

HEALTH
- signals:
- thresholds/policy owner:

FAILURE
- retryable:
- non-retryable:
- ambiguous:

RECOVERY
- local recovery:
- checkpoint/resume:
- quarantine/failover:
- human escalation:

TEST
- fake/test double:
- contract tests:
- resilience scenarios:
```

## 5. Conflict Prevention Review

Before coding a component, reviewers must ask:
- Does another component already own this decision?
- Can two workers act on the same durable entity concurrently?
- Is there one active lease/ownership token?
- Can stale data overwrite newer state?
- Can retries duplicate an external side effect?
- Can resource pressure create unbounded queues?
- Can a UI/adapter failure mutate business truth incorrectly?
- Can an unhealthy component be isolated without taking down unrelated work?

## 6. Resource Ownership Matrix

| Resource | Owner | Consumers | Conflict control |
|---|---|---|---|
| Job lease | Shared Job Engine | workers | lease token + version + expiry |
| Android device | Device Host Manager | one active Android Worker | device lock/binding |
| Worker process | Worker Supervisor | Device Host | process registry/heartbeat |
| Affiliate session context | authorized session/worker context, referenced centrally | Offer workflow | explicit provenance + eligibility |
| Video publish eligibility | Publishing Engine / Ledger | publish jobs | duplicate/readiness gates + DB invariant |
| DB write transaction | Application/Repository UoW | engines/use cases | short TX + optimistic concurrency |
| USB bandwidth | Device Host Resource Manager | device/stream adapters | budget/admission/degradation |
| Screen stream slots | Stream Manager / Host Resource Manager | operator UI | quality tiers + slot limits |
| Local disk/outbox | host/worker resource policy | workers/logging | quotas + high-watermarks |

## 7. Review Outcome

Current architecture has clear top-level ownership for the major domains and execution layers. The remaining production-gated areas are not ownership defects; they are real-world validation gaps such as exact scoring formulas, real Shopee Scene signatures/selectors, fingerprint thresholds and capacity benchmarks.

Any future component that cannot be placed cleanly in this matrix must undergo architecture review before implementation.
