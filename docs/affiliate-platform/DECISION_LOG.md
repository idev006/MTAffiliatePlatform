# Architecture Decision Log

This file indexes accepted project-level decisions. Material changes require document update before/with implementation.

## ADR-001 — Document-Driven Project
Accepted. Approved documents are SSOT; code conflicting with them is non-conforming until intentionally resolved.

## ADR-002 — Three Business Domains + Shared Core
Accepted. Domain A Product Intelligence, Domain B Affiliate Offer Automation, Domain C Content Publishing, with one Shared Core/control plane.

## ADR-003 — Workers Are Execution Agents
Accepted. Workers execute bounded jobs; Python Back Office owns business decisions and durable state.

## ADR-004 — Replaceable Adapters
Accepted. Platform/browser/Android/database/tool details are hidden behind adapters/ports.

## ADR-005 — Canonical Product Identity Candidate
Proposed pending validation: `(platform, shop_id, item_id)`.

## ADR-006 — Multiple Offers per Product
Accepted. Product 1:N Offers; preferred offer is a versioned decision, not permanent identity.

## ADR-007 — Multiple Videos per Product
Accepted. Product 1:N Videos.

## ADR-008 — Central Video Duplicate Prevention
Accepted concept. Exact hash + perceptual fingerprint; 0–10 second segment is initial primary perceptual window pending validation.

## ADR-009 — Platform-Level Publishing Ledger
Accepted. Shopee duplicate policy is enforced centrally from durable video identity/publish history.

## ADR-010 — MTShopeeMobile Role
Accepted. Existing MTShopeeMobile is candidate/reference Android Publishing Execution component, not the overall platform.

## ADR-011 — Process Before Tool
Accepted. Freeze workflow/data/contract requirements before allowing tool convenience to shape business process.

## ADR-012 — Distributed Product Discovery Worker Farm
Accepted. Horizontal browser-worker scaling; Back Office owns sharding/leasing/checkpoints/health/backpressure/deduplication.

## ADR-013 — Extension Side Panel UI
Accepted. Browser worker management UI uses Chrome/Extension Side Panel where supported; Content Script remains replaceable page adapter.

## ADR-014 — Step 1 Design Baseline
Accepted for development handoff subject to feature-specific validation gates.

## ADR-015 — Distributed Affiliate Offer Worker Farm
Accepted. Reuses Shared Core worker/job infrastructure and capability-based assignment.

## ADR-016 — Step 2 Business Logic in Back Office
Accepted. Filters/ranking/selection/freshness are centralized.

## ADR-017 — Step 2 Design Baseline
Accepted for development handoff subject to feature-specific validation gates.

## ADR-018 — Affiliate Account Context Provenance
Accepted. Worker identity is distinct from affiliate account/session identity.

## ADR-019 — Shared Job Lifecycle Is Single SSOT
Accepted. Shared Core `jobs`/`job_events` owns lifecycle/lease/retry/assignment; domain job tables may only extend details.

## ADR-020 — Replaceable Android Control Adapters
Accepted. Device transport, UI automation, screen streaming and input control are separate interfaces. ADB/uiautomator2/Appium/scrcpy/STF-style components are implementation candidates, not business architecture.

## ADR-021 — Semantic Android Selectors Before XPath/Coordinates
Accepted. resource/accessibility/text/context/structure before XPath; coordinates last-resort only.

## ADR-022 — Scene-Based Android Worker Runtime
Accepted. `Worker -> Job -> Workflow -> Scene -> Process -> Action -> Element -> Selector` and `Observe -> Recognize -> Validate -> Act -> Verify -> Checkpoint`.

## ADR-023 — Multi-Signal Scene Signatures + Bounded Recovery
Accepted. Ambiguous/unknown Scene blocks business action; recovery is re-observe → local → safe anchor → controlled restart → human takeover.

## ADR-024 — Scene-Aware Shopee Video Publishing
Accepted. Video selection/upload → optional prepare/editor → product basket → metadata/tags → final gate → publish → verify; basket limit is configurable and must be validated against actual app/account.

## ADR-025 — API as Core
Accepted. Major components communicate through versioned business-level contracts. REST is authoritative command/query baseline; WebSocket handles live telemetry; DB remains durable SSOT; local outbox provides delivery reliability.

## ADR-026 — Portable-First / Scale-Ready Persistence
Accepted. SQLite Tier-1 Portable Mode, PostgreSQL Tier-1 Farm Mode behind SQLAlchemy/Repository interfaces.

## ADR-027 — SQLAlchemy + Alembic
Accepted. SQLAlchemy ORM/Core provides persistence abstraction and Alembic manages versioned schema migrations; Tier-1 engine compatibility must be tested.

## ADR-028 — Three-Level Orchestration
Accepted. Back Office = global orchestration; Device Host Manager = device/resource/worker lifecycle; Worker Runtime = Scene/process execution.

## ADR-029 — Resource Ownership and Admission Control
Accepted. Device hosts enforce CPU/RAM/USB/stream/disk/outbox budgets and controlled degradation rather than overload collapse.

## ADR-030 — Agile Kanban + Vertical Slices
Accepted. Document/contract-ready cards move through Kanban; foundation and end-to-end thin slices are preferred to large horizontal infrastructure batches.

## ADR-031 — MTAffiliatePlatform Is Authoritative Repository
**Status: Accepted — 2026-08-31**

Decision:
- `idev006/MTAffiliatePlatform` is the authoritative monorepo and SSOT for the entire project.
- `idev006/MTShopeeMobile` becomes an existing Android implementation/historical reference.
- New project-level architecture/process/contracts/source must follow MTAffiliatePlatform.
- Future repo splits require an independent deployment/release-boundary justification.

Governing record: `REPOSITORY_MIGRATION_2026-08-31.md`.

## ADR-032 — Engine-First / Headless-First Core
**Status: Accepted — 2026-08-31**

Business rules, state machines, ranking, duplicate policy, publishing guards and Scene/recovery logic live in domain engines/application services that run without graphical UI.

Development order where applicable:
`Domain -> Engine/Application -> Port -> Fake/Test -> Concrete Adapter -> API/CLI -> UI`.

Governing record: `PROJECT_STRUCTURE_AND_ENGINE_ARCHITECTURE.md`.

## ADR-033 — UI Is Optional Presentation Shell
**Status: Accepted — 2026-08-31**

PySide6 remains the baseline desktop UI technology when a desktop interface is useful, but the UI is not required for core execution and owns no canonical business logic/state. CLI/API/test harnesses must be able to exercise the same application use cases.

Governing record: `UI_SHELL_AND_PRESENTATION_ARCHITECTURE.md`.

## ADR-034 — Testability Is an Architecture Gate
**Status: Accepted — 2026-08-31**

Critical business behavior must be testable without network/browser/Android/UI using deterministic inputs and fake/in-memory ports. Unit/component/contract/integration/resilience/compatibility tests are separate layers. Physical-device tests validate adapters and real-world behavior, not every business rule.

Governing record: `TEST_STRATEGY_AND_QUALITY_GATES.md`.

## ADR-035 — Inward Dependency Rule / Composition Root
**Status: Accepted — 2026-08-31**

Domain/engines cannot depend on FastAPI, PySide6, SQLAlchemy, browser APIs or Android tools. Infrastructure implements ports and is wired in a composition root. Architecture dependency checks must be added to CI during foundation implementation.

Governing record: `PROJECT_STRUCTURE_AND_ENGINE_ARCHITECTURE.md`.

## ADR-036 — System Physiology Model
**Status: Accepted — 2026-08-31**

All significant platform components and workflows are reviewed through the control loop:

`Input -> Sense -> Validate -> Decide -> Act -> Verify -> Record -> Feedback -> Recover`.

A happy path alone is insufficient for Implementation Ready. Health detection, failure classification, containment and recovery are architecture concerns.

Governing record: `SYSTEM_PHYSIOLOGY_MODEL.md`.

## ADR-037 — Component Anatomy / Health and Recovery Contract
**Status: Accepted — 2026-08-31**

Every implementation-significant component must have one authority owner plus explicit inputs, processing responsibility, outputs, communication boundary, durable-state ownership, health signals, known failure modes, bounded recovery/escalation, resource considerations and test path. No durable capability may have two independent lifecycle authorities.

Governing record: `COMPONENT_RESPONSIBILITY_AND_HEALTH_MATRIX.md`.

## ADR-038 — Relative-First Paths via PathManager
**Status: Accepted — 2026-08-31**

All project/runtime-owned filesystem locations are resolved through a central injectable `PathManager`/`RuntimePaths` service using explicit managed roots and `pathlib.Path`. Source code must not depend on developer-specific absolute paths or the current working directory. Managed paths are relative/logical first and become absolute only at infrastructure/OS boundaries.

Governing record: `PATH_AND_CONFIGURATION_POLICY.md`.

## ADR-039 — TOML Typed Configuration / No Scattered Hard-Coding
**Status: Accepted — 2026-08-31**

TOML is the baseline human-editable configuration format. Typed settings, deterministic profile precedence and explicit secret references are mandatory. Operational/business values that may vary by deployment, policy, experiment, platform behavior or scale must not be scattered as source constants. Domain engines receive only the typed policy/config they require; running jobs retain captured versioned policy where semantics must remain stable.

Governing record: `PATH_AND_CONFIGURATION_POLICY.md`.

## ADR-040 — Step 1 Is Operationally Named Program 1
**Status: Accepted — 2026-08-31**

The former `Step 1 — Product Discovery / Product Intelligence` is operationally named **โปรแกรมที่ 1 (Program 1)** from this baseline onward. Historical documents using `Step 1` refer to the same bounded capability unless explicitly superseded.

Program 1 is authorized for foundation implementation and fake-driven MVP thin slices under the governing Document-Driven / Project Must Follow Documents / Agile Kanban policies. Production completion remains gated by real Shopee evidence, scoring-model validation, identity validation and endurance/performance validation.

Governing record: `PROGRAM1_IMPLEMENTATION_READINESS.md`.

## ADR-041 — Closed-Loop Development, Verification and Learning Cycle
**Status: Accepted — 2026-08-31**

Every implementation slice follows the project Development Cycle from documented need/design through Definition of Ready, implementation, layered verification, adversarial testing, review, integration and operational feedback. Meaningful defects and near misses feed a mandatory Root Cause Analysis / Corrective and Preventive Action / Lesson Learned loop. A lesson is adopted only when it changes a durable artifact such as a document, ADR, test, CI rule, configuration schema, code guardrail or runbook.

Quality gates must not be weakened solely to obtain a passing build. A legitimate gate failure is treated as evidence and corrected at the appropriate design/code/test/process layer.

Governing records: `DEVELOPMENT_CYCLE_STANDARD.md` and `PROBLEM_LESSON_AND_CAPA_LOG.md`.

## ADR-042 — Durable ACK State Shares an Atomic Transaction Boundary
**Status: Accepted — 2026-08-31**

When the platform sends an ACK whose meaning depends on durable acceptance, the business data and the idempotency/receipt state required to reproduce that ACK after restart must be committed atomically where feasible. Program 1 therefore persists an ingestion batch claim/receipt and its accepted ProductObservations in the same SQL transaction.

A process crash must not produce the state “business facts committed but no durable knowledge of the ACK identity” for the same logical ingestion operation. Duplicate/retry semantics must be reproducible after process restart.

This decision generalizes to Shared Job, publishing ledger and other irreversible/durable workflows where acknowledgement correctness depends on durable state.

Governing records: `DATABASE_CONCURRENCY_AND_PORTABILITY_SPEC.md`, `APPLICATION_AND_ENGINE_CONTRACTS.md`, and `DEVELOPMENT_CYCLE_STANDARD.md`.

## ADR-043 — Step 2 Is Operationally Named Program 2 and Foundation Development Is Authorized
**Status: Accepted — 2026-08-31**

The former Step 2 Affiliate Offer capability is operationally **Program 2 — Affiliate Offer Intelligence & Automation**. Foundation implementation is authorized for domain types, engines, ports, fakes, contracts, persistence abstractions and test harnesses. Real Shopee identity/account/export behavior remains production-gated.

Governing record: `PROGRAM2_AFFILIATE_OFFER_DESIGN_AND_READINESS.md`.

## ADR-044 — Step 3 Is Operationally Named Program 3 and Foundation Development Is Authorized
**Status: Accepted — 2026-08-31**

The former Step 3 Content Publishing capability is operationally **Program 3 — Content Publishing & Android Device Farm**. Foundation implementation is authorized for PublishPlan/Ledger/duplicate policy, Scene runtime models, Device Host ownership/resource logic, worker protocols, fakes and deterministic test fixtures. Real Shopee UI/device behavior remains production-gated.

Governing record: `PROGRAM3_CONTENT_PUBLISHING_DESIGN_AND_READINESS.md`.

## ADR-045 — Cross-Program Integration Uses Versioned Handoff Contracts
**Status: Accepted — 2026-08-31**

Program 1 -> Program 2 and Program 2 -> Program 3 integrate through explicit versioned business contracts, not direct persistence coupling. Programs may develop in parallel using fakes/contract tests. Breaking handoff changes require document/ADR/schema-version update and compatibility verification before implementation merge.

Governing records: `PROGRAM1_TO_PROGRAM2_HANDOFF_CONTRACT.md`, `PROGRAM2_TO_PROGRAM3_HANDOFF_CONTRACT.md`, `PROGRAM2_PROGRAM3_IMPLEMENTATION_KANBAN.md`.

## ADR-046 — Program 1 Is Strategy-Led Affiliate Opportunity Intelligence
**Status: Accepted — 2026-09-04**

Program 1 is governed by Affiliate/Marketing Strategy before collection mechanics.

Decision:
- Program 1 exists to identify and prioritize affiliate opportunities, not to maximize scraping volume or merely list popular products.
- Marketing/Affiliate hypotheses define the business questions and decision signals; engineering derives data/evidence/collection requirements from them.
- Browser workers remain bounded fact collectors and do not own commercial scoring, contentability, opportunity ranking or recommendation policy.
- Program 1 preserves separation between observed facts, normalized facts, derived features and business decisions.
- Early phases favor explainable features, qualification, opportunity thesis and human-reviewable rules over invented production scoring weights.
- Program 1 must preserve historical/provenance data required for downstream attribution and future learning.
- Qualified opportunity candidates, not arbitrary harvested products, are the intended Program 1 -> Program 2 output.
- Strategic success is measured by improved affiliate decision quality and downstream outcome yield per unit of effort, not raw products collected.

Governing record: `PROGRAM1_AFFILIATE_SUCCESS_STRATEGY.md`.

## Pending Validation / Implementation Gates
- Product Scoring Model v1 exact formula.
- Affiliate Offer Scoring Model v1 exact formula.
- Product/Offer identity validation against real Shopee data.
- observation normalization contract.
- real Shopee Android Scene inventory/signatures/selectors.
- Safe Anchor / transition / recovery validation.
- post-submit reconciliation strategy.
- video fingerprint algorithm/threshold validation.
- device-host/screen-stream capacity benchmark.
- numeric pacing/retry defaults from endurance testing.

The pending items block production completion of affected features, but do not block foundation code that is isolated behind the accepted ports/contracts and test doubles.

## ADR-047 — Controlled Evidence Promotion Is Required for Live Platform Assumptions
**Status: Accepted — 2026-09-05**

Live Shopee/browser/affiliate/Android assumptions may not move from laboratory status to production solely because one capture or one manual run succeeds.

Promotion follows the lifecycle:
`EXPERIMENTAL -> LAB_VALIDATED -> EVIDENCE_VALIDATED -> PRODUCTION_CANDIDATE -> PRODUCTION_APPROVED`.

At minimum, evidence validation requires independent repeated captures, explicit negative/failure evidence, provenance, fail-closed mismatch behavior and tests tied to the promoted profile/policy. Production approval additionally requires controlled operational/endurance evidence, rollback/runbook support and senior review.

CAPTCHA/access-control/anti-abuse boundaries must not be bypassed. A traffic/verification gate is evidence of a blocked state, not permission to increase retry rate or evade controls.

Governing records:
- `CONTROLLED_PRODUCTION_EVIDENCE_VALIDATION_STANDARD.md`
- `PRODUCTION_EVIDENCE_PROMOTION_MATRIX.md`
