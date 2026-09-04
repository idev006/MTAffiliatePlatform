# Program 1 Controlled Evidence Attempt — 2026-09-05

Status: HOLD / NEEDS_REAL_DATA
Target: P1-E01 Shopee search result profile

## Controlled observation

Two public Shopee search URLs were retrieved through the available web retrieval channel:
- `search?keyword=ssd`
- `search?keyword=ssd%201tb`

Both retrieved representations contained ordinary search-result content rather than a verification/captcha page. Product rows exposed human-readable product name, price, rating and location text.

## Why this is NOT promotion evidence

The retrieval channel reported that the underlying pages were crawled weeks earlier. Therefore these observations are not treated as independent live browser-session captures on 2026-09-05.

Under `CONTROLLED_PRODUCTION_EVIDENCE_VALIDATION_STANDARD.md`, cached/search-engine retrieval cannot satisfy the independent live-capture requirement.

## Promotion decision

`HOLD / NEEDS_REAL_DATA`

P1-E01 remains `LAB_VALIDATED`.

## Required next evidence

- fresh authorized browser-session capture of search surface;
- second fresh independent capture varying keyword/page/session/restart;
- explicit identity/name/price/sold/rating boundaries;
- blocked/verification negative evidence;
- sanitized fixture + parser contract tests tied to the promoted profile.

## Safety

No CAPTCHA bypass, access-control circumvention, anti-bot evasion or aggressive retry was performed.