# Program 2 -> Program 3 Handoff Contract

Status: FOUNDATION CONTRACT v1
Date: 2026-08-31

## Purpose
Transfer an approved commercial selection from Affiliate Offer Intelligence to Content Publishing without letting Android workers make commercial decisions.

## Envelope
Required metadata:
- schema_version
- message_id
- created_at
- correlation_id
- idempotency_key
- source_program = PROGRAM2
- target_program = PROGRAM3
- commercial_policy_version

## ApprovedOfferSelectionForPublishing v1
Required fields:
- selection_id
- product_id
- offer_id
- platform
- shop_id
- item_id
- affiliate_account_id
- affiliate_link_id
- affiliate_link_value/reference
- selected_at
- selection_policy_version
- freshness_expires_at or freshness_policy reference

Expected identity evidence:
- expected product name/title fingerprint or display name
- expected seller/shop identity
- expected price range/evidence when relevant
- source observation IDs

Optional:
- backup_offer_ids[]
- campaign tags/context
- selection score/explanation summary

## Contract Rules
1. Program 3 consumes the selected commercial identity; Worker must not independently choose a different seller/Product/Offer.
2. Program 3 may reject/defer when the link/selection is stale, revoked, incomplete or conflicts with duplicate/publishing policy.
3. Any fallback to a backup Offer requires a Back Office decision and a new/updated versioned PublishPlan; Worker cannot silently substitute.
4. Affiliate account context is explicit and distinct from Android device/account ownership.
5. Re-delivery is idempotent by idempotency key + semantic payload.
6. Secrets/cookies/session credentials are references managed outside canonical handoff payloads.
7. Contract changes require schema versioning and compatibility tests.

## Admission Result
Program 3 returns:
`ACCEPTED | ALREADY_ACCEPTED | DEFERRED_STALE | DUPLICATE_BLOCKED | INVALID_SELECTION | ACCOUNT_CONTEXT_MISMATCH | CONFLICT | REJECTED_POLICY`

Acceptance means the selection can participate in content planning/publish-plan creation; it is not proof of publish success.
