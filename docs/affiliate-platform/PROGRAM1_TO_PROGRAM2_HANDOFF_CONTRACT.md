# Program 1 -> Program 2 Handoff Contract

Status: FOUNDATION CONTRACT v1
Date: 2026-08-31

## Purpose
Transfer an approved Product candidate from Product Intelligence to Affiliate Offer Intelligence without coupling Program 2 to Program 1 persistence internals.

## Envelope
Required metadata:
- schema_version
- message_id
- created_at
- correlation_id
- idempotency_key
- source_program = PROGRAM1
- target_program = PROGRAM2
- policy_version

## ProductCandidateForOfferDiscovery v1
Required fields:
- product_id: internal durable Product reference
- platform
- shop_id
- item_id
- product_name
- product_url when observed
- shortlist_decision_id
- shortlist_score
- shortlist_policy_version
- evidence_collected_at
- source_observation_ids[]

Optional evidence:
- observed current price
- seller/shop display facts
- sold/rating/review signals
- source query/campaign context

## Contract Rules
1. `(platform, shop_id, item_id)` remains a candidate natural identity pending real-data validation; internal `product_id` is the stable platform reference.
2. Program 2 must not recompute Program 1 shortlist authority.
3. Program 2 may reject/defer the candidate when required identity/evidence is incomplete or stale.
4. Re-delivery with the same idempotency key and same semantic payload is accepted idempotently.
5. Same idempotency key with changed semantic payload is `CONFLICT`.
6. Contract changes are versioned; consumers must not silently reinterpret old payloads.
7. No browser cookies, credentials or affiliate secrets cross this contract.

## Acceptance Result
Program 2 returns a durable admission result:
`ACCEPTED | ALREADY_ACCEPTED | DEFERRED_STALE | INVALID_IDENTITY | CONFLICT | REJECTED_POLICY`

Acceptance of this handoff does not mean an Offer exists; it means Offer discovery is eligible to be scheduled.
