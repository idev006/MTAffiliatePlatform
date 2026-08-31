# System Diagrams

Status: DEVELOPMENT HANDOFF BASELINE
Notation: Mermaid diagrams are source-controlled documentation and must evolve with the architecture.

## 1. System Context

```mermaid
flowchart LR
    OP[Operator] --> BO[Python Back Office]
    BO --> DB[(Operational DB)]
    BO --> BW[Browser Worker Farm]
    BW --> WEB[Shopee Web / Affiliate]
    BO --> DH[Device Host Manager]
    DH --> AW[Android Workers]
    AW --> DEV[Android Devices]
    DEV --> APP[Shopee Android App]
    BO --> AN[Analytics / Learning Loop]
```

## 2. Component Diagram

```mermaid
flowchart TB
  subgraph BackOffice[Python Back Office / Control Plane]
    API[API Gateway]
    ORCH[Job Orchestrator]
    REG[Worker/Device Registry]
    RULES[Rules & Configuration]
    PI[Product Intelligence]
    OFF[Affiliate Offer Service]
    PUB[Publishing Planner]
    VID[Video Registry/Fingerprint]
    AUD[Audit/Telemetry]
    REP[Repository Layer]
  end
  API --> ORCH
  API --> REG
  PI --> REP
  OFF --> REP
  PUB --> REP
  VID --> REP
  ORCH --> REP
  AUD --> REP
  REP --> DB[(SQLite / PostgreSQL)]
  API <--> BROWSER[Browser Workers]
  API <--> HOST[Device Host Manager]
  HOST --> WORKER[Android Worker Processes]
  WORKER --> ADAPTERS[ADB / UI / Stream Adapters]
```

## 3. Use Cases

```mermaid
flowchart LR
  Operator((Operator)) --> UC1[Configure discovery/rules]
  Operator --> UC2[Review product shortlist]
  Operator --> UC3[Review/select offers]
  Operator --> UC4[Register/manage videos]
  Operator --> UC5[Plan publishing]
  Operator --> UC6[Monitor workers/devices]
  Operator --> UC7[Human takeover/recovery]
  BrowserWorker((Browser Worker)) --> UC8[Collect product observations]
  BrowserWorker --> UC9[Collect/export affiliate offers]
  AndroidWorker((Android Worker)) --> UC10[Execute publish job]
  AndroidWorker --> UC11[Report Scene/process/results]
```

## 4. End-to-End Swimlane

```mermaid
flowchart LR
  subgraph BO[Back Office]
    A[Create discovery campaign] --> D[Normalize/dedupe/score]
    D --> E[Approve product]
    H[Rank/select offers] --> I[Create content/publish plan]
    I --> J[QA + duplicate + freshness gate]
    J --> K[Create publish job]
    N[Verify/record result] --> O[Analytics feedback]
  end
  subgraph BW[Browser Workers]
    B[Discover products] --> C[Submit observations + ACK]
    F[Discover candidate offers] --> G[Submit/export results]
  end
  subgraph AW[Android Worker]
    L[Lease job + recognize Scene] --> M[Execute Scene workflow]
  end
  A --> B --> C --> D
  E --> F --> G --> H
  K --> L --> M --> N
```

## 5. Step 3 Activity Diagram

```mermaid
flowchart TD
  S[Receive/lease PUBLISH_VIDEO] --> C{Device/account/job valid?}
  C -- No --> NH[NEEDS_HUMAN / reject]
  C -- Yes --> R[Recognize current Scene]
  R --> X{Scene confidence sufficient?}
  X -- No --> REC[Recovery Engine]
  REC --> R
  X -- Yes --> P[Select permitted Process]
  P --> E[Resolve logical Element]
  E --> A[Execute Action]
  A --> V[Verify expected state/next Scene]
  V --> OK{Job complete?}
  OK -- No --> CP[Checkpoint + report] --> R
  OK -- Yes --> F[Final publish verification / ledger result]
```

## 6. Worker Job Sequence

```mermaid
sequenceDiagram
  participant BO as Back Office
  participant HM as Device Host Manager
  participant W as Android Worker
  participant A as Shopee App
  participant DB as Database

  W->>BO: heartbeat/capabilities
  BO->>DB: atomically lease job
  BO-->>W: PUBLISH_VIDEO + lease token
  W->>A: observe/recognize Scene
  loop Scene processes
    W->>A: resolve + action
    A-->>W: UI state
    W->>BO: checkpoint / Scene event
    BO->>DB: short transaction + ACK
  end
  W->>A: final POST action
  A-->>W: success / failure / unknown
  W->>BO: JOB_RESULT
  BO->>DB: ledger + job state transaction
  BO-->>W: durable ACK
```

## 7. Android Scene State Model

```mermaid
stateDiagram-v2
  [*] --> VIDEO_SOURCE
  VIDEO_SOURCE --> VIDEO_PREPARE: select/upload
  VIDEO_PREPARE --> PRODUCT_BASKET: next
  PRODUCT_BASKET --> POST_DETAILS: confirm basket
  POST_DETAILS --> READY_TO_PUBLISH: validate metadata
  READY_TO_PUBLISH --> PUBLISHING: post
  PUBLISHING --> PUBLISH_SUCCESS: confirmed
  PUBLISHING --> POST_OUTCOME_UNKNOWN: timeout/disconnect/ambiguous
  POST_OUTCOME_UNKNOWN --> NEEDS_HUMAN
  state RECOVERY {
    [*] --> REOBSERVE
    REOBSERVE --> LOCAL_RECOVERY
    LOCAL_RECOVERY --> ANCHOR_RECOVERY
    ANCHOR_RECOVERY --> CONTROLLED_RESTART
  }
```

## 8. Deployment Diagram

```mermaid
flowchart TB
  subgraph Portable[Portable Mode / One Windows PC]
    UI[PySide6 Back Office]
    API[FastAPI]
    SDB[(SQLite)]
    HM[Device Host Manager]
    W1[Worker 01]
    WN[Worker N]
    UI --> API --> SDB
    API <--> HM
    HM --> W1 --> P1[Phone 01]
    HM --> WN --> PN[Phone N]
  end

  subgraph Farm[Farm Mode]
    SAPI[Back Office API]
    PDB[(PostgreSQL)]
    H1[Device Host A]
    HN[Device Host N]
    SAPI --> PDB
    SAPI <--> H1
    SAPI <--> HN
  end
```

## 9. Database Transaction Boundary

```mermaid
sequenceDiagram
  participant W as Worker
  participant API as Back Office API
  participant DB as DB
  participant EXT as External UI/App

  W->>API: request/claim job
  API->>DB: BEGIN claim/lease
  DB-->>API: COMMIT
  API-->>W: leased job
  W->>EXT: long external work (NO SQL TX OPEN)
  EXT-->>W: result
  W->>API: result/idempotency key
  API->>DB: BEGIN validate + update + event
  DB-->>API: COMMIT + durable ACK
  API-->>W: ACK
```

## 10. SSOT Change Flow

```mermaid
flowchart LR
  Issue[Requirement/defect/decision] --> Doc[Update governing document]
  Doc --> ADR[ADR if material]
  ADR --> Contract[Update API/data/state contracts]
  Contract --> Ready{Design gates pass?}
  Ready -- No --> Doc
  Ready -- Yes --> Code[Implementation]
  Code --> Verify[Conformance tests]
  Verify --> Done[Verified]
```
