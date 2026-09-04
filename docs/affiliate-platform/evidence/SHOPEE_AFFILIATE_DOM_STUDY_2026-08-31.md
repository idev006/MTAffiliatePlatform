# Shopee Affiliate DOM Study — 2026-08-31

Status: SANITIZED OBSERVATION / NOT A PRODUCTION SELECTOR CONTRACT
Source: logged-in Brave browser session controlled by the project owner
Scope: Shopee Thailand Affiliate dashboard and offer pages

## Safety Boundary

This note records page structure only. It does not store cookies, local storage, session tokens, credentials, OTPs, account secrets, raw revenue values, payout details or unsanitized user/account data.

The observations below are evidence for future adapter/profile work. They must not be treated as a frozen production parser, selector profile or canonical Shopee identity contract without additional controlled validation.

## Pages Observed

| Page | URL | Observed Shape |
|---|---|---|
| Dashboard | `https://affiliate.shopee.co.th/dashboard` | React/Ant Design shell with sidebar, date range inputs, metrics panels and a product performance table |
| Shopee Offer | `https://affiliate.shopee.co.th/offer/shopee_offer` | Search input, offer table and batch link action |
| Product Offer | `https://affiliate.shopee.co.th/offer/product_offer` | Search input, product card list, per-card checkbox, per-card `Get Link`, batch link action |
| Custom Link | `https://affiliate.shopee.co.th/offer/custom_link` | Ant Design form with textarea for Shopee URLs, sub-id inputs and `Get Link` action |

## Application Shell

Common shell:
- root node: `div#root`
- layout classes: `ant-layout`, `ant-layout-content`, `ant-layout-sider`, `sider`, `aff-sider`
- header class: `nav-header`
- sidebar id: `aff-sider`
- menu system: Ant Design `ul.ant-menu`, `li.ant-menu-item`, `li.ant-menu-submenu`

Observed sidebar routes:
- `/dashboard`
- `/offer/shopee_offer`
- `/offer/brand_offer`
- `/offer/product_offer`
- `/offer/offer_for_me`
- `/offer/custom_link`
- `/campaign/campaign_list`
- `/creative/product_feed`
- `/report/conversion_report`
- `/report/click_report`
- `/payment/billing`
- `/payment/payout_record`
- `/open_api`

## Dashboard Structure

Observed metrics headings:
- `Key Metrics`
- `Clicks`
- `Orders`
- `Est. Commission(฿)`
- `Items Sold`
- `Order Amount(฿)`
- `New Buyers`

Date range inputs:
- `input.ant-calendar-range-picker-input` with placeholder `Start date`
- `input.ant-calendar-range-picker-input` with placeholder `End date`

Performance table:
- selector shape: `table.ant-table-fixed`
- headers: `Product`, `Items Sold`, `Est. Commission(฿)`, `Action`
- rows use Ant Design table cell classes such as `ant-table-row-cell-break-word`

## Shopee Offer Page Structure

Route: `/offer/shopee_offer`

Observed heading:
- `Shopee Offer`

Search:
- `input.ant-input.ant-input-lg`
- placeholder: `Search for Shopee Offer`
- search button: `button.ant-btn.ant-input-search-button.ant-btn-primary`

Table:
- headers: `Offer Name`, `Offer Period`, `Offer Type`, `Commission Rate`, `Action`
- empty-state heading observed: `No Data`

Actions:
- `Search`
- `Batch Get Link`

## Product Offer Page Structure

Route: `/offer/product_offer`

Observed heading:
- `Product Offer`

Search:
- `input.ant-input.ant-input-lg`
- placeholder: `Search for all Shopee Products`

List/card shape:
- wrapper candidates: `.product-offer-item`, `.AffiliateItemCard`
- card root classes include `ItemCard__container`, `ItemCard__imageSection`, `ItemCard__contentSection`
- product name: `.ItemCard__name`
- labels/badges: `.ItemCard__labels`, `.ItemCard__label`
- price: `.ItemCard__price`, `.ItemCardPrice__wrap`, `.price`
- sold signal: `.ItemCardSold__wrap`
- commission signal: `.ItemCard__custom`, `.commRate`
- per-card checkbox: `input.ant-checkbox-input`
- per-card action: `button.ant-btn.AffiliateItemCard__getlinkBtn.ant-btn-sm`
- batch action: `button.ant-btn.ant-btn-primary` with visible text `Batch Get Link`
- product images load from `https://down-bs-th.img.susercontent.com/...`

Observed product detail link shape:

```text
/offer/product_offer/[product_id]?trace=[encoded]
```

The visible card list rendered 20 product items; a broad combined selector matched both outer and inner card elements and therefore counted 40 elements. A future parser should pick one stable root level and avoid double-counting.

## Custom Link Page Structure

Route: `/offer/custom_link`

Observed heading:
- `Custom Link`

Form:
- `form.ant-form.ant-form-horizontal.sub-id-form`
- main URL textarea: `textarea.ant-input`
- sub-id inputs:
  - `input#customLink_sub_id1.ant-input`
  - `input#customLink_sub_id2.ant-input`
  - `input#customLink_sub_id3.ant-input`
  - `input#customLink_sub_id4.ant-input`
  - `input#customLink_sub_id5.ant-input`

Action:
- `button.ant-btn.mkt-btn.ant-btn-primary` with visible text `Get Link`

Observed data attributes on this page:
- `data-__meta`
- `data-__field`

## Early Adapter Implications

Program 2 `Product Offer` acquisition should start as a versioned, evidence-gated parser profile around card structure, not table structure.

Candidate extraction fields from visible DOM:
- affiliate platform: inferred from route/domain, not DOM text alone
- product detail route id from `/offer/product_offer/[product_id]`
- product name from `.ItemCard__name`
- price text from `.ItemCard__price` / `.ItemCardPrice__wrap`
- sold signal from `.ItemCardSold__wrap`
- commission rate from `.commRate`
- image reference from card `img[src]`
- link action availability from `AffiliateItemCard__getlinkBtn`

Program 2 `Shopee Offer` acquisition appears table-based and should use a separate parser profile from `Product Offer`.

Program 2 `Custom Link` is a side-effecting form. Automation of the `Get Link` action requires explicit command idempotency/reconciliation design before implementation. This study did not submit that form.

## Open Questions / Evidence Gates

- Confirm whether class names are stable across locale, account, campaign and deployment version.
- Confirm whether the product detail route id maps to `item_id`, `offer_id` or another affiliate-specific identity.
- Confirm whether trace query parameters are required for action context or can be treated as transient evidence.
- Confirm whether `Get Link` opens a modal, triggers a network call, or starts a downloadable/export artifact.
- Capture sanitized network/API envelope only after reviewing whether endpoint payloads contain account identifiers or sensitive data.
- Add fixture-based parser tests only after a second controlled capture confirms stable card roots and field boundaries.
