# Job Lease / Pause / Resume Protocol Specification

Status: DESIGN — READY FOR REVIEW (implementation pending DoR/DoD gates)
Date: 2026-09-04
Owner Domain: Shared Core / Control Plane
Builds on: `SHARED_CORE_SPEC.md` (§5–§13), `API_COMMUNICATION_AND_PLUGIN_ARCHITECTURE.md` (§7–§13), `APPLICATION_AND_ENGINE_CONTRACTS.md` (§6 Shared Job Engine Contracts), `DATA_MODEL.md` (`jobs` / `job_events` / `job_checkpoints`, §10–§12), and the implemented worker-registry slice (migration `0003_shared_core_workers`).

> Governing precedence: where this document conflicts with the newer engine-first governing documents named above, those documents win and this spec must be updated before implementation.

## 1. Purpose and scope

Define the protocol by which the Shared Core dispatches **executable jobs to registered workers under a lease**, and how workers and operators **pause and resume** jobs and worker admission — without duplicating queue/lease authority inside domain tables and without treating heartbeats or UI state as durable job truth.

This slice completes the Shared Job Engine foundations on top of the existing registry:

- registry exists: `register`, `heartbeat`, `workers` table, health vocabulary `ONLINE_IDLE | ONLINE_BUSY | DEGRADED | OFFLINE | DISABLED`, migration `0003`;
- this protocol adds: `jobs` / `job_events` / `job_checkpoints` persistence, the lease state machine, dispatcher claim, pause/resume of jobs and of worker admission.

In scope: protocol, state machine, persistence deltas, REST contracts, engine behavior, tests.
Out of scope (owned by domain engines): domain payload semantics, retry/duplicate *policy*, publishing irreversibility rules. Domain engines supply those as **job-class policy** the engine applies.

## 2. Terminology

- **Lease** — exclusive right to execute one job, expressed as `lease_token` + `lease_until` on the `jobs` row. One executable job has at most one valid active lease.
- **Claim** — the transaction where a worker takes the next eligible job and receives a fresh lease.
- **Renewal** — extending `lease_until`; happens in the same short transaction as a job-context heartbeat (or an explicit renew call), only when token/version match.
- **Expiry / reclaim** — `lease_until < now` with no renewal; engine transitions the job per job-class policy (safe requeue, or `NEEDS_HUMAN` for outcome-unknown classes).
- **Checkpoint** — durable, worker-written execution state (`job_checkpoints`) that a later execution attempt replays from; never the DB cursor of an open transaction.
- **Admission pause (worker)** — a paused worker stops *claiming new jobs*; its current job continues to completion or checkpoint.
- **Job pause** — an operator- or worker-initiated quiescent stop of one job: the worker completes its current safe unit, checkpoints, releases the lease; resume re-queues from the checkpoint.
- **Resume** — clearing a pause so the worker or job becomes claim-eligible again.

## 3. Where authority sits

- Control plane (Back Office): decides what job runs, priority, ruleset, retry/duplicate classification, lease policy, pause/resume eligibility.
- Worker (execution plane): reports heartbeat, capabilities, current job context, observations, checkpoints, results/errors. A worker never decides durable job state on its own — it *requests* transitions the engine validates.
- Database: SSOT for jobs, leases, checkpoints, events, registry. Browser/device memory and UI are caches only.

Engine rule: the lease/state-machine engine and its decisions **must not depend on FastAPI, SQLAlchemy, or concrete transports** (SHARED_CORE_SPEC §15). FastAPI routes, SQLAlchemy repos and worker transport adapters wrap the same engine.

## 4. Persistence deltas (migration `0004_shared_core_jobs`)

Tables exactly per `DATA_MODEL.md`:

`jobs`
- `job_id`, `job_type`, `domain`, `state`, `priority`, `payload`/`payload_ref`, `idempotency_key` (nullable), `assigned_worker_id` (nullable), `lease_token` (nullable), `lease_until` (nullable), `attempt_no`, `job_version`, `created_at`, `started_at`, `completed_at`, `failure`/`error_ref` (nullable), `not_before` (nullable), `max_attempts`, `job_class_policy_ref` (nullable).
- Partial unique index on `idempotency_key` where not null (CreateJob invariant).
- Index for claim eligibility: `(state, priority, not_before)`; index for expiry scan: `(state, lease_until)` where `state` in lease-holding states; index for registry join: `(assigned_worker_id)` where lease-holding.

`job_events`
- `event_id`, `job_id`, `event_type`, `sequence`, `source`, `payload`/`evidence_ref`, `emitted_at`, `committed_at`; unique `(job_id, sequence)`.
- Append-only; every state transition and pause/resume/expiry writes an event.

`job_checkpoints`
- `checkpoint_id`, `job_id`, `checkpoint_type`, `checkpoint_payload`/`ref`, `worker_id`, `job_version`, `created_at`.
- Append-only; the latest checkpoint per job is returned on the next claim.

`workers` (alter)
- add `admission_paused` boolean NOT NULL DEFAULT 0, `admission_paused_at` (nullable), `admission_pause_reason` (nullable).
- Health vocabulary is **unchanged** — pause is an admission flag plus events, not a new health state. Observability derives "PAUSED" from the flag.

No worker column for "current job": the active lease join on `jobs(assigned_worker_id)` is authoritative and stays in one place.

## 5. Job state machine

Baseline (API §7) plus the quiescent `PAUSED` state:

```text
            +-------------------------+
            v                         |
CREATED -> QUEUED -> LEASED -> IN_PROGRESS -> VERIFYING -> COMPLETED
             |  ^        |          |              |
             |  |        |          +--(checkpoint)-> PAUSED --(resume)-----+
             |  |        +--(lease expired; class policy)                   |
             |  |              |                                            |
             |  +--------------+  (idempotent-safe class -> QUEUED)         |
             |                 |                                            |
             +- CANCELLED      +-- (outcome-unknown class -> NEEDS_HUMAN)   |
                                                          ^                 |
                                                          +-----------------+
Terminal: COMPLETED | FAILED | NEEDS_HUMAN | CANCELLED | SKIPPED_DUPLICATE
```

Transition notes (all validated by the engine; repository adapters never skip validation):
- `QUEUED -> LEASED`: the only worker-initiated entry. Conditional UPDATE wins exactly one claim.
- `LEASED -> IN_PROGRESS`: first heartbeat carrying the job context for that lease.
- `IN_PROGRESS/VERIFYING -> PAUSED`: requires the current lease token; the worker must have recorded a final checkpoint first (operator pause may request the worker to do this via the running lease — see §7).
- `PAUSED -> QUEUED`: resume. `attempt_no` is preserved between pause and resume; a later claim increments it, so each claim is one attempt against the attempt budget.
- Lease expiry transition depends on `job_class_policy`: `idempotent-safe` (e.g. discovery collection, observation capture) → `QUEUED` with a `LEASE_EXPIRED` event; anything whose outcome may be unknown after disappearance (publishing after an irreversible boundary, per class policy) → `NEEDS_HUMAN` with `LEASE_EXPIRED` + `OUTCOME_UNKNOWN`. Never silently retry a potentially completed publish (SHARED_CORE_SPEC §11).

## 6. Lease protocol

### 6.1 Claim (`LeaseJob`)

Worker → `POST /api/v1/jobs/claim`

Request (schema `job-claim-v1`):
```json
{
  "worker_id": "w00001",
  "worker_type": "DISCOVERY_BROWSER_WORKER",
  "capabilities": ["collector:shopee-current-page-lab-v2"],
  "lease_duration_seconds": 60,
  "idempotency_key": null
}
```

Engine behavior in **one short transaction**:
1. Registry guard: worker exists, `health_state != DISABLED`, `admission_paused = false`. Registry row `last_seen_at` refreshes and `health_state` becomes `ONLINE_BUSY` in the same transaction.
2. Select the highest-priority eligible job (`QUEUED`, `not_before <= now`, capability requirements ⊆ worker capabilities, class max_attempts not exceeded).
3. Conditional UPDATE `jobs SET state='LEASED', assigned_worker_id=?, lease_token=<uuid>, lease_until=now+?, attempt_no=attempt_no+1, job_version=job_version+1, started_at=COALESCE(started_at,now) WHERE job_id=? AND state='QUEUED'`. Rowcount 1 = won.
4. Append `job_events` `CLAIMED`; read latest checkpoint.

Responses:
- `200` — `{ job_id, job_type, domain, payload, payload_ref, lease_token, lease_until, job_version, attempt_no, checkpoint: { checkpoint_type, checkpoint_payload } | null, ruleset/policy refs }`;
- `204 NO_JOB` — nothing eligible (worker stays `ONLINE_IDLE`);
- `409 WORKER_PAUSED` / `409 WORKER_DISABLED` — admission guard rejected the claim;
- `409 STALE_WORKER` — registry `last_seen_at` older than the staleness window and no heartbeat this request (fail closed; worker must heartbeat first).

### 6.2 Heartbeat as liveness + renewal

`POST /api/v1/workers/{worker_id}/heartbeat` — schema `worker-heartbeat-v2` (additive over `-v1`):

```json
{
  "schema_version": "worker-heartbeat-v2",
  "health_state": "ONLINE_BUSY",
  "job_context": { "job_id": "job-…", "lease_token": "…", "job_version": 7 }
}
```

In one short transaction: update `last_seen_at`; when `job_context` is present and matches an active lease owned by this worker — extend `lease_until = now + lease_duration_seconds`, advance `LEASED -> IN_PROGRESS` on first occurrence, bump `job_version`, append `RENEWED`/`STARTED` event. `-v1` heartbeats (no `job_context`) keep working unchanged.

Mismatch handling (worker thinks it owns a lease the DB does not): response includes `lease_mismatch: true`; worker must stop the local unit of work, checkpoint if it safely can, and reconcile via `ReleaseJob` or a fresh claim. Mismatch is recorded in `job_events` but never transitions the job by itself.

### 6.3 Renewal without heartbeat

`POST /api/v1/jobs/{job_id}/lease/renew` — for long external interactions (browser/session/device work) where the heartbeat cadence is too coarse. Requires `lease_token` + `job_version`; conditional, short transaction, returns new `lease_until` + `job_version`. Optional per class policy; default is heartbeat renewal only.

### 6.4 Checkpoint

`POST /api/v1/jobs/{job_id}/checkpoints` (`RecordCheckpoint`): body `{ lease_token, job_version, checkpoint_type, checkpoint_payload, idempotency_key }`. Append `job_checkpoints`, bump `job_version`, append event. The next claim returns the latest checkpoint so a resumed execution replays from durable state, never from a guess.

### 6.5 Terminal transitions

`POST /api/v1/jobs/{job_id}/complete|/fail|/needs-human` — body `{ lease_token, job_version, result/error ref, error_class?, idempotency_key, evidence_ref }`. Conditional on token+version; same transaction appends the terminal event and clears the worker lease ownership (`assigned_worker_id`/`lease_token`/`lease_until` retained for audit but marked released via state terminal). Worker `health_state` returns to `ONLINE_IDLE` (or `DEGRADED` when its outbox retains undelivered work). `SKIPPED_DUPLICATE` follows the same path via the domain engine's duplicate gate.
Replay safety: complete/fail/needs-human/checkpoint are idempotent under `idempotency_key` (second call with the same key returns the original outcome without a second logical transition).

### 6.6 Release without terminal state

`POST /api/v1/jobs/{job_id}/lease/release` — worker releases voluntarily (e.g. `PAUSED` path, session required). Requires token+version; job returns to `QUEUED` (attempt preserved) or to `PAUSED`/`NEEDS_HUMAN` per caller intent and class policy.

## 7. Pause / resume

Two orthogonal pauses, both recorded durably and both auditable via `job_events`:

### 7.1 Worker admission pause

Triggers:
- worker self-pause under backpressure (outbox high-watermark, `RESOURCE_EXHAUSTED`) — the worker must pause admission rather than grow memory/disk (API §13);
- operator pause (maintenance, account/session hygiene);
- `SESSION_REQUIRED` class policy may suggest a pause rather than failure.

Contract: `POST /api/v1/workers/{worker_id}/pause` `{ reason, until? , actor: "worker"|"operator" }` and `POST /api/v1/workers/{worker_id}/resume`.

Effects:
- registry sets `admission_paused=1` (+ reason/at); health vocabulary unchanged; dashboards derive "PAUSED (admission)";
- claim guard rejects with `409 WORKER_PAUSED` while paused;
- the current job (if any) keeps its lease and runs to completion/checkpoint — pause is admission-only, never a mid-execution kill;
- heartbeat continues while paused (`ONLINE_IDLE` + admission flag), so liveness and pause are independent;
- resume clears the flag and makes the worker claim-eligible again. Expiry of `until` (if set) also clears it via the engine's periodic tick.

### 7.2 Job pause (operator) and graceful job stop (worker)

Operator: `POST /api/v1/jobs/{job_id}/pause` `{ reason }` → engine asks the holding worker (via the job-context heartbeat response `pause_requested: true`) to finish its current safe unit, checkpoint, and call `lease/release` with intent `PAUSED`; engine then marks `PAUSED` + event `PAUSED`. If the worker is unresponsive, the lease-expiry tick applies the class policy (never a silent kill of a publish in flight).

Worker graceful stop (human/session needed mid-job): worker checkpoints, then `lease/release` with intent `PAUSED` and `reason: SESSION_REQUIRED`. Engine transitions `IN_PROGRESS -> PAUSED`.

Resume: `POST /api/v1/jobs/{job_id}/resume` (operator) → `PAUSED -> QUEUED` (event `RESUMED`); the next eligible claim returns the job with its latest checkpoint. Attempt budget is preserved across pause/resume; each claim still consumes one attempt.

### 7.3 Relation to registry states

- `DISABLED` stays operator-only and terminal for admission (a disabled worker is never resurrected automatically); pausing is the reversible, less-severe control.
- `OFFLINE` remains *derived* from heartbeat staleness and never itself pauses a job — only lease expiry does.
- A paused worker that goes stale simultaneously is handled by the same lease-expiry machinery.

## 8. Transaction and concurrency rules

- Claim/renew/release/complete/checkpoint each run in **one short transaction**; never hold a transaction open across browser/device/human work (DATA_MODEL §10).
- Optimistic concurrency via `job_version`; every conditional transition is `WHERE … AND job_version = ?` (or token match) and checks rowcount.
- Claim single-winner is the conditional UPDATE above; the active-lease invariant is guaranteed by the state machine plus conditional updates, not by a separate long-lived lock.
- Append `job_events` in the same transaction as every transition.
- Only bounded retry for safe SQLite conflicts (e.g. `database is locked`); no blind retry of irreversible external actions (DATA_MODEL §11).
- Repository boundary: application code uses semantic repo operations (`create_job`, `claim_next_job`, `renew_lease`, `record_checkpoint`, `complete_job`, …) — vendor SQL stays in adapters (DATA_MODEL §12).

## 9. Registry integration points (this slice builds on the registry)

1. `claim` is the first consumer of `capabilities` + `health_state` + the new admission flag.
2. Heartbeat `-v2` makes the heartbeat endpoint the lease-renewal point, preserving "heartbeat is liveness, renewal is durable job truth" (API §10).
3. Current-job visibility: join `jobs` on `assigned_worker_id` where the lease is active — no new worker column.
4. Busy/idle derivation: `ONLINE_BUSY` when the worker holds an active lease; `ONLINE_IDLE` otherwise; worker-reported `DEGRADED` (outbox pressure) and operator `DISABLED` continue to win over idle for display.
5. Registry acceptance criteria stay valid: worker replacement without losing durable job state now means: new registration keeps `installation_id` semantics; the old worker's leases expire per class policy and jobs are reclaimed — never lost.

## 10. Engine responsibilities (Shared Job Engine)

Framework-free Python module (in-memory + SQL repo ports, mirroring the worker-registry slice structure):
- validate all transitions and pause/resume intents;
- claim selection (priority, `not_before`, capability match, attempt budget);
- periodic tick: expire leases and apply class policy (`idempotent-safe -> QUEUED`, else `NEEDS_HUMAN`), clear timed admission pauses, surface `pause_requested` on the holding worker's next heartbeat;
- write `job_events` for every transition and anomaly;
- enforce idempotency replay for terminal/checkpoint writes.

Job-class policy is configuration (versioned, recorded on the job) — e.g. `max_attempts`, `lease_duration_seconds`, `idempotent_safe: true|false`, `renewal: heartbeat|explicit`.

## 11. HTTP surface summary

| Operation | Endpoint | Guard |
|---|---|---|
| Claim next job | `POST /api/v1/jobs/claim` | registry online, not paused/disabled |
| Renew lease | `POST /api/v1/jobs/{job_id}/lease/renew` | token + version |
| Release lease | `POST /api/v1/jobs/{job_id}/lease/release` | token + version + intent |
| Record checkpoint | `POST /api/v1/jobs/{job_id}/checkpoints` | token + version |
| Complete / Fail / NeedsHuman | `POST /api/v1/jobs/{job_id}/complete` `/fail` `/needs-human` | token + version |
| Pause / Resume job | `POST /api/v1/jobs/{job_id}/pause` `/resume` | operator or holding worker |
| Pause / Resume worker admission | `POST /api/v1/workers/{worker_id}/pause` `/resume` | worker or operator |
| Heartbeat (+renew) | `POST /api/v1/workers/{worker_id}/heartbeat` | registered worker |
| Job/queue queries | `GET /api/v1/jobs`, `GET /api/v1/jobs/{job_id}` | admin/worker scope |

All endpoints mount on every runtime profile like the registry slice; error contract per API §12 (`RETRYABLE`, `CONFLICT`, `SESSION_REQUIRED`, `RESOURCE_EXHAUSTED`, `OUTCOME_UNKNOWN`, `NEEDS_HUMAN`, stable codes).

## 12. Sequence sketches

### 12.1 Claim → heartbeat renewal → checkpoint → complete

```text
Worker                Back Office (registry + job engine + jobs)
  |  register/heartbeat     |
  |------------------------>|  last_seen, ONLINE_IDLE
  |  POST /jobs/claim       |
  |------------------------>|  one tx: guard, pick, conditional lease
  |<------------------------|  200 {job_id, payload, lease_token, lease_until, version, checkpoint}
  |  execute page work ...  |
  |  heartbeat v2 (job ctx) |
  |------------------------>|  one tx: last_seen + lease_until += d, IN_PROGRESS
  |  POST checkpoints       |
  |------------------------>|  one tx: append + version++
  |  POST complete          |
  |------------------------>|  one tx: terminal + event, worker ONLINE_IDLE
```

### 12.2 Admission pause + job pause/resume

```text
Worker (outbox high)                    Engine
  | POST /workers/{id}/pause reason=OUTBOX_HIGHWATER |
  |------------------------------------->|  admission_paused=1 (+event)
  | (current job completes; releases)    |
  | POST /jobs/claim -> 409 WORKER_PAUSED|
  |------------------------------------->|
Operator
  | POST /jobs/job-7/pause reason=review |
  |------------------------------------->|  pause_requested on heartbeat
Worker
  | checkpoint + lease/release intent=PAUSED |
  |------------------------------------->|  IN_PROGRESS -> PAUSED (+event)
Operator
  | POST /jobs/job-7/resume              |
  |------------------------------------->|  PAUSED -> QUEUED (+event)
Worker
  | POST /jobs/claim -> 200 (job-7 + latest checkpoint) |
```

## 13. Test plan (mirrors existing gate tiers)

- Engine component tests (in-memory repos, no FastAPI/SQLAlchemy): every legal/illegal transition; claim selection by priority/capability/not_before; expiry policy per class (`idempotent-safe -> QUEUED`, else `NEEDS_HUMAN`); pause admission guard; resume replays latest checkpoint; idempotency replay of complete/checkpoint; version-conflict rejection.
- Contract tests: request/response shapes incl. `204 NO_JOB`, `409 WORKER_PAUSED/DISABLED/STALE_WORKER`, `lease_mismatch` heartbeat response.
- SQLite integration: concurrent claims on one job → exactly one winner (thread stress); restart durability — a leased job survives restart and expires/reclaims on tick; heartbeat renewal extends `lease_until`; pause flag survives restart; events append-only with monotonic sequence.
- Stress: many workers claiming from one queue; no duplicate active leases (invariant assert after every wave).
- Extension integration (later phase): discovery worker pauses admission when its outbox high-watermark trips, includes `job_context` in heartbeats once it can hold a lease.

## 14. Phasing

- **Phase A — persistence**: migration `0004_shared_core_jobs` (+worker admission columns), SQLAlchemy + in-memory repos for `jobs`/`job_events`/`job_checkpoints`, semantic repo operations.
- **Phase B — engine**: framework-free lease/pause/resume state machine + dispatcher tick + class-policy config; component + contract tests.
- **Phase C — API + runtime wiring**: endpoints above on every runtime profile; SQLite integration + stress gates.
- **Phase D — Program 1 worker consumption**: heartbeat `-v2` with `job_context`, outbox-high-watermark admission pause, graceful job stop with checkpoint; extension 0.1.16+.
- **Phase E — verification + docs**: full gate suite, implementation log + evidence records, Kanban/backlog update.

## 15. Open decisions for review

1. Default `lease_duration_seconds` and heartbeat-renewal factor per job class (engine config; suggest discovery `60 s` lease / `15–20 s` heartbeat).
2. Whether claim is dispatcher-picked (recommended, control-plane principle) with no worker-side job_id targeting in v1.
3. `PAUSED` retention: resume-only vs. auto-requeue after a configured max paused duration.
4. Whether operator job-pause should default to letting the current attempt finish (recommended) vs. preempting at the next checkpoint.

## 16. Acceptance criteria (additions to SHARED_CORE_SPEC §16)

1. A worker can claim, renew, checkpoint and complete a job through registry-authenticated endpoints; the lease invariant holds under concurrency stress.
2. Lease expiry never duplicates irreversible work: outcome-unknown classes route to `NEEDS_HUMAN`.
3. Pausing worker admission blocks new claims but never kills the current job; resuming restores claim eligibility.
4. A paused job resumes from its latest durable checkpoint with its attempt budget preserved.
5. Every claim/renew/checkpoint/pause/resume/expiry/terminal is auditable in `job_events`.
6. Engine behavior is component-testable without network or production DB (in-memory ports), per SHARED_CORE_SPEC §15.
