# Step 1 — Product Discovery / Product Intelligence Baseline

Status: ACCEPTED DESIGN BASELINE

## Goal
Answer: **Which products should we market?**

## Architecture
Python Back Office is the brain; browser plugins are distributed Product Discovery Workers.

```text
Back Office -> Campaign/Sharding/Job Leasing -> Browser Workers 01..N -> Product Observations -> Normalize/Dedupe -> Product Intelligence -> Shortlist
```

## Worker Modes
- DISCOVER_SEARCH
- DISCOVER_CATEGORY
- DISCOVER_SHOP
- CAPTURE_CURRENT_PAGE
- REFRESH_QUERY / refresh cohort

Workers collect facts only; unavailable fields are null, never fabricated.

## Observation Contract
Includes worker/job/source context, collected_at, item_id/shop_id, product name/url/image, price/discount, sold/rating/review signals, seller/shop/promotion/voucher/shipping/stock signals, extractor/raw-payload versions.

## Identity
Candidate canonical natural identity: `(platform, shop_id, item_id)` pending real-data validation before production hard constraints.

## History
Product observations are append-oriented time snapshots. Back Office derives velocity, price movement, promotion, momentum and stability.

## Distributed Worker Farm
- worker identity and capabilities
- shared job queue
- bounded shard/job leasing
- heartbeat/health
- checkpoints
- ACK/outbox
- requeue after lease expiry
- no duplicate active shard assignment
- backpressure/adaptive pacing

## Browser UI Boundary
Chrome Extension Side Panel is the management UI where supported; normal management controls are not injected into Shopee DOM. Content Script is a replaceable Page Adapter; Extension Service Worker owns extension lifecycle/API/outbox.

## Data
Core concepts: workers, campaigns, campaign_shards, jobs, job_checkpoints, ingestion_batches, products, product_observations, worker/job events, product_scores, shortlist_entries.

Shared Core `jobs` remains lifecycle SSOT.

## Implementation Gates
- Product Scoring Model v1 exact formula
- product identity validation against real observations
- shared observation normalization contract
- Step1→Step2 final handoff schema
- endurance/pacing defaults from testing

No coding should embed unvalidated Shopee DOM structure into domain/business models.
