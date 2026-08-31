# Development Cycle Diagrams

Status: GOVERNING VISUAL REFERENCE
Date: 2026-08-31
Companion policy: `DEVELOPMENT_CYCLE_STANDARD.md`

## 1. Closed-Loop Development Lifecycle

```mermaid
flowchart LR
    A[Need / Problem / Goal] --> B[Evidence / Context]
    B --> C[Document / ADR / Contract]
    C --> D{Definition of Ready}
    D -- Not Ready --> C
    D -- Ready --> E[Kanban READY]
    E --> F[Implement Small Vertical Slice]
    F --> G[Developer Verification]
    G --> H[Static + Automated Gates]
    H --> I[Adversarial / Failure Tests]
    I --> J[Code + Architecture Review]
    J --> K[Integration / Compatibility]
    K --> L{Release / Acceptance Gate}
    L -- Fail --> M[Problem Record + RCA]
    L -- Pass --> N[Controlled Release / Product Acceptance]
    N --> O[Observe Telemetry / Feedback]
    O --> P{Issue / Lesson?}
    P -- No --> Q[DONE / Operate]
    P -- Yes --> M
    M --> R[Corrective Action]
    R --> S[Preventive Action]
    S --> T[Regression Test / Guardrail]
    T --> U[Update Documents / ADR / Config / Runbook]
    U --> C
```

## 2. Kanban State and Quality Gates

```mermaid
flowchart LR
    B[BACKLOG] --> A[ANALYSIS]
    A --> D[DESIGN / CONTRACT]
    D --> R[READY]
    R --> I[IN DEV]
    I --> C[CODE REVIEW]
    C --> V[VERIFY]
    V --> X{All Required Gates Pass?}
    X -- Yes --> DONE[DONE]
    X -- No --> P[Problem / Defect Record]
    P --> I

    A -.-> ND[NEEDS_DECISION]
    D -.-> NR[NEEDS_REAL_DATA]
    I -.-> BL[BLOCKED]
    V -.-> LAB[NEEDS_DEVICE_LAB]
    V -.-> NH[NEEDS_HUMAN]
```

## 3. Product Verification Pyramid and Operational Loop

```mermaid
flowchart TB
    L1[Static / Build Quality]
    L2[Unit + Property Tests]
    L3[Component + Contract Tests]
    L4[Integration + Compatibility]
    L5[Resilience + Failure Injection]
    L6[Performance + Capacity + Endurance]
    L7[E2E + Product Acceptance]
    L8[Controlled Release + Operational Validation]

    L1 --> L2 --> L3 --> L4 --> L5 --> L6 --> L7 --> L8
    L8 --> OBS[Telemetry / Operator Feedback / Incidents]
    OBS --> RCA[RCA + CAPA + Lesson Learned]
    RCA --> L1
```

## 4. Defect-to-Prevention Feedback Loop

```mermaid
flowchart LR
    F[Failure / Defect / Near Miss] --> E[Collect Evidence]
    E --> S[Severity + Impact]
    S --> C[Containment]
    C --> R[Root Cause Analysis]
    R --> CA[Corrective Action]
    CA --> PA[Preventive Action]
    PA --> RT[Regression Test]
    RT --> DG[Durable Guardrail]
    DG --> V[Verification Evidence]
    V --> LL[Lesson Learned]
    LL --> X{Cross-Program Applicable?}
    X -- Yes --> GOV[Update Governing Standard]
    X -- No --> LOCAL[Update Local Spec / Runbook]
    GOV --> CLOSE[Close Record]
    LOCAL --> CLOSE
```

## 5. CI Failure Sequence

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant Docs as SSOT Documents
    participant Code as Code / Tests
    participant CI as CI Quality Gates
    participant Log as Problem + CAPA Register
    participant Review as Reviewer

    Dev->>Docs: Confirm card is READY
    Dev->>Code: Implement smallest vertical slice
    Dev->>CI: Push / open PR
    CI->>CI: Lint + unit + contract + integration + stress as required

    alt All gates pass
        CI-->>Review: Verification evidence
        Review->>Docs: Confirm implementation conforms
        Review-->>Dev: Eligible for DONE / next gate
    else Legitimate gate failure
        CI-->>Dev: Failure evidence
        Dev->>Log: Record problem / severity / reproduction
        Dev->>Docs: Check missing or incorrect rule
        Dev->>Code: Correct implementation / tests
        Dev->>Code: Add regression protection
        Dev->>Log: Record RCA + corrective + preventive action
        Dev->>CI: Re-run affected and full required gates
        CI-->>Review: New verification evidence
    end
```

## 6. Durable Ingestion Transaction — Program 1 Reference

```mermaid
sequenceDiagram
    participant Worker as Browser Worker
    participant API as Back Office API
    participant App as Program 1 Application
    participant DB as SQLite/PostgreSQL

    Worker->>API: POST batch_id + observations
    API->>App: ingest_batch(...)
    App->>DB: BEGIN transaction
    App->>DB: Claim/check batch_id

    alt Existing same batch fingerprint
        DB-->>App: Original durable receipt
        App->>DB: ROLLBACK/close read transaction
        App-->>API: Original ACK semantics
        API-->>Worker: Same ACK
    else Existing different fingerprint
        DB-->>App: Conflict
        App->>DB: ROLLBACK
        App-->>API: CONFLICT
        API-->>Worker: HTTP 409
    else New batch
        App->>DB: Insert batch claim
        App->>DB: Insert/validate observations
        App->>DB: Finalize accepted_count receipt
        App->>DB: COMMIT facts + receipt atomically
        App-->>API: Durable result
        API-->>Worker: ACK
    end

    Note over Worker,DB: No durable ACK is emitted before the transaction commits.
```

## 7. Diagram Usage Rule

When a new workflow has multiple components, irreversible effects, retries, concurrency, durable acknowledgement, or recovery behavior, the responsible design card must add or update an appropriate sequence/activity/state/integration diagram before Implementation Ready.
