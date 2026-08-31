# Product Intelligence Specification

Status: IMPLEMENTATION HANDOFF BASELINE
Owner Domain: Product Intelligence
Migrated to authoritative repo: 2026-08-31

> Governing implementation rule: Product Intelligence is a headless/testable engine. Data acquisition is replaceable. Exact scoring weights remain a production validation gate.

## 1. Purpose

The Product Intelligence domain converts a very large Shopee product universe into a small, explainable, actionable shortlist of products worth producing affiliate content for.

The domain answers: **Which products should we market next, and why?**

It is not merely a scraper. Data acquisition is replaceable; decision quality is the core capability.

## 2. Inputs

Accepted source adapters may include:
- Browser Extension Discovery Workers
- Shopee exports available to the user
- Authorized APIs
- User-imported CSV/XLSX/JSON datasets
- Historical internal catalog snapshots
- Other approved external datasets

All sources normalize into a common Product Observation contract.

## 3. Canonical Product Identity

Candidate Shopee identity is `(platform, shop_id, item_id)` pending real-world validation.

A source-specific raw ID, URL or title must not replace canonical identity without an approved ADR.

## 4. Observation Model

Observations are append-oriented immutable facts. Current projections are derived.

Minimum conceptual fields:
- source/provenance
- worker/context
- collected_at
- query/category/shop context
- item_id/shop_id
- product name/URL/category
- shop/seller metadata when available
- current/original price
- sold signal
- rating/review_count
- location/image/promotion signals when available
- raw evidence/reference
- extractor/schema version

Unavailable data remains unknown/null.

## 5. Discovery Strategy

Support multiple strategies:
- Keyword universe
- Category discovery
- Shop discovery
- Trend-driven discovery
- Expansion from proven winners
- Manual seed products

Discovery jobs are resumable and idempotent through Shared Job Engine.

## 6. Normalization

Normalization covers:
- numeric price parsing
- timestamps
- URLs
- product/shop IDs
- category aliases
- textual whitespace/encoding
- observation-level duplicate handling

Raw provenance remains traceable.

## 7. Qualification Filters

Hard filters are versioned/configurable, including:
- allowed/excluded categories
- min/max price
- minimum rating
- minimum sales/review signal
- excluded sellers/shops
- insufficient data policy
- product freshness
- commercial/policy exclusions

Rejected products retain reason codes.

## 8. Product Intelligence Engine

Engine responsibilities:
- derive features from normalized facts/history;
- apply qualification rules;
- calculate explainable opportunity score;
- rank candidates;
- build shortlist decisions;
- emit component scores/reasons/model version;
- remain deterministic for identical normalized facts + model version.

Engine does not:
- parse Shopee DOM;
- access PySide6;
- issue SQL directly;
- control browser workers.

## 9. Opportunity Score

Baseline model is explainable/rule-based before ML.

Candidate dimensions:
- Demand
- Sales velocity/trend
- Price fit
- Rating/review confidence
- Seller quality
- Competition
- Commission potential
- Promotion/voucher attractiveness
- Content demonstration potential
- Content multiplication potential
- Historical internal performance

Output:
- total score (target normalized range such as 0–100 once formula is frozen)
- component scores
- model/ruleset version
- explanation/reasons
- confidence/data sufficiency

No opaque score is acceptable for baseline production.

Exact formula/weights remain open until validated.

## 10. Content Multiplication Potential

Estimate materially different content angles, e.g.:
- problem/solution
- demo
- before/after
- comparison
- unboxing
- test
- how-to
- use case
- review
- feature highlight

This matters because Product 1:N Videos is a core business relationship.

## 11. Shortlisting

Support configurable funnels, e.g.:
`100,000 observed -> 10,000 qualified -> 1,000 scored -> 100 candidates -> 10–20 production targets`.

Every shortlist record preserves:
- product identity
- score/rank
- timestamp
- model/ruleset version
- reasons
- reviewer/approval state

## 12. Output Contract

Approved products become stable ProductCandidate references for Affiliate Offer domain.

Minimum semantic output:
- product_id/canonical external identity
- product name
- source/context provenance
- opportunity score + explanation
- target offer count/policy reference
- priority
- approval state
- model/ruleset version

Final DTO schema is governed by `../APPLICATION_AND_ENGINE_CONTRACTS.md`.

## 13. Testability

Unit/component suites must verify without browser/network/UI:
- normalization rules;
- qualification matrices;
- scoring component calculations;
- insufficient-data behavior;
- deterministic ranking;
- tie/boundary behavior;
- shortlist reason generation;
- model version provenance;
- historical feature calculation;
- idempotent application use cases.

Property-based tests are recommended for score bounds/normalization and identity rules.

## 14. Non-Functional Requirements

- Architecture target >=1,000,000 observations without domain redesign.
- Worker failure cannot delete persisted history.
- Discovery workers are disposable.
- Back Office is SSOT.
- Acquisition/scoring logic are independently replaceable.
- Major decisions are auditable.

## 15. Acceptance Criteria

1. Different source adapters can feed the same normalized model.
2. Duplicate canonical products merge identity while observations remain historical.
3. A ruleset can reject and explain products.
4. Every shortlisted product has explainable decision provenance.
5. Discovery restarts do not duplicate logical durable work.
6. Stable Step 1 output can feed Offer domain.
7. Product Intelligence Engine runs entirely headless with fake/in-memory repositories.

## 16. Open Production Gates

- Exact Product Scoring Model v1 formula/weights.
- Minimum data sufficiency required for score vs REVIEW/INSUFFICIENT_DATA.
- Initial keyword-universe generation method.
- Refresh intervals by product class.
- External/public signal selection.
- Final Product identity validation against real Shopee data.