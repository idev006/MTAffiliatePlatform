# Domain Specification Index

Status: IMPLEMENTATION HANDOFF INDEX
Date: 2026-08-31

This directory contains implementation-facing domain/worker specifications. Governing project-level policies live one level above and take precedence when conflicts exist.

## Shared Core
- `SHARED_CORE_SPEC.md` — control plane, jobs, workers, idempotency, audit, configuration.
- `JOB_LEASE_PAUSE_RESUME_SPEC.md` — job lease/claim/renew/expiry protocol and worker-admission + job pause/resume, building on the worker registry (DESIGN — READY FOR REVIEW).

## Step 1 — Product Discovery / Intelligence
- `PRODUCT_DISCOVERY_WORKER_SPEC.md` — browser acquisition worker boundary, outbox, parser/versioning, fixture-based testing.
- `PRODUCT_INTELLIGENCE_SPEC.md` — headless Product Intelligence Engine, qualification/scoring/shortlist behavior.

## Step 2 — Affiliate Offer
- `AFFILIATE_OFFER_WORKER_SPEC.md` — distributed Offer Worker, account/session provenance, candidate collection, export workflow boundary.
- Governing Program 2 developer pack starts at `../PROGRAM2_DEVELOPER_HANDOFF.md` and includes strategy, architecture/UML, traceability, Kanban/cards, UX and automated-test architecture.

## Step 3 — Content Publishing / Android
- `CONTENT_PUBLISHING_SPEC.md` — Content Identity, Publish Plan, duplicate gate, irreversible submit boundary, Publishing Ledger.
- `ANDROID_SCENE_ENGINE_SPEC.md` — Scene/Process/Action model, recognition, selectors, transition/recovery, fake-driven Android automation testing.
- Governing Program 3 developer pack starts at `../PROGRAM3_DEVELOPER_HANDOFF.md` and includes strategy/safety, architecture/UML, traceability, Kanban/cards, UX and automated-test architecture.

## Governing Companion Documents
Before implementation, also read:
- `../PROJECT_STRUCTURE_AND_ENGINE_ARCHITECTURE.md`
- `../APPLICATION_AND_ENGINE_CONTRACTS.md`
- `../DATA_MODEL.md`
- `../TEST_STRATEGY_AND_QUALITY_GATES.md`
- `../UI_SHELL_AND_PRESENTATION_ARCHITECTURE.md`
- `../IMPLEMENTATION_READINESS_AND_DEFINITION_OF_READY.md`
- `../ENGINEERING_GOVERNANCE.md`
- `../DEVELOPMENT_HANDOFF_MASTER.md`

## Priority Rule
If an older migrated detail conflicts with a newer accepted ADR or governing architecture document, the newer governing decision wins. Update the affected spec before implementing the conflicting behavior.