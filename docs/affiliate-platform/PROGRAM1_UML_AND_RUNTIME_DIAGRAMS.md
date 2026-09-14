# Program 1 — UML and Runtime Diagram Pack

Status: GOVERNING DESIGN SUPPORT
Date: 2026-09-09
Governing architecture: `PROGRAM1_SYSTEM_ARCHITECTURE.md`

This pack exists to reduce implementation ambiguity. Diagrams describe responsibility, collaboration, state and failure boundaries. Concrete selectors and browser-specific internals remain adapter-local.

## D1 — Business Use Case View

```mermaid
flowchart LR
  M((Marketing / Affiliate Strategist))
  O((Operator))
  P2((Program 2))
  A((Analytics / Attribution))
  W((Browser Worker))

  M --> U1[Define affiliate hypothesis]
  M --> U2[Define required decision signals]
  O --> U3[Create/approve discovery campaign]
  O --> U4[Review Opportunity Thesis / shortlist]
  O --> U5[Pause/resume/stop worker jobs]
  W --> U6[Collect bounded market observations]
  U6 --> U7[Persist observations]
  U7 --> U8[Derive opportunity features]
  U8 --> U9[Evaluate / rank opportunity]
  U9 --> U4
  U4 --> U10[Emit qualified opportunity]
  U10 --> P2
  A --> U11[Provide downstream outcomes]
  U11 --> U1
```

## D2 — Strategy-to-Implementation Activity Diagram

```mermaid
flowchart TD
  S[Affiliate success objective] --> H[Form hypothesis]
  H --> Q[What decision must improve?]
  Q --> G[Define required signals]
  G --> E{Evidence source known?}
  E -- No --> R[Create controlled evidence-research card]
  R --> E
  E -- Yes --> V{Evidence sufficient/stable?}
  V -- No --> X[Keep signal EXPERIMENTAL/LAB]
  X --> R
  V -- Yes --> C[Define contract/feature]
  C --> I[Implement smallest vertical slice]
  I --> T[Test + fixture + resilience]
  T --> P{Pass quality/evidence gates?}
  P -- No --> F[RCA / CAPA / revise design]
  F --> H
  P -- Yes --> D[Deploy/experiment]
  D --> O[Measure downstream outcome]
  O --> L[Learn / version new policy]
  L --> H
```

## D3 — Program 1 Component Diagram

```mermaid
flowchart TB
  subgraph BO[Back Office]
    API[Program 1 API]
    APP[Application Services]
    JOB[Shared Job Engine]
    REG[Worker Registry]
    NORM[Identity / Normalization]
    FE[Opportunity Feature Engine]
    OE[Opportunity Evaluation]
    RANK[Ranking / Shortlist]
    REP[Repository Ports]
  end

  subgraph EXT[Browser Extension Worker]
    BG[Background Runtime]
    ROUTER[Collection Router]
    PROFILE[Collection Profiles]
    OUT[(Durable Outbox)]
    PANEL[Side Panel]
  end

  API --> APP
  APP --> JOB
  APP --> NORM
  APP --> FE
  APP --> OE
  APP --> RANK
  APP --> REP
  JOB --> REP
  REG --> REP
  PANEL --> BG
  API <--> BG
  BG --> ROUTER --> PROFILE
  PROFILE --> OUT --> API
  REP --> DB[(SSOT DB)]
  PROFILE --> WEB[Shopee Web]
```

## D4 — Discovery Job Happy-Path Sequence (Target Composition)

```mermaid
sequenceDiagram
  autonumber
  actor M as Marketing/Operator
  participant API as Back Office API
  participant APP as Discovery Planning
  participant JE as Shared Job Engine
  participant DB as DB
  participant BW as Browser Background Worker
  participant CR as Collection Router/Profile
  participant OUT as Local Outbox
  participant FE as Opportunity Engines

  M->>API: Create campaign(hypothesis, signals, scope)
  API->>APP: planDiscovery(...)
  APP->>JE: createJob(capabilities, policy refs)
  JE->>DB: persist QUEUED job
  DB-->>JE: commit

  BW->>API: heartbeat + capabilities
  BW->>API: lease compatible work
  API->>JE: leaseJob(worker)
  JE->>DB: atomic lease
  DB-->>JE: lease_token + version
  API-->>BW: job + lease

  BW->>CR: collect bounded page/surface
  CR-->>BW: observations + page classification + checkpoint
  BW->>OUT: durable enqueue batch
  BW->>API: submit observations(batch_id)
  API->>DB: atomic ingestion + receipt
  DB-->>API: durable accounted result
  API-->>BW: ACK
  BW->>OUT: remove acknowledged batch

  BW->>API: checkpoint/result
  API->>JE: verify lease + checkpoint
  JE->>DB: persist checkpoint/job transition

  API->>FE: derive features/evaluate opportunity
  FE->>DB: persist feature snapshot + decision
  FE-->>API: Opportunity Thesis / action
```

## D5 — ACK Loss / Idempotent Replay

```mermaid
sequenceDiagram
  autonumber
  participant BW as Browser Worker
  participant OUT as Outbox
  participant API as Back Office
  participant DB as DB

  BW->>OUT: enqueue B-101
  BW->>API: submit B-101
  API->>DB: atomic observations + receipt
  DB-->>API: COMMIT
  API--xBW: ACK lost

  Note over BW,OUT: retain B-101

  BW->>API: replay same B-101
  API->>DB: lookup durable receipt/idempotency
  DB-->>API: same accounted result
  API-->>BW: reproducible ACK
  BW->>BW: validate version + accepted/duplicate/accounted counts
  BW->>OUT: persist last receipt + remove B-101 in one serialized update
  Note over BW,OUT: Panel projects last receipt; checkpoint uses this batch only
```

## D6 — Poison Message / Quarantine Decision

```mermaid
flowchart TD
  M[Outbox message] --> S[Send]
  S --> R{Result class}
  R -- Success/Accounted --> A[ACK and remove]
  R -- Transient --> T[Retain + backoff]
  R -- Permanent contract/payload --> Q[Quarantine + structured reason]
  R -- Ambiguous ACK --> C[Retain + reconcile]
  T --> S
  Q --> H[Operator / remediation workflow]
  C --> H
  H --> D{Safe resolution?}
  D -- Yes --> S
  D -- No --> X[Keep quarantined / close with evidence]
```

## D7 — Anti-bot / Schema Change Flow

```mermaid
flowchart TD
  P[Open target page] --> O[Observe page context]
  O --> C{Classification}
  C -- Supported --> X[Execute profile]
  C -- Anti-bot / verification --> B[PAGE_BLOCKED_BY_ANTIBOT]
  C -- Unsupported --> U[PAGE_UNSUPPORTED]
  C -- Expected surface but schema drift --> S[SCHEMA_CHANGED]
  B --> PZ[Pause / cooldown / human resolution]
  U --> E[End or re-plan scope]
  S --> Q[Quarantine profile / collect evidence]
  X --> V{Extraction valid?}
  V -- Yes --> R[Return observations]
  V -- No --> S
```

## D8 — Pause / Resume Sequence (Target Operator Interaction)

```mermaid
sequenceDiagram
  autonumber
  actor OP as Operator
  participant UI as Side Panel
  participant API as Back Office
  participant JE as Shared Job Engine
  participant BW as Background Worker
  participant DB as DB

  OP->>UI: Pause
  UI->>API: pauseJob(job_id)
  API->>JE: request pause
  JE->>DB: transition to PAUSE_REQUESTED/PAUSED policy state
  API-->>BW: pause directive / next poll response
  BW->>API: safe checkpoint + paused
  API->>JE: record checkpoint/state
  JE->>DB: durable PAUSED
  UI->>API: refresh status
  API-->>UI: PAUSED + checkpoint

  OP->>UI: Resume
  UI->>API: resumeJob(job_id)
  API->>JE: validate resumable
  JE->>DB: transition eligible for lease/resume
  BW->>API: renew/reacquire valid lease
  API-->>BW: resume from checkpoint
```

## D9 — Service Worker Restart Recovery

```mermaid
sequenceDiagram
  autonumber
  participant CH as Chromium
  participant BW as Extension Background Worker
  participant ST as chrome.storage
  participant API as Back Office
  participant JE as Shared Job Engine

  CH--xBW: MV3 worker terminated
  Note over ST: settings/run-local/outbox durable state remains
  CH->>BW: restart on event
  BW->>ST: load settings + local delivery state
  BW->>API: register/heartbeat
  API->>JE: query active lease/job authority
  JE-->>API: canonical job state
  API-->>BW: canonical state/directive
  BW->>BW: reconstruct only safe local execution state
  BW->>API: resume/reconcile from durable checkpoint
```

## D10 — Collection Profile Selection Sequence

```mermaid
sequenceDiagram
  participant BW as Worker Runtime
  participant R as Collection Router
  participant REG as Profile Registry
  participant P as Selected Profile
  participant PAGE as Browser Page

  BW->>R: collect(page_context, required_capability)
  R->>REG: find compatible profiles
  REG-->>R: candidates + evidence status/version
  R->>PAGE: observe surface indicators
  alt exactly one supported profile
    R->>P: execute observed-fact extraction
    P->>PAGE: read bounded DOM facts
    PAGE-->>P: facts
    P-->>R: observations + page context
    R-->>BW: success/profile version
  else ambiguous
    R-->>BW: PROFILE_AMBIGUOUS / fail closed
  else unsupported
    R-->>BW: PAGE_UNSUPPORTED
  end
```

## D11 — Opportunity Feature Derivation Sequence

```mermaid
sequenceDiagram
  participant APP as Opportunity Application
  participant REP as Repository
  participant FE as Feature Engine
  participant POL as Policy Registry
  participant DB as DB

  APP->>REP: load product history/context
  REP->>DB: read observations/projection
  DB-->>REP: history
  APP->>POL: resolve feature_policy_version
  POL-->>APP: immutable policy snapshot
  APP->>FE: derive(history, context, policy)
  FE-->>APP: features + unknowns + evidence refs
  APP->>REP: save feature snapshot
  REP->>DB: commit
```

## D12 — Opportunity Evaluation Sequence

```mermaid
sequenceDiagram
  participant APP as Opportunity Application
  participant QE as Qualification Engine
  participant OE as Opportunity Evaluation
  participant R as Ranking Engine
  participant REP as Repository

  APP->>REP: load feature snapshot + policy
  REP-->>APP: features/evidence/context
  APP->>QE: qualify(...)
  QE-->>APP: eligible / needs evidence / reject + reasons
  alt eligible
    APP->>OE: evaluate(...)
    OE-->>APP: thesis + action + risk + optional score
    APP->>R: rank within campaign
    R-->>APP: rank/shortlist decision
  else insufficient evidence
    APP->>OE: build NEEDS_EVIDENCE thesis
    OE-->>APP: uncertainty/action
  end
  APP->>REP: persist decision/shortlist
```

## D13 — Program 1 to Program 2 Handoff

```mermaid
sequenceDiagram
  participant P1 as Program 1
  participant DB as DB
  participant P2 as Program 2

  P1->>DB: load qualified opportunity decision
  P1->>P1: build ProductCandidateForOfferDiscovery v1.1
  P1->>P2: handoff(idempotency, thesis, evidence freshness)
  P2->>P2: validate contract/identity/freshness
  alt accepted
    P2-->>P1: ACCEPTED / ALREADY_ACCEPTED
  else stale
    P2-->>P1: DEFERRED_STALE
  else invalid/conflict
    P2-->>P1: INVALID_IDENTITY / CONFLICT
  end
```

## D14 — Opportunity Lifecycle State

```mermaid
stateDiagram-v2
  [*] --> OBSERVED
  OBSERVED --> INSUFFICIENT_EVIDENCE
  OBSERVED --> FEATURE_READY
  INSUFFICIENT_EVIDENCE --> FEATURE_READY: more evidence

  FEATURE_READY --> QUALIFIED
  FEATURE_READY --> DEPRIORITIZED
  FEATURE_READY --> REJECTED

  QUALIFIED --> WATCH
  QUALIFIED --> TEST_NOW
  TEST_NOW --> SCALE: favorable outcome evidence
  TEST_NOW --> HOLD: inconclusive
  TEST_NOW --> STOP: poor/risk outcome
  WATCH --> TEST_NOW: condition improves
  SCALE --> HOLD: conditions deteriorate
  HOLD --> TEST_NOW: requalified
  DEPRIORITIZED --> WATCH: context changes
```

This lifecycle is a conceptual business-decision view, not a mutable single-field lifecycle that overrides versioned decision history.

## D15 — Evidence Lifecycle

```mermaid
stateDiagram-v2
  [*] --> EXPERIMENTAL
  EXPERIMENTAL --> LAB_VALIDATED
  LAB_VALIDATED --> EVIDENCE_VALIDATED
  EVIDENCE_VALIDATED --> PRODUCTION_CANDIDATE
  PRODUCTION_CANDIDATE --> PRODUCTION_APPROVED
  LAB_VALIDATED --> STALE
  EVIDENCE_VALIDATED --> STALE
  PRODUCTION_CANDIDATE --> STALE
  PRODUCTION_APPROVED --> STALE
  STALE --> EXPERIMENTAL: re-study
  PRODUCTION_APPROVED --> DEPRECATED
```

## D16 — Data Lineage / Traceability

```mermaid
flowchart LR
  H[Hypothesis]
    --> S[Signal Requirement]
    --> J[Discovery Job]
    --> E[Evidence / Profile]
    --> O[Observation]
    --> N[Normalized Fact]
    --> F[Feature Snapshot]
    --> D[Opportunity Decision]
    --> L[Shortlist]
    --> P2[Program 2 Candidate]
    --> C[Content / Publish]
    --> R[Outcome]
    --> M[Model/Policy Learning]
    --> H
```

## D17 — Portable Deployment

```mermaid
flowchart TB
  subgraph PC[Windows Portable Mode]
    API[Program 1 FastAPI]
    CORE[Application / Engines]
    DB[(SQLite)]
    B[Chromium/Brave + Extension]
    API --> CORE --> DB
    B <--> API
  end
  B --> WEB[Shopee Web]
```

## D18 — Farm Deployment

```mermaid
flowchart TB
  subgraph CP[Central Control Plane]
    API[Program 1 API]
    CORE[Application / Engines]
    DB[(PostgreSQL)]
    API --> CORE --> DB
  end

  subgraph H1[Browser Host 1]
    W1[Worker A]
    W2[Worker B]
  end
  subgraph H2[Browser Host N]
    W3[Worker ...]
  end

  API <--> W1
  API <--> W2
  API <--> W3
```

## D19 — Failure Containment

```mermaid
flowchart LR
  PAGE[Shopee page/profile failure] --> PW[One collection profile/job affected]
  PW --> WR[Worker degraded/quarantined if repeated]
  WR --> HOST[Browser host only if shared runtime problem]
  HOST --> BO[Control plane only if central dependency fails]

  DBF[DB/API failure] --> OUT[Worker retains durable outbox]
  OUT --> REC[Retry/reconcile]
```

Rule: one bad page/profile/message must not silently corrupt unrelated opportunity decisions.

## D20 — Test Pyramid and Evidence Gate

```mermaid
flowchart TB
  U[Unit: pure rules/features]
  C[Component: use case + fakes]
  K[Contract: API/ports/profile]
  F[Fixture: deterministic DOM]
  I[Integration: DB/migrations]
  R[Resilience: restart/ACK/lease]
  E[E2E: real extension + local fixture]
  L[Controlled Live Shopee Evidence]

  U --> C --> K --> F --> I --> R --> E --> L
```

Live evidence validates adapters/profile assumptions. Core business logic should already be proven below that layer.

## Diagram Governance

A material change to Program 1 ownership, lifecycle, contracts, profile architecture, durable ACK semantics or opportunity decision flow requires updating the relevant diagram in this pack before/with implementation.

Diagrams are not decorative. They are part of the implementation handoff contract.

## Use-case coverage and implementation boundary — 2026-09-09

D1-D20 retain the governing architectural intent. D4 is an end-to-end target composition, not evidence that collection automatically triggers evaluation. D8 is the target operator interaction: do not infer dedicated Pause/Resume buttons from it (the current panel exposes Start/Stop). D11-D13 describe logical responsibilities; the concrete runtime may combine these in application services. D13 does not prove an automatic network push to Program 2. D18 is a deployment target, not a verified farm/scale claim. D7 classification names are conceptual; D10 uses the current PROFILE_AMBIGUOUS router result. Implementation status must be read with the current contract and verification record.

| Use case | Sequence | Governing contract | Implementation/test evidence |
|---|---|---|---|
| Strategy, campaign and discovery planning | D4 | PROGRAM1_SYSTEM_ARCHITECTURE.md | tests/component/test_program1_strategy_planner.py; operator campaign UI pending |
| Worker register and heartbeat | D21 | APPLICATION_AND_ENGINE_CONTRACTS.md | tests/contract/test_worker_registry_api_contract.py; tests/integration/sqlite/test_worker_registry_sqlite.py |
| Manual Capture and collector bootstrap | D22, D10 | PROGRAM1_CHROMIUM_E2E_AND_RESTART_SPEC.md | browser_plugin/program1/tests/manual_collector_bootstrap.test.mjs; real Brave single-page receipt evidence |
| Auto Run, lease, renew, checkpoint and pagination | D4, D23 | PROGRAM1_SYSTEM_ARCHITECTURE.md | browser_plugin/program1/tests/background_execution.test.mjs; Chromium restart harness; live pagination gated |
| Durable ingestion, duplicate ACK and image reference | D5, D24 | PROGRAM1_ACK_ACCOUNTING_CONTRACT.md; PROGRAM1_IMAGE_REFERENCE_CONTRACT.md | tests/integration/sqlite/test_program1_durable_batch.py; tests/unit/test_program1_image_reference.py |
| Delivery retry, quarantine and operator recovery | D25 | PROGRAM1_ACK_ACCOUNTING_CONTRACT.md | browser_plugin/program1/tests/delivery_reliability.test.mjs; no automatic quarantine repair UI claimed |
| Pause/resume and restart reconciliation | D8, D9 | PROGRAM1_SYSTEM_ARCHITECTURE.md | browser_plugin/program1/tests/background_execution.test.mjs; canonical job transitions remain Back Office owned |
| Read observations/history and image reference | D26 | PROGRAM1_IMAGE_REFERENCE_CONTRACT.md | tests/contract/test_program1_observation_evidence.py; catalog/image UI pending |
| Restore receipt and inspect delivery status | D27 | PROGRAM1_ACK_ACCOUNTING_CONTRACT.md | browser_plugin/program1/tests/background_transport.test.cjs; Chromium panel reload scenario |
| Derive features, evaluate, review shortlist | D11, D12 | PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md | tests/component/test_program1_opportunity_flow.py; production scoring gated |
| Qualified handoff to Program 2 | D13 | PROGRAM1_TO_PROGRAM2_HANDOFF_CONTRACT.md | tests/contract/test_program1_opportunity_api_contract.py; no Program2 implementation expansion |
| Download/cache images; outcome attribution | Not implemented | Separate approved contract required | P1-IMG-1 stores URLs only; do not invent a download sequence as current behavior |

## D21 — Register / Refresh Worker and Heartbeat

```mermaid
sequenceDiagram
  actor OP as Operator
  participant UI as Settings Panel
  participant BW as Background Worker
  participant ST as Local Storage
  participant API as Registry API
  participant APP as Registry Application
  participant REP as Registry Repository
  OP->>UI: Save backend URL and worker ID
  UI->>BW: Save settings and register
  BW->>ST: Read or persist installation ID
  BW->>API: Register worker ID, installation ID, version, capabilities
  API->>APP: register
  APP->>REP: Atomic insert or refresh
  alt New worker or same installation
    REP-->>APP: Committed worker record
    APP-->>API: Record
    API-->>BW: Registered
    BW-->>UI: Registry status
    BW->>API: Heartbeat with reportable health
    API->>APP: Record heartbeat
    APP->>REP: Commit liveness
  else Worker ID belongs to another installation
    REP-->>APP: Registration conflict
    APP-->>API: Conflict
    API-->>BW: HTTP 409
    BW-->>UI: Registration failed
    Note over OP,REP: Choose an unused ID; never overwrite another installation
  end
  Note over APP,REP: Re-registration does not resurrect a Back Office disabled worker
```

## D22 — Manual Capture on a Fresh Tab

```mermaid
sequenceDiagram
  actor OP as Operator
  participant UI as Side Panel
  participant BR as Browser Bridge
  participant CR as Collector Router and Profiles
  participant BW as Background Runtime
  participant ST as Durable Outbox
  OP->>UI: Capture Current Page
  UI->>BR: Find active supported web tab and check permission
  alt Permission denied or unsupported tab
    BR-->>UI: Structured failure
    UI-->>OP: Show blocked state; no success
  else Allowed tab
    UI->>BR: Inject core, profiles, router, then content bridge
    Note over BR,CR: Idempotent bootstrap installs one message receiver
    UI->>BR: Send capture message
    BR->>CR: Classify page and select versioned profile
    alt Blocked, ambiguous or missing receiver
      CR-->>UI: Failure via bridge
      UI-->>OP: Show error; do not queue fabricated observations
    else Supported capture
      CR-->>UI: Observations and pagination facts
      UI->>UI: Attach worker provenance and batch ID
      UI->>BW: Queue batch
      BW->>ST: Commit local message
      BW->>BW: Drain delivery using D24 and D25
      BW-->>UI: Current batch receipt or pending/failure
      UI-->>OP: Render confirmed receipt separately from telemetry
    end
  end
  Note over UI,BW: Manual capture does not create a canonical campaign or claim completion of an unleased job
```

## D23 — Background Auto Cycle and Last Page

```mermaid
sequenceDiagram
  participant WA as Wake or Operator Start
  participant BW as Background Controller
  participant LC as Job Lifecycle Client
  participant BO as Back Office Job Application
  participant CR as Browser Collector
  participant ST as Local Storage
  WA->>BW: Execute bounded cycle
  BW->>LC: Reconcile active work or lease compatible job
  LC->>BO: Validate worker and lease authority
  BO-->>LC: Canonical work and valid token or no work
  alt No eligible work or invalid authority
    LC-->>BW: Stop or reconcile
    BW->>ST: Persist local stopped state
  else Valid work
    BW->>CR: Open or recover tab and collect
    CR-->>BW: Observations and observed pagination
    BW->>BW: Durable delivery D24
    alt Current batch has no valid accounted receipt
      BW->>ST: Persist blocked state; retain recoverable evidence
    else Current batch accounted
      BW->>LC: Checkpoint current receipt and page facts
      LC->>BO: Validate lease and persist checkpoint
      alt Observed has_next is false
        BW->>LC: Verify and complete
        LC->>BO: Canonical verification and completion
        BO-->>LC: Completed job
        BW->>ST: Clear local active work; terminal run
      else More work according to profile
        BW->>CR: Advance using profile pagination evidence
        BW->>ST: Persist local progress and schedule wake
        Note over BW,BO: Delay waits outside database transactions; renew/reconcile before further side effects
      end
    end
  end
```

## D24 — Atomic Observation / Image Reference Ingestion

```mermaid
sequenceDiagram
  participant BW as Worker
  participant API as Program 1 API
  participant APP as Program1Service
  participant ING as Batch Ingestor Port and SQL Adapter
  participant DB as SQLite
  BW->>API: Batch identity and observations with optional image URL
  API->>API: Validate payload and HTTP(S) image reference
  alt Invalid input or missing job binding
    API-->>BW: HTTP 422; no ACK
  else Valid input
    API->>APP: ingest_batch
    APP->>APP: Fingerprint payload; omit null image field for legacy compatibility
    APP->>ING: Atomic ingest with fingerprint
    ING->>DB: Begin transaction and inspect batch receipt
    alt Existing batch and same fingerprint
      DB-->>ING: Original accepted and received counts
    else Batch or observation identity has changed payload
      ING->>DB: Rollback
      ING-->>API: Conflict via application
      API-->>BW: HTTP 409; no successful receipt
    else New batch
      ING->>DB: Insert new observations; account exact duplicates
      ING->>DB: Insert receipt and commit together
      DB-->>ING: Durable result
    end
    opt Ingestion returned a durable result
      ING-->>APP: Original batch counts
      APP-->>API: Accepted, duplicate and accounted counts
      API-->>BW: Versioned ACK
    end
  end
  Note over API,DB: No image fetch, browser wait or network wait in transaction
  Note over APP,DB: URL is observed evidence, not an image file or new-product count
```

## D25 — Drain / Retry / Quarantine and Local Commit Failure

```mermaid
sequenceDiagram
  participant BW as Background Drain
  participant ST as Serialized Local Storage
  participant API as Back Office
  participant UI as Operator Status
  BW->>ST: Read pending messages
  loop Each pending message until blocking failure
    BW->>API: Submit original payload and batch ID
    alt Valid accounted ACK
      API-->>BW: Receipt
      BW->>BW: Validate identity, version and integer totals
      BW->>ST: One update stores last receipt and removes message
      alt Local update succeeds
        BW-->>UI: Confirmed delivery
      else Local update fails
        BW-->>UI: Retained or uncertain; retry original identity
      end
    else Permanent payload HTTP 400/409/413/415/422
      BW->>ST: Move message to quarantine with reason
      Note over BW,ST: Continue only after successful quarantine write
    else Network, transient, authentication or unknown failure
      BW-->>UI: Retain message and stop this drain
    else Malformed or ambiguous ACK
      BW-->>UI: Retain and require reconciliation
    end
  end
  Note over BW,UI: Original IDs survive retry; no blind payload rewrite or automatic quarantine repair
```

## D26 — Read Product Observation History / Image Evidence

```mermaid
sequenceDiagram
  actor OP as Operator or API Client
  participant API as Program 1 API
  participant APP as Program1Service
  participant REP as Product Repository Port
  participant DB as SQLite Adapter
  OP->>API: GET product observations with limit
  alt Limit outside 1..100
    API-->>OP: HTTP 422
  else Valid limit
    API->>APP: observation_evidence(product key, limit)
    APP->>REP: observation_history(product key)
    REP->>DB: Read stored observations
    DB-->>REP: History including nullable image reference
    REP-->>APP: Chronological history
    APP->>APP: Return newest first with bounded count
    APP-->>API: Evidence list
    API-->>OP: HTTP 200; empty list if unknown
  end
  Note over APP,DB: Response limit is not storage pagination; no remote image fetch
```

## D27 — Restore Last Receipt After Panel Reopen

```mermaid
sequenceDiagram
  actor OP as Operator
  participant UI as Side Panel
  participant BW as Background Runtime
  participant ST as Local Storage
  OP->>UI: Open panel or refresh status
  UI->>BW: Get process status
  BW->>ST: Read outbox and last persisted receipt
  ST-->>BW: Stored evidence and backend association
  alt Receipt backend matches current settings
    BW-->>UI: Last receipt and pending outbox count
    UI-->>OP: Original-batch counts and pending delivery separately
  else Missing receipt or another backend
    BW-->>UI: No current-backend receipt
    UI-->>OP: No confirmed receipt available
  end
  Note over UI,ST: Panel reopen never owns job transitions or reconstructs success from UI counters
```

## D28 — Operator Product Review

The governing sequence and failure branches are in PROGRAM1_OPERATOR_REVIEW_CONTRACT.md. It extends D26 with a paged latest-product list and a read-only daisyUI shell. Implementation: Program1Service.product_evidence_page, Program1 runtime static mount, BackOffice.vue. Evidence: tests/contract/test_program1_observation_evidence.py and real Brave list/history readback. No remote image fetch or business mutations.
