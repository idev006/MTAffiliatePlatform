# Program 2 — Affiliate Offer Success Strategy

Status: IMPLEMENTATION GOVERNING BASELINE
Date: 2026-09-04
Owner: Affiliate Offer Intelligence

## Mission

Convert a qualified Program 1 opportunity into the best currently actionable affiliate offer set, with evidence, provenance, freshness, account context and recovery semantics sufficient for profitable and reliable downstream content publishing.

Program 2 must answer:

> For this qualified product opportunity and affiliate account context, which offer should we use now, what backups should we retain, why, how fresh is the evidence, and what must happen before Program 3 may publish?

## Business success principles

1. Program 1 qualification is the upstream admission gate. Raw arbitrary products do not become Program 2 commercial work by default.
2. Highest commission is not automatically best. Decision quality considers earnings opportunity, availability, seller confidence, price/value, demand/social proof, freshness, account context and uncertainty.
3. Observed facts are separated from derived features and commercial decisions.
4. Account/session provenance is mandatory whenever the observed offer depends on affiliate account context.
5. A selected offer is time-sensitive. Freshness is a business invariant, not UI decoration.
6. Preferred + backups are retained because offer availability and economics can change.
7. Program 3 consumes durable qualified selection/link artifacts, never worker memory.
8. Unknown or ambiguous export/link outcome fails closed.
9. Exact production scoring weights remain evidence-gated. Until validated, qualification and explainable rules may drive selection.
10. Downstream order/commission outcomes should later feed the learning loop.

## Canonical business flow

Program1 QualifiedOpportunityHandoff
-> Offer Discovery Plan
-> Shared Job
-> Affiliate Worker Lease
-> Candidate Offer Observations
-> Durable ACK / History
-> Normalize / Account Context / Freshness
-> Offer Feature Snapshot
-> Eligibility / Qualification
-> Explainable Selection
-> Preferred + Backups
-> Export / Link Artifact
-> Import / Validate
-> Program3 Ready Handoff
-> Outcome Attribution / Learning

## Strategic decision dimensions

- commission opportunity;
- effective price/value;
- availability;
- seller/reputation confidence;
- rating/review/sold evidence;
- voucher/promotion context;
- freshness;
- affiliate-account fit;
- operational/export readiness;
- uncertainty/risk;
- downstream conversion history when available.

## Action vocabulary

- SELECT_NOW
- WATCH
- HOLD
- REJECT
- NEEDS_EVIDENCE
- NEEDS_SESSION
- NEEDS_HUMAN

## Production gates

Program 2 must not claim production-ready scoring or offer identity until:
- offer external identity is validated against real evidence;
- commission field semantics are validated;
- freshness thresholds are benchmarked/approved;
- export/link artifact semantics are validated;
- account/session provenance is proven;
- final Program2->Program3 DTO is verified;
- live worker recovery and ambiguous export outcomes are tested.

## North-star metrics

Technical:
- durable observation acceptance rate;
- duplicate/replay safety;
- stale selection detection rate;
- worker recovery success;
- export/import correlation correctness.

Business:
- selected-offer availability at publish time;
- commission realization;
- conversion rate;
- net commission per qualified opportunity;
- backup failover success;
- regret rate versus alternative offers when measurable.
