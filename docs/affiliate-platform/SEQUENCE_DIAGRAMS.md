# Sequence Diagrams — Implementation Handoff Pack

Status: DEVELOPMENT HANDOFF BASELINE
Purpose: Define runtime collaboration, ownership, transaction boundaries, ACK/idempotency behavior and recovery semantics across the platform.
Notation: Mermaid `sequenceDiagram`.

> Rule: sequence diagrams describe business/runtime collaboration. Concrete DOM selectors, Android coordinates and ORM internals must not leak into these contracts.

## SD-01 — Step 1 Product Discovery Happy Path

```mermaid
sequenceDiagram
    autonumber
    actor OP as Operator
    participant API as Back Office API
    participant JE as Shared Job Engine
    participant DB as Repository/DB
    participant BW as Discovery Browser Worker
    participant OUT as Worker Local Outbox
    participant PE as Product Intelligence Engine

    OP->>API: Create discovery campaign
    API->>JE: create DISCOVER_PRODUCTS job
    JE->>DB: persist job + ruleset version
    DB-->>JE: committed

    BW->>API: heartbeat + capabilities
    BW->>API: request/lease compatible job
    API->>JE: claim job(worker_id)
    JE->>DB: atomic lease transaction
    DB-->>JE: lease token + version
    API-->>BW: job payload + lease token

    BW->>BW: observe supported Shopee page
    BW->>OUT: persist observation batch
    BW->>API: submit batch(batch_id, idempotency_key)
    API->>DB: normalize + persist observations
    DB-->>API: commit
    API-->>BW: durable ACK(batch_id)
    BW->>OUT: mark/delete acknowledged batch

    BW->>API: JOB_RESULT completed
    API->>JE: complete job
    JE->>DB: job state + event transaction
    DB-->>JE: commit

    API->>PE: evaluate new/changed products
    PE->>DB: read observations / write scores + shortlist
```

## SD-02 — Step 1 Outbox Retry / ACK Loss

```mermaid
sequenceDiagram
    autonumber
    participant BW as Browser Worker
    participant OUT as Local Outbox
    participant API as Back Office API
    participant DB as Database

    BW->>OUT: persist batch B-101
    BW->>API: submit B-101
    API->>DB: idempotent insert/update
    DB-->>API: COMMIT
    API--xBW: ACK lost / connection drops

    Note over BW,OUT: No ACK = retain durable local copy

    BW->>API: retry B-101 with same idempotency key
    API->>DB: detect previously committed B-101
    DB-->>API: existing durable result
    API-->>BW: ACK B-101
    BW->>OUT: remove/mark delivered
```

## SD-03 — Step 2 Affiliate Offer Discovery and Selection

```mermaid
sequenceDiagram
    autonumber
    participant PI as Product Intelligence Engine
    participant API as Back Office API
    participant JE as Shared Job Engine
    participant OW as Affiliate Offer Worker
    participant DB as Database
    participant OE as Offer Engine

    PI->>API: approved ProductCandidate
    API->>JE: create DISCOVER_OFFERS job
    JE->>DB: persist job

    OW->>API: heartbeat + affiliate capabilities/account context
    OW->>API: lease request
    API->>JE: claim compatible job
    JE->>DB: atomic lease
    API-->>OW: product identity + collection rules

    OW->>OW: verify authorized session/context
    OW->>OW: search/read candidate offers
    OW->>API: candidate batch + provenance
    API->>DB: persist candidate observations
    DB-->>API: durable ACK
    API-->>OW: ACK

    API->>OE: rank/select offers
    OE->>DB: read candidates + ruleset
    OE->>DB: persist preferred/backup selection
    OE-->>API: selected offer identities

    API-->>OW: SELECT/EXPORT instruction
    OW->>OW: execute permitted platform workflow
    OW->>API: export/result metadata
    API->>DB: validate + persist affiliate links + events
    DB-->>API: commit
    API-->>OW: durable ACK / job complete
```

## SD-04 — Step 2 Session Required / Human Intervention

```mermaid
sequenceDiagram
    autonumber
    participant OW as Affiliate Offer Worker
    participant API as Back Office API
    participant JE as Job Engine
    participant DB as Database
    actor OP as Operator

    OW->>OW: detect SESSION_REQUIRED
    OW->>API: JOB_ERROR(SESSION_REQUIRED, evidence)
    API->>JE: transition job
    JE->>DB: IN_PROGRESS -> NEEDS_HUMAN / WAITING_OPERATOR
    DB-->>API: commit
    API-->>OW: stop business actions
    API-->>OP: intervention required
    OP->>API: session restored / resume approved
    API->>JE: requeue/resume from checkpoint
    JE->>DB: persist new leaseable state
```

## SD-05 — Step 3 Publish Happy Path

```mermaid
sequenceDiagram
    autonumber
    participant PP as Publishing Engine
    participant DB as Publishing Ledger/DB
    participant API as Back Office API
    participant HM as Device Host Manager
    participant W as Android Worker
    participant SE as Scene Engine
    participant UA as UI Automation Adapter
    participant APP as Shopee Android App

    PP->>DB: validate video/offer/account/device eligibility
    PP->>DB: duplicate gate + reserve publish intent
    DB-->>PP: reservation committed
    PP->>API: create PUBLISH_VIDEO job

    HM->>API: host/device health + capacity
    W->>API: worker heartbeat/capabilities
    W->>API: lease request
    API-->>W: PublishPlan + lease token

    W->>SE: start workflow(plan)
    SE->>UA: observe UI hierarchy/state
    UA->>APP: inspect current screen
    APP-->>UA: UI state
    UA-->>SE: normalized observations
    SE->>SE: recognize + validate Scene

    loop Scene / Process / Action
        SE->>UA: execute logical action
        UA->>APP: semantic UI operation
        APP-->>UA: resulting state
        UA-->>SE: observations
        SE->>SE: verify expected transition
        W->>API: checkpoint + Scene event
        API->>DB: short transaction
        DB-->>API: commit
        API-->>W: ACK
    end

    Note over W,APP: Irreversible boundary
    SE->>UA: SUBMIT_PUBLISH
    UA->>APP: publish action
    APP-->>UA: publish result evidence
    UA-->>SE: confirmed success
    W->>API: POST_CONFIRMED + evidence
    API->>DB: transaction: ledger + publish state + job completion
    DB-->>API: durable commit
    API-->>W: final ACK
```

## SD-06 — Step 3 Scene Mismatch and Recovery

```mermaid
sequenceDiagram
    autonumber
    participant W as Android Worker
    participant SE as Scene Engine
    participant UA as UI Automation Adapter
    participant APP as Shopee App
    participant API as Back Office API

    W->>SE: continue current process
    SE->>UA: observe
    UA->>APP: inspect UI
    APP-->>UA: actual state
    UA-->>SE: observations
    SE->>SE: expected PRODUCT_BASKET, actual NETWORK_ERROR
    SE-->>W: transition mismatch
    W->>API: SCENE_MISMATCH + evidence

    SE->>SE: Recovery L0 re-observe
    SE->>UA: observe after UI stable
    UA-->>SE: still wrong scene
    SE->>SE: Recovery L1 local recovery
    SE->>UA: verified local navigation
    UA-->>SE: resulting observations

    alt Expected scene recovered
        SE-->>W: PRODUCT_BASKET confirmed
        W->>API: recovery checkpoint
    else Recovery budget exhausted
        SE-->>W: NEEDS_HUMAN
        W->>API: NEEDS_HUMAN + evidence
    end
```

## SD-07 — Publish Outcome Unknown / Never Blind Repost

```mermaid
sequenceDiagram
    autonumber
    participant W as Android Worker
    participant APP as Shopee App
    participant API as Back Office API
    participant PE as Publishing Engine
    participant DB as Publishing Ledger/DB
    actor OP as Operator

    W->>APP: SUBMIT_PUBLISH
    APP--xW: connection/UI response lost
    W->>API: POST_OUTCOME_UNKNOWN
    API->>PE: reconcile publish outcome
    PE->>DB: read publish intent/ledger/history

    alt Success can be proven
        PE->>DB: record POST_CONFIRMED + platform evidence
        DB-->>PE: commit
        PE-->>API: COMPLETED
    else Failure can be proven safe-to-retry
        PE->>DB: record verified failure
        DB-->>PE: commit
        PE-->>API: eligible for controlled retry policy
    else Outcome remains ambiguous
        PE->>DB: mark NEEDS_HUMAN / outcome_unknown
        DB-->>PE: commit
        PE-->>API: block repost
        API-->>OP: manual reconciliation required
    end

    Note over API,DB: Never auto-create a second publish while outcome is ambiguous
```

## SD-08 — Device Discovery, Worker Spawn and Ownership

```mermaid
sequenceDiagram
    autonumber
    participant ADB as ADB Device Transport
    participant HM as Device Host Manager
    participant RM as Resource Manager
    participant WS as Worker Supervisor
    participant W as Android Worker
    participant API as Back Office API

    ADB-->>HM: device connected(serial)
    HM->>HM: register/resolve device identity
    HM->>RM: admission check(CPU/RAM/USB/stream budget)

    alt Capacity available
        RM-->>HM: admit
        HM->>WS: spawn worker(device_id, serial)
        WS->>W: start isolated process
        W->>API: enroll/register + capabilities
        API-->>W: accepted configuration
        W->>API: heartbeat ONLINE_IDLE
    else Capacity exhausted
        RM-->>HM: defer admission
        HM->>API: DEVICE_AVAILABLE_HOST_CAPACITY_BLOCKED
    end
```

## SD-09 — Worker Crash, Lease Expiry and Safe Reassignment

```mermaid
sequenceDiagram
    autonumber
    participant W1 as Worker-01
    participant API as Back Office API
    participant JE as Job Engine
    participant DB as Database
    participant W2 as Worker-02

    W1->>API: checkpoint CP-4
    API->>DB: persist CP-4
    DB-->>API: ACK
    W1-xAPI: process/host disappears

    API->>JE: heartbeat stale / lease expired
    JE->>DB: inspect job + checkpoint + side-effect state

    alt Job safe to resume
        JE->>DB: expire lease + requeue from CP-4
        W2->>API: lease request
        API->>JE: claim job
        JE->>DB: atomic new lease
        API-->>W2: job + resume checkpoint CP-4
    else Irreversible outcome may have occurred
        JE->>DB: mark NEEDS_HUMAN / reconciliation
        Note over API,W2: No automatic reassignment of unsafe step
    end
```

## SD-10 — API → Application → Engine → Repository Boundary

```mermaid
sequenceDiagram
    autonumber
    actor C as Client/UI/CLI
    participant API as FastAPI Route
    participant UC as Application Use Case
    participant E as Domain Engine
    participant R as Repository Port
    participant DB as SQLAlchemy Adapter/DB

    C->>API: business request DTO
    API->>API: auth + DTO validation
    API->>UC: typed command
    UC->>R: load required domain state
    R->>DB: query
    DB-->>R: persistence rows
    R-->>UC: domain objects
    UC->>E: evaluate/execute business policy
    E-->>UC: typed decision/result
    UC->>R: persist state/events
    R->>DB: short transaction
    DB-->>R: commit
    R-->>UC: durable result
    UC-->>API: response model
    API-->>C: API response

    Note over API,E: API/UI contains no domain decision logic
```

## SD-11 — Desktop UI as Optional Shell

```mermaid
sequenceDiagram
    autonumber
    actor OP as Operator
    participant UI as PySide6 UI Shell
    participant API as API/Application Facade
    participant UC as Application Use Case
    participant E as Engine

    OP->>UI: user action
    UI->>UI: presentation validation only
    UI->>API: invoke business operation
    API->>UC: typed command/query
    UC->>E: execute policy/use case
    E-->>UC: result/state
    UC-->>API: result DTO
    API-->>UI: presentation-safe result
    UI-->>OP: render state

    Note over UI,E: Engine must be fully usable without UI
```

## SD-12 — Ruleset / Configuration Versioning During Job Execution

```mermaid
sequenceDiagram
    autonumber
    actor OP as Operator
    participant API as Back Office API
    participant CFG as Configuration Service
    participant JE as Job Engine
    participant DB as Database
    participant W as Worker

    OP->>API: publish new ruleset R2
    API->>CFG: validate + activate R2
    CFG->>DB: persist immutable R2 + active pointer
    DB-->>CFG: commit

    Note over JE,W: Existing job J1 was created under R1
    JE->>DB: read J1.ruleset_version = R1
    JE-->>W: dispatch J1 with effective R1 snapshot/version

    Note over API,DB: New jobs use R2; running jobs do not silently change semantics
```

## Sequence Diagram Coverage Rule

A feature is not Implementation Ready if its critical path crosses more than one runtime/component and none of the governing diagrams/specifications explains:

- initiating actor/component;
- authoritative owner of state;
- request/response/event contract;
- durable transaction/ACK boundary;
- idempotency/retry semantics;
- failure/ambiguity behavior;
- expected terminal state.

Sequence diagrams are normative for collaboration semantics but do not replace typed API contracts, state-machine specs or tests.
