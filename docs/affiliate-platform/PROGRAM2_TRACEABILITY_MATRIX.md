# Program 2 — Traceability Matrix

Status: IMPLEMENTATION HANDOFF
Date: 2026-09-04

| ID | Business objective | Authority | Implementation target | Required verification |
|---|---|---|---|---|
| P2-UC-01 | accept only qualified upstream opportunities | Program2 Intake | application/program2_intake | contract/adversarial |
| P2-UC-02 | create idempotent offer discovery work | Shared Job Engine | application/program2_jobs | unit/integration |
| P2-UC-03 | register/lease compatible offer worker | Shared Core | worker registry/job engine | contract/resilience |
| P2-UC-04 | collect account-context candidate facts | Worker adapter | browser extension/profile | fixture/contract |
| P2-UC-05 | preserve durable offer history | Offer Repo | SQL/in-memory repo | SQLite/Postgres |
| P2-UC-06 | reject forged/stale job provenance | Job Engine | ingest guard | adversarial |
| P2-UC-07 | derive freshness/economic features | Offer Engine | feature policy | unit/property |
| P2-UC-08 | eligibility/qualification | Offer Engine | qualification policy | table-driven |
| P2-UC-09 | preferred + backup selection | Offer Engine | selection policy | deterministic |
| P2-UC-10 | persist decision provenance | Offer Repo | decision repository | restart/idempotency |
| P2-UC-11 | send bounded export instruction | Program2 App | worker command contract | contract |
| P2-UC-12 | correlate export artifact to job/account/selection | Program2 App | artifact model/repo | integration |
| P2-UC-13 | ambiguous export fails closed | Program2 App/Job | reconciliation | resilience |
| P2-UC-14 | stale selection blocks downstream | Program2 App | freshness gate | unit/contract |
| P2-UC-15 | Program3 consumes typed durable handoff | Program2 App | Program3OfferHandoff | contract |
| P2-UC-16 | audit/account/session provenance | Program2 domain | all decision records | audit |
| P2-UC-17 | no UI business authority | architecture | API/headless use cases | architecture gate |
| P2-UC-18 | downstream outcome learning-ready | analytics contract | evidence refs/decision id | future integration |

## Traceability chain

Business Goal -> QualifiedOpportunityHandoff -> OfferDiscoveryPlan -> Shared Job -> Offer Observation -> Feature Snapshot -> Qualification -> Selection Decision -> Link Artifact -> Program3 Handoff -> Outcome.
