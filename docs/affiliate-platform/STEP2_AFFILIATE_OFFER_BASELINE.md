# Step 2 — Affiliate Offer Automation Baseline

Status: ACCEPTED DESIGN BASELINE

## Goal
Answer: **For an approved product, which affiliate offer/seller/link should be used?**

## Pipeline
`Approved Product -> Offer Discovery -> Candidate Offers -> Eligibility/Ranking -> Preferred + Backup Offers -> Platform Selection/Export -> Import/Validation -> Affiliate Link Store -> Ready for Step 3`

## Distributed Worker Model
Affiliate Offer Workers reuse Shared Core worker registry, jobs, leasing, heartbeat, checkpoints, ACK/outbox, health and backpressure.

Workers advertise capabilities such as:
- DISCOVER_OFFER
- READ_OFFER_CANDIDATES
- SELECT_OFFERS
- EXPORT_AFFILIATE_LINKS
- REPORT_DOWNLOAD

PCs are not permanently bound to Step 1 or Step 2; scheduler assigns compatible jobs.

## Back Office Ownership
Back Office owns:
- hard filters
- ranking weights/profiles
- preferred/backup selection
- freshness policy
- export/import validation
- account-context-aware decisions

Workers collect facts and execute selected platform actions only.

## Offer Signals
May include price, base/extra commission, seller/shop quality, sales/rating/review signals, voucher/promotion, stock/availability, freshness and own conversion history when available.

## Account / Session Provenance
Worker identity != Affiliate Account identity. Offer observations/exports/links retain logical `affiliate_account_id` / session context where facts may differ by account.

Credentials/cookies/secrets do not belong in canonical Product/Offer records.

## Job Lifecycle SSOT
Shared Core `jobs`/`job_events` are authoritative for lifecycle, lease, retry, assignment and terminal state. Step-specific tables are domain detail only and must not become a second scheduler.

## Data Concepts
- affiliate_offer_campaigns
- offer job detail
- affiliate_offer_candidates
- affiliate_offer_observations
- affiliate_offer_scores
- affiliate_offer_selections
- affiliate_export_jobs/items/artifacts
- affiliate_links

One Product may have many Offers. Preferred Offer is a versioned decision, not permanent Product identity.

## Failure States
Include PRODUCT_NOT_FOUND, NO_OFFERS_FOUND, SESSION_REQUIRED, PAGE_CHANGED/SCHEMA_CHANGED, RETRYABLE_ERROR, NEEDS_HUMAN, FAILED, CANCELLED.

## Implementation Gates
- Affiliate Offer Scoring Model v1 exact rules
- offer identity validation
- observation normalization contract
- Step2→Step3 final handoff contract
- real export parser/format validation
- account-context behavior validation
