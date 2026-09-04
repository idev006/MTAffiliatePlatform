# Program 2 — Agile Kanban

Status: ACTIVE
Date: 2026-09-04

## Policy

Each card: Document/DoR -> smallest vertical slice -> unit/component -> contract/integration -> failure injection -> CI -> audit/CAPA -> docs/evidence -> Done.

WIP limit: keep active architectural slices small; do not start concrete live Shopee adapter work before fake-driven contract is green.

## Ready / Priority

### P0
- P2-001 Typed Program1 QualifiedOpportunity intake
- P2-002 OfferDiscoveryPlan + Shared Job integration
- P2-003 job/worker/lease-bound observation ingestion
- P2-004 OfferFeatureSnapshot + freshness/data sufficiency
- P2-005 OfferQualificationDecision + deterministic OfferSelectionDecision
- P2-006 durable selection decision repository/migration
- P2-007 Program3OfferHandoff + stale selection gate
- P2-008 Program2 conformance gate + CI coverage scope

### P1
- P2-009 AffiliateLinkArtifact + validation/import
- P2-010 export command idempotency + OUTCOME_UNKNOWN reconciliation
- P2-011 worker lifecycle/restart/outbox
- P2-012 deterministic browser fixture E2E
- P2-013 structured observability/read models
- P2-014 UX shell for novice operator

### Evidence-gated
- P2-E01 real offer identity
- P2-E02 commission field semantics
- P2-E03 account/session behavior
- P2-E04 export/download artifact semantics
- P2-E05 freshness threshold calibration
- P2-E06 production scoring model
