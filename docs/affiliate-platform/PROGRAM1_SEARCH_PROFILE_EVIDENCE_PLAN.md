# Program 1 — Search Profile Controlled Evidence Plan

Status: READY / NEEDS_REAL_DATA
Date: 2026-09-05
Card: P1-I
Evidence target: P1-E01
Profile: `shopee-search-lab-v1` version `1`
Current stage: `LAB_VALIDATED`

## Objective

Collect sufficient fresh, independent, authorized Shopee Search-surface evidence to decide whether `shopee-search-lab-v1` may move to `EVIDENCE_VALIDATED`.

This plan does not authorize scraping at scale. It is a bounded evidence campaign.

## Evidence campaign

Minimum successful evidence set:
1. at least two fresh supported Search captures;
2. vary at least one meaningful dimension per independent capture, preferably keyword plus browser restart/time;
3. retain exact profile/version/evidence-stage provenance;
4. preserve candidate identity links and product-name boundary evidence;
5. record page slot/hydration counts;
6. record verification/blocked outcome separately from empty/unsupported;
7. obtain at least one negative/failure evidence artifact from an ordinary observed state when available;
8. no CAPTCHA solving automation, anti-bot evasion or aggressive retry.

Preferred campaign shape:
```text
Evidence Set A
  Session 1 -> Search keyword A -> capture/manifest
  Browser restart
  Session 2 -> Search keyword B or page N -> capture/manifest
  Optional negative state -> blocked/unsupported manifest
  -> sanitize
  -> build fixtures
  -> parser/profile tests
  -> independent review
  -> HOLD / PROMOTE-to-EVIDENCE_VALIDATED / NEEDS_REAL_DATA
```

## Tool

Use:
`python tools/program1_capture_search_evidence.py`

The tool:
- fails closed on verification pages by default;
- writes structurally sanitized HTML;
- writes SHA-256 evidence manifests;
- uses `shopee-search-lab-v1` metadata from `mtaffiliate.common.evidence`;
- groups captures with `evidence_set_id`;
- records `capture_session_id`;
- produces a structural promotion-readiness summary;
- never turns a successful capture directly into approval.

## Required field review

| Field/signal | Current authority | P1-I decision |
|---|---|---|
| `(shop_id,item_id)` | identity parser candidate | verify repeatability; do not redefine identity casually |
| product name | LAB parser | verify stable card boundary |
| product URL | identity-backed | verify sanitized canonical shape |
| price | currently unknown/null in profile | promote only with direct repeated boundary evidence |
| sold signal | currently unknown/null | promote only with direct repeated semantics |
| rating/review | not production contract | evidence required before adding |
| seller/location/promo | not production contract | collect only if a business decision requires it and evidence supports semantics |

## Acceptance for EVIDENCE_VALIDATED review

All must be true:
- >=2 supported independent live captures;
- profile metadata consistent;
- no mixed/unknown code-version ambiguity without review;
- identity/name boundaries repeat;
- blocked/verification state remains fail-closed;
- sanitized fixtures committed when safe;
- parser/profile tests cover the observed structures and failure state;
- evidence refs are linked from profile metadata/docs;
- unresolved CRITICAL/HIGH findings = 0;
- senior Engineering + Process + QA review passes.

## Stop conditions

Immediately stop the campaign and set `BLOCKED` or `NEEDS_REAL_DATA` when:
- verification/traffic gate appears and ordinary human workflow cannot proceed;
- evidence would require guessing field meaning;
- capture provenance is missing;
- session/account data cannot be safely sanitized;
- platform behavior becomes ambiguous or inconsistent;
- repeated retries would be needed to force access.

## Current decision

`NEEDS_REAL_DATA`.

Cached/public retrieval from earlier work is retained only as background context and cannot satisfy this plan.