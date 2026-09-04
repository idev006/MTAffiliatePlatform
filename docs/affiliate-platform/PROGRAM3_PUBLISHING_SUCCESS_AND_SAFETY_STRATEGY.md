# Program 3 — Publishing Success and Safety Strategy

Status: IMPLEMENTATION GOVERNING BASELINE
Date: 2026-09-04
Owner: Content Publishing / Android Automation

## Mission

Turn validated Program 2 offer handoffs and approved content into a reliable, duplicate-safe, auditable publication while protecting the account from blind retries, ambiguous submission outcomes and device/UI drift.

Program 3 must answer:
- Is this content allowed to publish now?
- Is the selected Program 2 offer/link still valid and fresh?
- Is the target account/device/job execution authorized?
- Is the Android Scene confirmed before each action?
- Did irreversible submit actually happen?
- If outcome is ambiguous, what evidence is required before any retry?
- What durable evidence may downstream attribution trust?

## Success principles

1. Durable publishing truth lives in Back Office, never Android memory/UI.
2. Shared Job Engine is the only executable job lifecycle authority.
3. Program 2 typed handoff is the commercial input authority.
4. PublishPlan is immutable/supersedable and versioned.
5. Duplicate prevention is enforced at planning, queue, pre-submit and confirmed-success boundaries.
6. Unknown/ambiguous Scene blocks business action.
7. POST_SUBMITTED is an irreversible boundary.
8. After POST_SUBMITTED, absence of success signal is not proof of failure.
9. Blind repost is prohibited.
10. Recovery is bounded, checkpointed and evidence-driven.
11. Worker/device identity is separate from target publishing account identity.
12. Critical logic must run headlessly with scripted fixtures and fake adapters.

## Canonical business flow

Program2OfferHandoff
-> Content/Video Identity
-> Build PublishPlan
-> Duplicate/Freshness/Capacity Validation
-> Shared Publish Job
-> Device/Worker Admission
-> Lease / Start
-> Scene Workflow
-> READY_TO_PUBLISH
-> Back Office Pre-Submit Guard
-> POST_SUBMITTED durable checkpoint
-> Verify / Reconcile
-> CONFIRMED_SUCCESS | CONFIRMED_FAILURE_SAFE_TO_RETRY | OUTCOME_UNKNOWN | NEEDS_HUMAN
-> Publishing Ledger
-> Attribution/Learning

## Business/operational KPIs

- duplicate-prevention success;
- confirmed publish success rate;
- ambiguous outcome rate;
- safe recovery rate;
- human-takeover rate;
- worker/device recovery time;
- publish plan rejection correctness;
- post/account/video/offer attribution completeness;
- repeated-submit incident count (target 0).

## Production evidence gates

Do not claim production-ready Android publishing until:
- real Shopee Scene/signature/selector evidence is validated;
- safe-anchor navigation is validated;
- product basket capacity by app/account/version is validated;
- submit-success and reconciliation evidence are validated;
- pacing/retry/recovery budgets are validated on devices;
- Program2->Program3 payload is proven in controlled integration;
- real-device restart/disconnect scenarios are exercised.

The system may still reach high engineering maturity when these uncertainties are isolated behind versioned policies/adapters and fail closed.
