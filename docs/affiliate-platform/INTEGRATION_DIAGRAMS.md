# Integration Architecture Diagrams

Status: IMPLEMENTATION HANDOFF BASELINE
Date: 2026-08-31
Governing rule: Project must follow the document.

## 1. Purpose

This document defines how the major components of MTAffiliatePlatform integrate at logical, runtime, protocol and data-flow levels.

It complements:
- `WORKFLOW.md` — canonical business workflow/pipeline;
- `SYSTEM_DIAGRAMS.md` — context/component/deployment/state views;
- `SEQUENCE_DIAGRAMS.md` — interaction timing and failure paths;
- `API_COMMUNICATION_AND_PLUGIN_ARCHITECTURE.md` — communication contract rules.

Integration design must preserve:
- one durable business SSOT;
- API-as-core;
- engine-first/headless-first architecture;
- pluggable adapters;
- explicit ACK/idempotency/retry boundaries;
- failure isolation;
- testability without live external systems.

---

## 2. Enterprise / Logical Integration Diagram

```mermaid
flowchart LR
  OP[Operator / Future UI] --> API[FastAPI / Application Boundary]
  CLI[CLI / Test Harness] --> API

  subgraph CORE[Python Back Office / Control Plane]
    API --> APP[Application Use Cases]
    APP --> JOB[Shared Job Engine]
    APP --> PI[Product Intelligence Engine]
    APP --> OE[Affiliate Offer Engine]
    APP --> CI[Content Identity Engine]
    APP --> PE[Publishing Engine]
    APP --> CFG[Rules / Configuration]
    APP --> REP[Repository Ports]
  end

  REP --> DB[(SQLite / PostgreSQL SSOT)]

  API <--> BW1[Step 1 Browser Workers]
  API <--> BW2[Step 2 Affiliate Workers]
  API <--> DH[Device Host Manager]

  DH --> WS[Worker Supervisor]
  WS --> AW[Android Worker Runtime]
  AW --> SE[Scene Engine]
  SE --> UA[UI Automation Adapter]
  AW --> DT[Device Transport Adapter]
  AW --> SS[Screen Stream Adapter]

  BW1 --> SHOPEEWEB[Shopee Web]
  BW2 --> AFFWEB[Shopee Affiliate Web]
  UA --> SHOPAPP[Shopee Android App]
  DT --> PHONE[Android Device]
  SS --> PHONE
```

### Authority rule
- Engines own business decisions/policies.
- Application layer coordinates use cases.
- Adapters translate external technology specifics.
- Database owns durable canonical state.
- UI/CLI/worker local state is never business SSOT.

---

## 3. Canonical Business Pipeline / Step Integration

```mermaid
flowchart LR
  S[Strategy / Rules] --> D[Step 1 Discovery]
  D --> N[Normalize / Dedupe]
  N --> PI[Product Intelligence]
  PI --> PL[Product Shortlist / Approval]
  PL --> OD[Step 2 Offer Discovery]
  OD --> OR[Offer Eligibility / Ranking]
  OR --> OS[Preferred + Backup Offer Selection]
  OS --> VR[Video Registry / Fingerprint]
  VR --> MATCH[Product + Offer + Video Match]
  MATCH --> PP[Publish Plan]
  PP --> G[Duplicate / Freshness / Policy Gate]
  G --> J[Shared Job Queue]
  J --> DH[Device Host]
  DH --> AW[Android Worker]
  AW --> V[Publish Verification]
  V --> L[Publishing Ledger]
  L --> A[Analytics / Attribution]
  A --> S
```

### Step handoff principle
Steps exchange canonical IDs and versioned contracts, not worker memory or UI-specific state.

---

## 4. Step 1 Integration — Product Discovery

```mermaid
flowchart LR
  BO[Back Office] -->|DISCOVER_PRODUCTS job| API[Worker API]
  API --> BW[Discovery Browser Worker]
  BW -->|read supported page| SW[Shopee Web]
  BW --> OUT[(Local Outbox)]
  OUT -->|ObservationBatch + idempotency| API
  API -->|short TX| DB[(SSOT DB)]
  DB -->|durable commit| API
  API -->|ACK| BW
  DB --> N[Normalization]
  N --> PI[Product Intelligence Engine]
  PI --> SL[Shortlist]
```

Integration invariants:
- observation batch persists locally before send;
- ACK only after durable Back Office commit;
- canonical dedupe happens centrally;
- Product Intelligence never depends directly on browser DOM.

---

## 5. Step 2 Integration — Affiliate Offer Discovery

```mermaid
flowchart LR
  PROD[Approved Product] --> APP[Offer Application Service]
  APP --> JOB[Shared Job Engine]
  JOB --> API[Worker API]
  API --> OW[Affiliate Browser Worker]
  OW --> WEB[Shopee Affiliate Web]
  OW --> OUT[(Local Outbox)]
  OUT -->|OfferCandidateBatch| API
  API --> DB[(SSOT DB)]
  DB --> OE[Affiliate Offer Engine]
  OE --> SEL[Preferred / Backup Selection]
  SEL --> LINK[Affiliate Link / Export Records]
  LINK --> P3[Step 3 Publishing Input]
```

Integration invariants:
- affiliate account/session provenance is part of observations when context-sensitive;
- commercial ranking occurs only in Back Office;
- Shared Core jobs remain lifecycle SSOT.

---

## 6. Step 3 Integration — Publishing / Android Device Farm

```mermaid
flowchart LR
  PLAN[Publish Plan] --> PE[Publishing Engine]
  PE --> DG{Duplicate / Policy / Freshness Gate}
  DG -->|pass| JE[Shared Job Engine]
  JE --> API[Worker API]
  API --> DH[Device Host Manager]
  DH --> RM[Resource Manager]
  RM --> WS[Worker Supervisor]
  WS --> AW[Android Worker]
  AW --> SE[Scene Engine]
  SE --> UAP[UIAutomationPort]
  UAP --> ADA[Android UI Adapter]
  ADA --> APP[Shopee App]
  AW -->|checkpoint/result| API
  API --> DB[(SSOT DB)]
  DB --> LED[Publishing Ledger]
```

Integration invariants:
- one active worker per device;
- Device Host Manager owns device/resource lifecycle;
- worker reports facts; Back Office owns durable transitions;
- no SQL transaction waits on Android/Shopee actions;
- POST outcome ambiguity never triggers blind repost.

---

## 7. Runtime Integration — Portable Mode

```mermaid
flowchart TB
  subgraph PC[Single Windows PC]
    UI[Optional PySide6 UI]
    API[FastAPI / Application]
    ENGINES[Domain Engines]
    DB[(SQLite)]
    DH[Device Host Manager]
    W1[Worker Process 01]
    W2[Worker Process 02]
    WN[Worker Process N]

    UI --> API
    API --> ENGINES
    ENGINES --> DB
    API <--> DH
    DH --> W1
    DH --> W2
    DH --> WN
  end

  W1 --> P1[Android 01]
  W2 --> P2[Android 02]
  WN --> PN[Android N]
```

Portable mode is one deployment unit, not one monolithic process.

---

## 8. Runtime Integration — Farm Mode

```mermaid
flowchart TB
  subgraph CONTROL[Control Plane]
    API[Back Office API]
    EN[Engines / Application]
    DB[(PostgreSQL)]
    API --> EN --> DB
  end

  subgraph BH[Browser Hosts]
    B1[Discovery Workers]
    B2[Offer Workers]
  end

  subgraph H1[Device Host A]
    HM1[Host Manager]
    WA[Android Workers 1..N]
    HM1 --> WA
  end

  subgraph H2[Device Host B]
    HM2[Host Manager]
    WB[Android Workers N+1..M]
    HM2 --> WB
  end

  API <--> B1
  API <--> B2
  API <--> HM1
  API <--> HM2
```

Horizontal growth must not require redesign of domain engines or canonical data models.

---

## 9. Protocol Integration Matrix

| Integration | Baseline Protocol | Authoritative? | Reliability mechanism |
|---|---|---:|---|
| UI/CLI -> Application | in-process command/query or HTTP | No | application validation |
| External client -> Back Office | REST/HTTP `/api/v1` | command/query boundary | idempotency + DB transaction |
| Worker -> Back Office results | REST/HTTP batch | Yes after commit | local outbox + durable ACK |
| Back Office -> Worker job | REST lease/poll baseline | job state in DB | lease token + expiry + version |
| Live telemetry | WebSocket | No | reconnect/snapshot refresh |
| Application -> DB | SQLAlchemy Repository/UoW | Yes | transaction + constraints |
| Device Host -> Worker | local IPC/process control | No | supervisor + heartbeat |
| Worker -> Android | adapter-specific ADB/UI automation | No | action verification/checkpoint |
| Screen streaming | scrcpy/STF-style adapter | No | reconnect/degrade |

Key rule: **WebSocket presence, screen stream state, and worker memory are never durable business truth.**

---

## 10. Data Ownership / SSOT Integration Diagram

```mermaid
flowchart TB
  DB[(Canonical DB / Durable SSOT)]

  PROD[Product Engine] --> DB
  OFFER[Offer Engine] --> DB
  JOB[Job Engine] --> DB
  CONTENT[Content Identity Engine] --> DB
  PUB[Publishing Engine] --> DB

  BW[Browser Worker Cache/Outbox] -. reports .-> DB
  AW[Android Worker Runtime] -. reports .-> DB
  UI[UI Read Model] -. reads .-> DB

  note1[Workers/UI are projections or execution state, not SSOT]
```

Authoritative durable areas include:
- canonical products and observations;
- affiliate offers and selections;
- jobs/job events/leases/checkpoints;
- videos/content identities;
- publishing ledger;
- versioned rules/configuration decisions.

---

## 11. Integration Failure Boundaries

```mermaid
flowchart LR
  BO[Back Office] --- BOUND1{{API Boundary}} --- W[Worker]
  W --- BOUND2{{Adapter Boundary}} --- EXT[External Platform]
  BO --- BOUND3{{Repository Boundary}} --- DB[(Database)]

  F1[API loss] --> R1[Outbox / retry / same idempotency]
  F2[Worker crash] --> R2[Lease expiry / checkpoint / safe reassignment]
  F3[Adapter/schema change] --> R3[SCHEMA_CHANGED / quarantine]
  F4[DB conflict] --> R4[short retry / optimistic concurrency]
  F5[Publish ambiguity] --> R5[reconcile / NEEDS_HUMAN]
```

Failure in one boundary must not silently mutate another boundary's authoritative state.

---

## 12. Test Integration Architecture

```mermaid
flowchart LR
  TEST[Test / Scenario] --> APP[Application Use Case]
  APP --> ENG[Domain Engine]
  ENG --> PORT[Port]
  PORT --> FAKE[Fake / In-Memory Adapter]

  APP2[Same Application Use Case] --> PORT2[Same Port]
  PORT2 --> REAL[Real DB / Browser / Android Adapter]
```

The same engine/application code must run against fake and real adapters. This is the core testability rule.

---

## 13. Integration Readiness Checklist

A component integration is not implementation-ready until all are explicit:
1. caller and callee;
2. command/query/event name;
3. request/response schema version;
4. canonical identity fields;
5. authoritative state owner;
6. sync vs async behavior;
7. timeout and retry policy;
8. idempotency identity;
9. ACK point;
10. transaction boundary;
11. failure/error classification;
12. observability/correlation IDs;
13. compatibility/version strategy;
14. test double / contract test path.

## 14. Governing Decision

Integration architecture is defined by contracts and ownership, not by incidental library calls. A concrete library may change behind an adapter without changing business workflow or SSOT semantics.