# Program 3 — Traceability Matrix

Status: IMPLEMENTATION HANDOFF
Date: 2026-09-04

| ID | Objective | Authority | Implementation target | Verification |
|---|---|---|---|---|
| P3-UC-01 | accept typed fresh Program2 handoff | Program3 planning | application/program3_planning | contract |
| P3-UC-02 | register/verify content identity | Content Identity | content engine/repo | unit/integration |
| P3-UC-03 | build immutable PublishPlan | Program3 app | planning service | component |
| P3-UC-04 | duplicate gate before queue | Publishing Guard | publishing engine | unit |
| P3-UC-05 | create Shared publish job | Shared Job Engine | Program3 jobs | integration |
| P3-UC-06 | device/worker admission | Device Host | device engine/registry | unit/resilience |
| P3-UC-07 | confirm Scene before action | Scene Engine | worker executor | fixture/component |
| P3-UC-08 | checkpoint verified transitions | Shared Job/checkpoint | worker/app | component |
| P3-UC-09 | pre-submit duplicate/freshness guard | Publishing Engine | pre-submit service | adversarial |
| P3-UC-10 | durable POST_SUBMITTED | Program3 Back Office | submission record/checkpoint | idempotency/restart |
| P3-UC-11 | no blind repost after ambiguity | Publishing Engine | reconciliation service | resilience |
| P3-UC-12 | confirmed success ledger | Publishing Ledger | repo/application | SQLite/concurrency |
| P3-UC-13 | unknown outcome -> NEEDS_HUMAN | Publishing Engine/Job | reconciliation | adversarial |
| P3-UC-14 | UI has no business authority | architecture | headless API/app | conformance |
| P3-UC-15 | publish evidence attribution | ledger | decision/handoff refs | audit |
| P3-UC-16 | controlled human takeover | operator boundary | API/read model | contract |

Traceability:
Program2 handoff -> PublishPlan -> Shared Job -> Device/Worker lease -> Scene checkpoints -> PreSubmitDecision -> SubmissionRecord -> ReconciliationDecision -> PublishingLedger -> Attribution.
