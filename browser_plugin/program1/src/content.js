// Production Shopee collection profiles remain evidence-gated. The live-page
// profile below extracts only candidate product identity from visible URLs and
// returns PAGE_UNSUPPORTED instead of guessing when identity is not present.

var FIXTURE_PROFILE = "fixture-profile-v1";
var SHOPEE_CURRENT_PAGE_PROFILE = "shopee-current-page-lab-v2";

function parseShopeeProductIdentityFromUrl(value) {
  if (!value) return null;
  let url;
  try {
    url = new URL(value, window.location.href);
  } catch (_error) {
    return null;
  }

  const productPath = url.pathname.match(/\/product\/(\d+)\/(\d+)(?:\/|$)/);
  if (productPath) {
    return { shop_id: productPath[1], item_id: productPath[2] };
  }

  const itemPath = url.pathname.match(/(?:^|-)i\.(\d+)\.(\d+)(?:\/|$)/);
  if (itemPath) {
    return { shop_id: itemPath[1], item_id: itemPath[2] };
  }

  const shopId = url.searchParams.get("shopid") || url.searchParams.get("shop_id");
  const itemId = url.searchParams.get("itemid") || url.searchParams.get("item_id");
  if (shopId && itemId && /^\d+$/.test(shopId) && /^\d+$/.test(itemId)) {
    return { shop_id: shopId, item_id: itemId };
  }

  return null;
}

function normalizeText(value) {
  return (value || "").replace(/\s+/g, " ").trim();
}

function isMetricOnlyText(value) {
  const text = normalizeText(value);
  return /^(?:฿\s*[\d,.]+|[\d,.kK+]+\s*(?:sold|ขายแล้ว)|[\d.]+\s*(?:rating|ratings?))$/i.test(text);
}

function cleanProductNameText(value) {
  const text = normalizeText(value);
  const withoutMetrics = text.replace(/\s*฿[\s\S]*$/, "").trim();
  return withoutMetrics || text;
}

function numericText(value) {
  if (!value) return null;
  const match = String(value).replace(/,/g, "").match(/\d+(?:\.\d+)?/);
  return match ? match[0] : null;
}

function integerText(value) {
  const number = numericText(value);
  return number === null ? null : Number.parseInt(number, 10);
}

function randomObservationId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return `obs-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function inferShopeeSurfaceFromUrl(value) {
  let url;
  try {
    url = new URL(value || window.location.href, window.location.href);
  } catch (_error) {
    return "unknown";
  }

  if (url.pathname === "/search") return "search";
  if (/-cat\.\d+(?:\.\d+)*/.test(url.pathname)) return "category";
  if (parseShopeeProductIdentityFromUrl(url.href)) return "product_detail";
  if (url.hostname === "shopee.co.th" && /^\/[^/]+$/.test(url.pathname)) return "shop";
  return "unknown";
}

function nearestProductContainer(anchor) {
  let current = anchor;
  for (let depth = 0; current && depth < 6; depth += 1) {
    const text = normalizeText(current.innerText || current.textContent);
    if (
      current.querySelector?.("img") &&
      /฿|\bsold\b|ขายแล้ว|คะแนน|rating/i.test(text)
    ) {
      return current;
    }
    current = current.parentElement;
  }
  return anchor;
}

function productTargetsForCurrentPage() {
  const searchItems = [...document.querySelectorAll('[data-sqe="item"].shopee-search-item-result__item')];
  if (searchItems.length) {
    return searchItems
      .map((container) => ({
        anchor: container.querySelector?.("a[href]"),
        container,
      }))
      .filter((target) => target.anchor);
  }
  return [...document.querySelectorAll("a[href]")]
    .filter((anchor) => parseShopeeProductIdentityFromUrl(anchor.getAttribute("href")))
    .map((anchor) => ({
      anchor,
      container: nearestProductContainer(anchor),
    }));
}

function readProductName(anchor, container) {
  const candidates = [
    anchor.innerText || anchor.textContent,
    anchor.getAttribute("title"),
    anchor.getAttribute("aria-label"),
    container.querySelector?.("[data-sqe='name']")?.textContent,
    container.querySelector?.("[class*='name' i]")?.textContent,
    document.querySelector("h1")?.textContent,
    document.title,
  ];
  for (const candidate of candidates) {
    const text = normalizeText(candidate);
    if (text && !isMetricOnlyText(text)) return cleanProductNameText(text).slice(0, 240);
  }
  return "Shopee product";
}

function readCurrentProductDetailName() {
  const candidates = [
    document.querySelector("h1")?.textContent,
    document.querySelector("[data-sqe='name']")?.textContent,
    document.title?.replace(/\s*\|\s*Shopee.*$/i, ""),
  ];
  for (const candidate of candidates) {
    const text = normalizeText(candidate);
    if (text && !isMetricOnlyText(text)) return cleanProductNameText(text).slice(0, 240);
  }
  return "Shopee product";
}

function pageNumberFromHref(value) {
  try {
    const page = Number.parseInt(
      new URL(value, window.location.href).searchParams.get("page") || "",
      10,
    );
    return Number.isFinite(page) ? page : null;
  } catch (_error) {
    return null;
  }
}

function isPageBlockedByAntibot() {
  const path = window.location.pathname || "";
  if (/^\/verify\//.test(path)) return true;
  if (/crawler_?item|_?anti_?bot|abuse/i.test(window.location.search || "")) return true;
  if (document.querySelector('iframe[src*="captcha"]')) return true;
  const bodyText = normalizeText(document.body ? document.body.innerText || "" : "");
  return bodyText.includes("โปรดลองอีกครั้งในภายหลัง") || bodyText.includes("Please verify you are human");
}

// Reads the pagination controller observed on Shopee listing pages
// (`.shopee-page-controller` with numbered links plus prev/next arrows).
function readPaginationInfo() {
  const controller = document.querySelector(".shopee-page-controller");
  if (!controller) return null;
  const anchors = [...controller.querySelectorAll("a[href]")];
  const currentAnchor = controller.querySelector('a[aria-current="true"]');
  const nextAnchor = anchors.find((anchor) =>
    /shopee-icon-button--right/.test(anchor.className || ""),
  );
  const isDisabled = (anchor) =>
    anchor?.getAttribute("aria-disabled") === "true" ||
    /(?:^|\s)--disabled/.test(anchor.className || "");
  const currentPage = currentAnchor
    ? pageNumberFromHref(currentAnchor.getAttribute("href"))
    : pageNumberFromHref(window.location.href);
  const nextUrl =
    nextAnchor && !isDisabled(nextAnchor)
      ? new URL(nextAnchor.getAttribute("href"), window.location.href).href
      : null;
  const hasNext = nextUrl !== null;
  const miniTotal = document.querySelector(".shopee-mini-page-controller__total");
  let totalPages = miniTotal
    ? Number.parseInt((miniTotal.textContent || "").replace(/[^\d]/g, ""), 10)
    : Number.NaN;
  if (!Number.isFinite(totalPages)) {
    const pageParams = anchors
      .map((anchor) => pageNumberFromHref(anchor.getAttribute("href")))
      .filter((page) => page !== null);
    if (currentPage !== null) pageParams.push(currentPage);
    const maxPageParam = pageParams.reduce((max, page) => Math.max(max, page), -1);
    totalPages = maxPageParam >= 0 ? maxPageParam + 1 : Number.NaN;
  }
  return {
    current_page: currentPage, // 0-based page parameter, e.g. 7 == 8th page
    total_pages: Number.isFinite(totalPages) ? totalPages : null, // 1-based count
    has_next: hasNext,
    next_url: nextUrl,
  };
}

function readShopeeProductsFromCurrentPage() {
  if (window.location.hostname !== "shopee.co.th") return [];
  const sourceQuery = new URL(window.location.href).searchParams.get("keyword");
  const currentPageIdentity = parseShopeeProductIdentityFromUrl(window.location.href);
  if (currentPageIdentity) {
    return [
      {
        observation_id: randomObservationId(),
        platform: "shopee",
        shop_id: currentPageIdentity.shop_id,
        item_id: currentPageIdentity.item_id,
        collected_at: new Date().toISOString(),
        product_name: readCurrentProductDetailName(),
        product_url: window.location.href.split("?")[0],
        price_current: null,
        sold_signal: null,
        source_query: sourceQuery || null,
        extractor_version: SHOPEE_CURRENT_PAGE_PROFILE,
      },
    ];
  }

  const seen = new Set();
  const observations = [];

  for (const { anchor, container } of productTargetsForCurrentPage()) {
    const identity = parseShopeeProductIdentityFromUrl(anchor.getAttribute("href"));
    if (!identity) continue;
    const key = `${identity.shop_id}:${identity.item_id}`;
    if (seen.has(key)) continue;
    seen.add(key);

    observations.push({
      observation_id: randomObservationId(),
      platform: "shopee",
      shop_id: identity.shop_id,
      item_id: identity.item_id,
      collected_at: new Date().toISOString(),
      product_name: readProductName(anchor, container),
      product_url: new URL(anchor.getAttribute("href"), window.location.href).href.split("?")[0],
      price_current: null,
      sold_signal: null,
      source_query: sourceQuery || null,
      extractor_version: SHOPEE_CURRENT_PAGE_PROFILE,
    });
  }

  return observations;
}

function readFixtureProducts() {
  return [...document.querySelectorAll("[data-program1-fixture-product]")].map((node) => ({
    observation_id: randomObservationId(),
    platform: node.dataset.platform || "shopee",
    shop_id: node.dataset.shopId,
    item_id: node.dataset.itemId,
    collected_at: new Date().toISOString(),
    product_name: node.dataset.name || node.textContent.trim(),
    product_url: node.dataset.url || null,
    price_current: node.dataset.price || null,
    sold_signal: node.dataset.sold ? Number(node.dataset.sold) : null,
    rating: node.dataset.rating ? Number(node.dataset.rating) : null,
    review_count: node.dataset.reviews ? Number(node.dataset.reviews) : null,
    extractor_version: FIXTURE_PROFILE,
  }));
}

function captureCurrentPage() {
  const fixtureProducts = readFixtureProducts();
  if (fixtureProducts.length) {
    return {
      ok: true,
      error: null,
      profile: FIXTURE_PROFILE,
      observations: fixtureProducts,
      page_url: window.location.href,
    };
  }

  if (isPageBlockedByAntibot()) {
    return {
      ok: false,
      error: "PAGE_BLOCKED_BY_ANTIBOT",
      profile: SHOPEE_CURRENT_PAGE_PROFILE,
      observations: [],
      page_url: window.location.href,
    };
  }

  const shopeeProducts = readShopeeProductsFromCurrentPage();
  const pagination = readPaginationInfo();
  if (shopeeProducts.length) {
    return {
      ok: true,
      error: null,
      profile: SHOPEE_CURRENT_PAGE_PROFILE,
      observations: shopeeProducts,
      pagination,
      page_url: window.location.href,
    };
  }

  return {
    ok: false,
    error: "PAGE_UNSUPPORTED",
    profile: SHOPEE_CURRENT_PAGE_PROFILE,
    observations: [],
    pagination,
    page_url: window.location.href,
  };
}

if (globalThis.__mtaProgram1CollectorVersion !== SHOPEE_CURRENT_PAGE_PROFILE) {
  globalThis.__mtaProgram1CollectorVersion = SHOPEE_CURRENT_PAGE_PROFILE;
  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (
      message.type !== "PROGRAM1_CAPTURE_FIXTURE_PAGE" &&
      message.type !== "PROGRAM1_CAPTURE_CURRENT_PAGE"
    ) {
      return false;
    }
    sendResponse(captureCurrentPage());
    return false;
  });
}

if (typeof module !== "undefined") {
  module.exports = {
    captureCurrentPage,
    cleanProductNameText,
    inferShopeeSurfaceFromUrl,
    integerText,
    isMetricOnlyText,
    isPageBlockedByAntibot,
    numericText,
    pageNumberFromHref,
    parseShopeeProductIdentityFromUrl,
    randomObservationId,
    readCurrentProductDetailName,
    readPaginationInfo,
    readShopeeProductsFromCurrentPage,
  };
}
