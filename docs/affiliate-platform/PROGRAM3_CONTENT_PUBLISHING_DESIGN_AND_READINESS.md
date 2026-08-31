# Program 3 — Content Publishing & Android Device Farm

Status: IMPLEMENTATION-GOVERNING DESIGN / FOUNDATION READY
Date: 2026-08-31

## 1. Mission
Program 3 turns an approved content-publish plan into a verified Shopee publishing outcome through managed Android devices while preventing duplicate posts, blind actions and ambiguous replay.

Program 3 receives commercial choices from Program 2. Android workers must never choose products/offers on commercial grounds.

## 2. Architecture Boundary
`Back Office Global Orchestrator -> Device Host Manager -> Worker Supervisor -> Android Worker Runtime -> Android Control Adapters -> Shopee App`

Three orchestration scopes are mandatory:
- Back Office: job/business lifecycle and canonical state;
- Device Host Manager: device/resource/worker ownership;
- Worker Runtime: Scene/process/action execution.

## 3. Worker Execution Model
`Worker -> Job -> Workflow -> Scene -> Process -> Action -> Logical Element -> Selector`

Golden Rule:
`Observe -> Recognize -> Validate -> Act -> Verify -> Checkpoint`

Unknown/ambiguous Scene blocks business action.

## 4. Initial Scene Workflow
`VIDEO_SOURCE -> VIDEO_PREPARE -> PRODUCT_BASKET -> POST_DETAILS -> READY_TO_PUBLISH -> PUBLISHING -> PUBLISH_SUCCESS`

Scenes are versioned and defined by multi-signal signatures. Real thresholds/selectors remain evidence-gated.

## 5. Publishing Plan Contract
Back Office provides identity-rich immutable plan snapshot including:
- publish_job_id / idempotency key;
- platform/account context;
- video identity + hash/fingerprint references;
- selected Product/Offer/link identities from Program 2;
- expected seller/shop/item evidence;
- caption/tags/metadata policy snapshot;
- basket capacity/policy version;
- duplicate-policy version;
- required freshness checks.

Worker reports observations/facts; it does not mutate the plan semantics.

## 6. Duplicate Prevention
Publishing Ledger is authoritative.

Required gates:
1. job creation;
2. queue admission;
3. pre-dispatch;
4. immediately before irreversible submit where safe;
5. atomic post-success ledger transition.

Video filename is never identity. Exact SHA-256 plus configurable perceptual fingerprint evidence is the baseline.

After uncertain submit: `POST_OUTCOME_UNKNOWN -> RECONCILE -> CONFIRMED | NOT_PUBLISHED | NEEDS_HUMAN`.
Never auto-repost while outcome is unknown.

## 7. Device Ownership
One device has at most one active Worker owner. Device Host Manager owns durable/lease-level device assignment and resource admission.

Device states include:
`ONLINE | OFFLINE | UNAUTHORIZED | MISSING | BUSY | DEGRADED | QUARANTINED`.

ADB unauthorized always requires human authorization; no bypass behavior.

## 8. Resource Governance
Device Host Manager enforces budgets for:
- CPU
- RAM
- USB/ADB throughput
- screen streams
- disk/outbox
- network

Under pressure, stop admitting new work and degrade observability before compromising business correctness.

## 9. Adapter Ports
- `DeviceTransportPort` — ADB candidate
- `UIAutomationPort` — uiautomator2 primary candidate; Appium alternative
- `ScreenStreamPort` — scrcpy/STF-style candidate
- `InputControlPort`
- `SceneEvidencePort` / snapshot provider

Adapters are replaceable. Domain/workflow code cannot import these concrete tools directly.

## 10. Logical Element Resolution
Priority:
1. resource/platform identifier
2. accessibility/content-description
3. stable text + context
4. class/state/property
5. relative hierarchy
6. controlled XPath-like fallback
7. visual matching fallback
8. coordinates last resort

Coordinates must be explicitly version/profile scoped and treated as fragile evidence.

## 11. Recovery Levels
0. re-observe/stability wait
1. local recovery
2. Safe Anchor Scene
3. controlled app restart when action history proves it safe
4. Human Takeover / NEEDS_HUMAN

Recovery cannot cross an irreversible boundary without reconciliation evidence.

## 12. Event Model
Examples:
- JOB_STARTED
- DEVICE_BOUND
- SCENE_CHANGED
- JOB_CHECKPOINT
- VIDEO_SELECTED
- BASKET_ATTACHED
- FORM_VERIFIED
- POST_SUBMITTED
- POST_CONFIRMED
- POST_OUTCOME_UNKNOWN
- POST_FAILED
- NEEDS_HUMAN

Back Office owns durable transitions. Worker events are facts, not direct canonical DB writes.

## 13. Persistence / Transaction Invariants
- no SQL transaction remains open while waiting on phone/app/network;
- optimistic concurrency/version checks for mutable canonical state;
- idempotency keys and unique constraints enforce invariants;
- publish success + Publishing Ledger update follows an atomic durable boundary;
- event history is append-oriented; current state is derived/managed by Back Office;
- bounded conflict/deadlock retry only where safe.

## 14. Program 3 Test Tailoring
1. Scene recognizer deterministic fixtures;
2. ambiguous/unknown Scene blocking tests;
3. selector fallback-order tests;
4. transition validator tests;
5. duplicate ledger normal/concurrent/restart tests;
6. post-submit ambiguity tests;
7. Worker crash/device unplug/ADB reconnect tests;
8. Back Office restart/lease expiry tests;
9. disk-full/outbox/resource-pressure tests;
10. device ownership collision tests;
11. screen-stream degradation tests;
12. physical-device controlled-lab tests;
13. 10/20/50/100-device benchmark before scale claims.

## 15. Failure/Conflict Matrix Minimum
Must cover at least:
- two workers same job;
- two workers same device;
- duplicate video job;
- device unplug during upload;
- network loss before/after POST_SUBMITTED;
- Shopee crash;
- Back Office restart;
- DB contention;
- worker/host crash;
- disk full;
- many streams;
- selector/UI drift;
- account session expired;
- unknown publish outcome.

Each case defines detection, authority owner, containment, recovery and forbidden outcome.

## 16. Implementation Readiness
### Foundation authorized now
- Program 3 domain types/state machines;
- Publishing Plan and Ledger contracts;
- duplicate policy engine with fakes;
- Scene/Process/Action model;
- Scene recognizer/transition validator using deterministic fixtures;
- Device Host ownership/resource model;
- worker event protocol;
- fake Android adapter ports;
- API DTOs and test harnesses.

### Production completion gates
- real Shopee Scene/signature inventory;
- selector profiles by app/version/locale/account context;
- Safe Anchor/recovery evidence;
- post-submit reconciliation validated;
- fingerprint algorithm/threshold validated;
- basket capacity validated against target app/account/version;
- physical device-lab verification;
- capacity/endurance benchmarks;
- Program 2 -> Program 3 handoff validated end-to-end.

Unresolved CRITICAL/HIGH design issues for foundation implementation: **0**.

## 17. Initial Vertical Slices
P3-VS1: immutable PublishPlan -> duplicate gate -> fake worker -> simulated confirmed result -> Publishing Ledger.

P3-VS2: Scene engine using fixture snapshots -> deterministic transitions -> checkpoint/recovery.

P3-VS3: Device Host registry/lease -> one worker per fake device -> disconnect/reconnect handling.

P3-VS4: fake end-to-end video/basket/details/publish workflow with POST_OUTCOME_UNKNOWN reconciliation.

P3-VS5: controlled physical-device spike with ADB/uiautomator2 and evidence capture only; no scale claim.
