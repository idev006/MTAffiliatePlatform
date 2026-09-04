# Shopee Program 1 Marketplace DOM Attempt — 2026-08-31

Status: CONTROLLED EVIDENCE SPIKE / SEARCH, CATEGORY, SHOP AND PRODUCT DETAIL DOM CAPTURED AFTER HUMAN CAPTCHA
Scope: Program 1 Product Discovery marketplace pages

## Attempt

Codex opened a logged-in browser session and attempted to navigate to:

```text
https://shopee.co.th/search?keyword=ssd
```

Shopee initially redirected the session to:

```text
https://shopee.co.th/verify/captcha?...scene=crawler_item...
```

## Decision

The project owner solved the CAPTCHA manually. The CAPTCHA / anti-bot boundary was not bypassed by Codex. This is consistent with the project governance:
- platform compliance is a design constraint;
- browser workers must assist authorized workflows, not bypass anti-abuse controls;
- unsupported or blocked pages must not be treated as successful empty observations.

## Search Result DOM Evidence

After manual CAPTCHA completion, `https://shopee.co.th/search?keyword=ssd` rendered a search result page with:

- title shape: `ssd - Prices and Deals - Aug 2026 | Shopee Thailand`
- search input: `input.shopee-searchbar-input__input`
- result item root: `li.shopee-search-item-result__item[data-sqe="item"]`
- observed result item count in DOM: `60`
- product link shape: `/...-i.<shop_id>.<item_id>?extraParams=...`
- common classes around item cards: `flex`, `flex-col`, `cursor-pointer`, `bg-white`, `line-clamp-2`, `text-shopee-primary`
- filter/sort controls: `Relevance`, `Latest`, `Top Sales`, `Price`
- filter checkbox values include shipping/location/discount style categories

Observed product-card field candidates:
- product identity from the product link path;
- product name from nearby visible card text;
- price from text containing `฿`, but not yet field-stable enough to ingest;
- sold signal from text containing `sold`, but not yet field-stable enough to ingest;
- image presence from card `img`;
- keyword provenance from URL query parameter `keyword`.

## Product Detail DOM Evidence

Representative product detail URL shape:

```text
https://shopee.co.th/...-i.<shop_id>.<item_id>?extraParams=...
```

Observed detail-page anchors/sections:
- title: `h1` with class observed as `auau1S`;
- breadcrumb container: `.page-product__breadcrumb`;
- category breadcrumb links:
  - `/Computers-Laptops-cat.11044958`;
  - `/Computer-Components-cat.11044958.11045198`;
  - `/Internal-Solid-State-Drive-cat.11044958.11045198.11046028`;
- shop section: `.page-product__shop`;
- shop name example text: `Fikwot Storage Store`;
- shop link examples:
  - `/yyf.th?categoryId=100644&entryPoint=ShopByPDP&itemId=<item_id>`;
  - `/yyf.th#product_list`.

Visible detail text included title, rating, ratings count, sold count, current price and variants. These fields remain evidence-only because the current implementation does not yet have saved fixture assertions for the exact field boundaries.

## Category Listing DOM Evidence

Representative category URL:

```text
https://shopee.co.th/Internal-Solid-State-Drive-cat.11044958.11045198.11046028
```

Observed category listing structure:
- title shape: `Internal Solid State Drive Online Sale - Computer Components | Computers & Laptops, Aug 2026 | Shopee TH`;
- result item root: `li.shopee-search-item-result__item[data-sqe="item"]`;
- observed result item count in DOM: `60`;
- product anchors: `a.contents[href*="-i."]`;
- product URL shape: `/...-i.<shop_id>.<item_id>?extraParams=...`.

This supports using the same identity-backed container strategy as search result pages.

## Shop Listing DOM Evidence

Representative shop URL:

```text
https://shopee.co.th/yyf.th#product_list
```

Observed shop listing structure:
- title shape: `สั่งซื้อสินค้าออนไลน์จาก Fikwot Storage Store | Shopee Thailand`;
- shop heading: `.section-seller-overview-horizontal__portrait-name`;
- `li.shopee-search-item-result__item[data-sqe="item"]` count: `0`;
- identity-backed product anchor count: `38`;
- product anchors: `a.contents[href*="-i."]`;
- product URL shape: `/...-i.<shop_id>.<item_id>?extraParams=...`.

This requires the Browser Plugin fallback path that scans identity-backed product anchors when the search/category root is absent.

## Implementation Outcome

Program 1 Browser Plugin was extended with a conservative evidence-gated current-page profile:

```text
shopee-current-page-lab-v1
```

The profile extracts only candidate product observations from already-visible pages where product identity is present in Shopee product URLs. Search and category listing pages now prefer `li.shopee-search-item-result__item[data-sqe="item"]` as the product container. Shop pages fall back to identity-backed product URL scanning. Product detail pages use the current URL identity first so the worker does not accidentally capture recommended products instead of the open product.

The first live extraction check confirmed identity and query extraction but showed that broad card text can confuse product model numbers with price or sold values. The lab profile therefore records `price_current = null` and `sold_signal = null` until a narrower field selector is validated by saved fixtures.

Supported candidate identity URL shapes:
- `-i.<shop_id>.<item_id>`
- `/product/<shop_id>/<item_id>`
- `?shopid=<shop_id>&itemid=<item_id>`

The profile fails closed with `PAGE_UNSUPPORTED` when it cannot find identity-backed product links.

## Live Plugin/Backend Verification

Local Program 1 API was run with:

```text
MTAFFILIATE_CONFIG=D:\dev\MTAffiliatePlatform\config\program1.toml
MTAFFILIATE_PORT=8000
```

Verified API status:

```json
{"service":"MTAffiliatePlatform API","status":"ok","enabled_programs":["program1"]}
```

Representative shop-page capture from `https://shopee.co.th/yyf.th#product_list`:
- captured observations: `22`;
- backend response status: `200`;
- backend response body shape: `{"batch_id":"browser-live-final-...","received_count":22,"accepted_count":22}`;
- SQLite confirmed persisted product rows with names such as `Fikwot FS810 2.5'' SATA SSD 128GB 256GB 512GB 3D NAND -WARRANTY 5 YEARS-เหมาะสำหรับโน๊ตบุ๊คและเดสก์ท็อป`;
- `price_current` and `sold_signal` remained `null` by design.

Defect found during live verification:
- shop-page capture initially selected the shop heading as `product_name` because broad metric filtering rejected card text containing `sold`;
- fix: keep product card text, strip trailing metric text beginning at `฿`, and only reject standalone metric-only strings;
- regression coverage added in Browser Plugin parser tests.

Transport hardening added after live verification:
- `PROGRAM1_QUEUE_BATCH` now reports whether a batch was queued, how many observations were queued, how many outbox messages were sent, how many remain, and the first delivery error;
- missing backend configuration no longer reports a misleading successful send;
- Side Panel attaches `source_worker_id` to observations when configured.

Operator process visibility added after plugin smoke testing:
- popup/side panel now shows explicit worker state instead of only raw JSON;
- visible states include `CONFIG_REQUIRED`, `READY`, `COLLECTING`, `QUEUED`, `DELIVERED`, `DELIVERY_BLOCKED` and `PAGE_UNSUPPORTED`;
- visible counters include captured observations, accepted observations, queued observations, delivered batches and remaining outbox messages;
- latest delivery/page error is visible without opening extension developer tools.
- auto-run pacing uses an operator-controlled randomized delay range slider from `0` to `600` seconds and schedules the next cycle with a fresh random delay after the current cycle finishes.

## Specialist Browser Plugin Review

A browser-plugin specialist review was requested for the Program 1 worker after the first operator panel implementation. The review accepted the direction but identified reliability gaps that matter for a production-style worker:

- repeated capture could inject `content.js` multiple times and redeclare top-level symbols;
- outbox removal trusted any HTTP 2xx response instead of validating the Back Office ACK;
- concurrent flushes could race through read/mutate/write local storage operations;
- optional host permissions were too broad for the current worker role;
- operator counters needed to distinguish observations from batches;
- product detail extraction should prioritize current PDP title sources instead of generic page/body text.

Implemented hardening from the review:

- content script listener registration is now guarded by `globalThis.__mtaProgram1CollectorLoaded`;
- content-script profile globals use repeat-injection-safe declarations;
- outbox flushing is serialized through a single drain promise;
- delivery removes outbox messages only after ACK `batch_id`, `received_count` and `accepted_count` match the submitted payload;
- side panel now separates captured observations, queued observations, delivered batches and accepted observations;
- extension host permissions are limited to Shopee and local Back Office origins;
- product detail pages use PDP-first name extraction from `h1` / title sources.

## Sanitized Fixture Regression Gate

Sanitized marketplace fixtures were added for the observed Program 1 browser-worker surfaces:

- search result listing;
- category listing;
- shop product listing;
- product detail page;
- CAPTCHA / unsupported page with no identity evidence.

The fixtures assert that the lab profile extracts only identity-backed observations, preserves source query provenance where present, strips metric text out of product names, keeps price/sold fields `null` until field boundaries are validated, and returns no observations when CAPTCHA or unsupported pages expose no product identity.

Local verification on 2026-09-04:

```text
node --test browser_plugin\program1\tests\*.test.cjs
34 passed

D:\dev\MTAffiliatePlatform\.venv\Scripts\python.exe -m ruff check tools src tests migrations
PASS
```

Program 1 local API was also started for browser-worker smoke testing:

```text
http://127.0.0.1:8000/
{"service":"MTAffiliatePlatform API","status":"ok","enabled_programs":["program1"]}
```

Playwright persistent-profile harness smoke verification:

```text
D:\dev\MTAffiliatePlatform\.venv\Scripts\python.exe tools\program1_open_playwright_browser.py --url about:blank --profile-dir .browser-profiles\program1-smoke --smoke-close-after 1 --require-extension
Browser: brave
Extension ID: mmljiahkjdnnphianfhgmdjjionggnji
Persistent profile: D:\dev\MTAffiliatePlatform\.browser-profiles\program1-smoke
```

## Follow-up Capture — 2026-09-04 (search surface, keyword=ssd)

Status: SANITIZED OBSERVATION / EVIDENCE ONLY — NO CODE CHANGE
Provenance: repeat capture of `https://shopee.co.th/search?keyword=ssd` (project owner, same logged-in marketplace surface as the study above). The raw DOM was reviewed against the current `shopee-current-page-lab-v2` profile and the parser was intentionally left unchanged.

### Conformance result — lab-v2 rules held on the real page

- result root `li.shopee-search-item-result__item[data-sqe="item"]` matches exactly;
- first `a[href]` inside every hydrated card is the product anchor (`a.contents`); the "Find Similar" `a` with query-only `shopid`/`itemid` always follows it, so the first-anchor rule picks the product;
- the identity regex parsed 7/7 representative real hrefs when run through the real parser code, including worst-case slugs: Thai text `(มือ2)`, emoji `✅🔥`, `M.2`, `2.5''`, `**` and trailing model tokens such as `-A0151171`;
- product-name boundary holds: `anchor.innerText` starts with the name and the cut at the first `฿` keeps clean names with no metric bleed;
- lazy skeleton slots: the list reserves 60 `li` but only ~15 are hydrated cards; skeleton `li` have no product anchor and are dropped by the existing no-anchor filter (no phantom observations);
- dedupe key `(shop_id, item_id)` is correct on the page (one shop, e.g. `62824618`, legitimately lists many distinct items);
- `source_query=ssd` provenance preserved; pagination observed as `1/12` with `/search?keyword=ssd&page=N` links.

### Price/sold field-boundary candidates (single-capture evidence)

Observed on all hydrated cards under the item-card module `shopee__item-card-centralisation 0.3.2`:

- price container: `div.max-w-full...text-shopee-primary`; current price is the first `div.truncate.flex.items-baseline` → `span ฿` + `span.truncate.text-base/5` (examples `฿989`, `฿1,180`, `฿6,799`);
- promo-only original price: sibling `div.text-shopee-black26.line-through`, absent when there is no promotion (e.g. a HIKSEMI card showed only the current price);
- discount chip text `-5%` … `-58%`; rating badge and sold signal sit in the same row;
- sold signal: `div.truncate.text-shopee-black87` values in two shapes — approximate `5k+ sold`, `1k+ sold`, `10k+ sold` and exact `72 sold`, `259 sold`, `645 sold` — both matching the metric-only text family the parser already uses to strip metrics out of names;
- shipping/EDT and location (`Bangkok`, `Nakhon Sawan`, `Overseas`) render in a separate row below.

These are structural candidates only. Per the project evidence gate they need a second independent capture before they become fixture assertions or a `search-card-th-v1` profile.

### Capture-yield finding

Each search page reserves 60 item slots but only ~15 are hydrated without scrolling, so one scroll-less capture yields ~15 observations, not 60. Repeated captures of the same URL return the same set unless scroll or pagination loads more. A scroll-load capture strategy remains a design question, not a parser defect.

### Fixture evidence kept

The sanitized search fixture (`tests/fixtures/shopee_marketplace_surfaces.fixture.json`) now includes representative cards from this capture: a Thai-slug name, promo and no-promo price shapes, and both exact and approximate sold formats. Parser assertions are unchanged (`price_current`/`sold_signal` remain `null` by design); the content-parser suite still passes (14/14).

### Second independent capture — deferred by anti-bot rate limit (2026-09-04)

A repeat capture of `https://shopee.co.th/search?keyword=ssd&page=1` and a first capture of `https://shopee.co.th/search?keyword=keyboard` were attempted with a new Playwright persistent-profile capture tool (`tools/program1_capture_search_evidence.py`, profile `.browser-profiles/shopee-program1`, headed so a human can verify).

Observed outcome:
- Shopee forced the session to `/verify/captcha?...scene=crawler_item...`, then to a traffic-verification dialog rendered as "โปรดลองอีกครั้งในภายหลัง / การยืนยันไม่สามารถดำเนินการได้ในขณะนี้" ("please try again later; verification cannot be completed now");
- the human operator reports this follows repeated logins from the same profile, i.e. an anti-abuse suspicion window, not a normal CAPTCHA;
- no CAPTCHA/verification bypass was attempted — consistent with project governance;
- the blocked page state was kept as controlled evidence: `.browser-profiles/captures/2026-09-04/01_search_main_fragment.html` + `01_search_stats.json` (gitignored scratch, not a committed selector contract).

Consequence: the price/sold boundary candidates remain single-capture evidence. The second independent capture stays an open gate and should be retried only after the suspicion window cools and a human can complete normal verification.

### Live auto-run attempt — block confirmed at network level, not only account level (2026-09-04)

A live validation of the 0.1.13 pagination-aware auto-run was attempted with `tools/program1_paginated_autorun_live.py` using a **fresh guest context** (brand-new profile `.browser-profiles/autorun-guest`, extension 0.1.13, no login), explicitly to avoid touching the flagged logged-in profile.

Observed outcome:
- the very first request to `https://shopee.co.th/search?keyword=SATA%20SSD%20512GB` was redirected by Shopee to `/verify/traffic/error?home_url=...&is_logged_in=false&next=...&tracking_id=74573583466-4c4b-47c9-800e-980952f7b63f&type=4` — `is_logged_in=false` proves the traffic gate applies to anonymous sessions too, i.e. the suspicion window sits on the network/device fingerprint, not just on login frequency;
- the 0.1.13 anti-bot classification was validated against this real page: the side panel reported state `PAGE_BLOCKED_BY_ANTIBOT` with the message *"Blocked by Shopee verification/anti-bot; not treated as a harvest (<verify URL>)"* — under pre-0.1.13 code this same page was mislabeled as generic `PAGE_UNSUPPORTED`;
- the run aborted after the single blocked probe (fail-closed, no repeated hammering);
- incidental positive: the fresh profile registered with the local Back Office cleanly (`Registry: registered (autorun-live-guest)`), re-confirming the registry flow from a brand-new profile.

Consequence: the **live last-page finish behavior remains unverified** — it is exercised only by the content-parser unit suite (pagination parsing, `has_next: false` finish). The live run should be retried, without further probes until then, after the network-level traffic gate cools; the driver already adapts to whichever keyword listing it finds and walks it to the genuine last page.

### OPERATOR TO-DO — retry the second independent capture after cooldown

> **Blocked since:** 2026-09-04 (network-level traffic gate; guest probe `is_logged_in=false` → `/verify/traffic/error`, type 4).
> **Revisit on/after:** 2026-09-05 — only after normal Shopee browsing verifies cleanly from this network/device. Do **not** probe earlier; repeated attempts extend the window.

1. Confirm a normal logged-in Shopee session loads listings without the verification page.
2. Run `D:\dev\MTAffiliatePlatform\.venv\Scripts\python.exe tools\program1_capture_search_evidence.py` (page 2 of `keyword=ssd` + a second keyword) for the second independent price/sold evidence capture.
3. When the network gate clears, the pagination-aware auto-run can also be live-run via `tools\program1_paginated_autorun_live.py` to record the real last-page finish.
4. Record outcomes as a dated follow-up section in this file; until step 2 lands, the price/sold boundary candidates stay single-capture evidence.

## Remaining Evidence Needed

Additional validation still needed before promotion:
- second search result page with a different keyword;
- repeated captures after logout/login and browser restart;
- explicit field-boundary tests for price, sold, rating, seller and image fields.

After those captures, the next implementation step is to save sanitized fixtures and promote the lab profile into versioned per-surface profiles such as:
- `search-card-th-v1`
- `category-card-th-v1`
- `shop-card-th-v1`
- `product-detail-th-v1`

These profiles remain validation-gated until repeated captures prove stable field boundaries.
