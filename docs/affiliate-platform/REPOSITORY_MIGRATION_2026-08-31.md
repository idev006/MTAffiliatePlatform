# Repository Migration Record — 2026-08-31

Status: ACCEPTED

## Decision
The authoritative repository / SSOT for the Affiliate Platform is now:

`idev006/MTAffiliatePlatform`

## Previous Location
Design work was initially developed under:

`idev006/MTShopeeMobile/docs/affiliate-platform/`

The previous repository remains useful as an existing Android/mobile implementation and historical engineering reference, but it is no longer the authority for the overall three-step platform.

## Migration Baseline
The new repository has been initialized with the governing/development-handoff baseline including:
- root project README
- Project Charter
- Logical Architecture
- Development Handoff Master
- Technology Stack
- API Communication / Plugin Architecture
- Database Concurrency / Portability Specification
- System Diagram Pack
- Agile Kanban Implementation Plan
- Engineering Governance
- Step 1 baseline
- Step 2 baseline
- Step 3 Scene-based Android Worker baseline

## SSOT Rule From This Date
New project-level requirements, architecture decisions, API/data contracts, diagrams, implementation plans and source code must be created or updated in `MTAffiliatePlatform`.

Changes made only in `MTShopeeMobile` must not silently redefine Affiliate Platform architecture.

If useful code/components are reused from MTShopeeMobile, they must conform to MTAffiliatePlatform contracts or be wrapped by an adapter.

## Monorepo Direction
MTAffiliatePlatform is a modular monorepo. Step 1, Step 2 and Step 3 are business domains of one platform, not separate repositories by default.

Repository separation in the future should be based on an independently justified deployment/release boundary, not merely because a component belongs to a different Step.

## Source Snapshot
The last source-repository Affiliate Platform handoff/decision baseline used during migration was on `MTShopeeMobile/main` around commit `8c59fc748b19908b6905ad9a836c1f2416ae0171` plus preceding Step-3 design commits. This record is provenance only; new decisions must be committed to MTAffiliatePlatform.
