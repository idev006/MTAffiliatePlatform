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

## Pending Validation / Implementation Gates
- Product Scoring Model v1 exact formula.
- Affiliate Offer Scoring Model v1 exact formula.
- Product/Offer identity validation against real Shopee data.
- Step1→Step2 and Step2→Step3 final handoff schemas.
- observation normalization contract.
- real Shopee Android Scene inventory/signatures/selectors.
- Safe Anchor / transition / recovery validation.
- post-submit reconciliation strategy.
- video fingerprint algorithm/threshold validation.
- device-host/screen-stream capacity benchmark.
- numeric pacing/retry defaults from endurance testing.
