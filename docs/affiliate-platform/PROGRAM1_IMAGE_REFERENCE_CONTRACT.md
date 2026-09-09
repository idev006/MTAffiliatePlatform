# Program 1 primary image reference contract

Date: 2026-09-09. Card: P1-IMG-1. Status: IMPLEMENTED / IN VERIFY.

## Decision and value

Operators need a traceable primary image reference when comparing observed products. Back Office stores the observed URL as evidence, not as proof of ownership or a downloaded artifact. This additive foundation follows Program 1 strategy, architecture, observation provenance and atomic ACK contracts.

## Contract

- Add optional primary_image_url to ProductObservation; absent/null means no image evidence. Retain source page URL, collected_at and extractor_version as existing provenance.
- Accept absolute HTTP(S) URLs with a host and no embedded credentials. Reject other schemes and invalid URLs. Preserve the accepted string; never fetch it during ingestion or within a SQL transaction.
- Add a nullable database column; existing rows remain null. Both product repository and atomic batch ingestor round-trip the field after restart.
- Existing batch fingerprints must remain identical when primary_image_url is absent/null. Include a non-null image reference in the fingerprint. Changed image under the same observation/batch identity remains a conflict.
- One primary reference only. No download status, thumbnail cache, outbound HTTP, rights assertion, deduplication by image, historical backfill or image proxy in this slice.
- Shopee profiles continue omitting the field until fresh evidence proves which image belongs to each product card. No guessed selectors or CDN rules.
- GET /api/v1/program1/products/{platform}/{shop_id}/{item_id}/observations returns stored observations newest first, with limit 1..100 (default 50); unknown product returns an empty list. Uses existing observation_history port. Response is bounded; storage-level pagination is deferred. URLs are returned as data and never fetched. No full catalog UI in this slice.

## Acceptance

Unit/API validation, legacy fingerprint compatibility, real SQLite migration with old data, restart/readback, exact replay and changed-image conflicts. No changes to Program 2/3 policy. Required pipeline/CI and truthful evidence status. CRITICAL/HIGH unresolved design issues: zero for storage-only foundation; live extraction/download remain separate gates.
