(function initProgram1CollectorCore(global) {
  const ns = global.__mtaProgram1Collectors || { profiles: [] };
  const STAGE_RANK = {
    EXPERIMENTAL: 0,
    LAB_VALIDATED: 1,
    EVIDENCE_VALIDATED: 2,
    PRODUCTION_CANDIDATE: 3,
    PRODUCTION_APPROVED: 4,
    STALE: -1,
    DEPRECATED: -2,
  };

  function registerProfile(profile) {
    const index = ns.profiles.findIndex((item) => item.profile_id === profile.profile_id);
    if (index >= 0) ns.profiles[index] = profile;
    else ns.profiles.push(profile);
    return profile;
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

  function parseShopeeProductIdentityFromUrl(value) {
    if (!value) return null;
    let url;
    try {
      url = new URL(value, window.location.href);
    } catch (_error) {
      return null;
    }
    const productPath = url.pathname.match(/\/product\/(\d+)\/(\d+)(?:\/|$)/);
    if (productPath) return { shop_id: productPath[1], item_id: productPath[2] };
    const itemPath = url.pathname.match(/(?:^|-)i\.(\d+)\.(\d+)(?:\/|$)/);
    if (itemPath) return { shop_id: itemPath[1], item_id: itemPath[2] };
    const shopId = url.searchParams.get("shopid") || url.searchParams.get("shop_id");
    const itemId = url.searchParams.get("itemid") || url.searchParams.get("item_id");
    if (shopId && itemId && /^\d+$/.test(shopId) && /^\d+$/.test(itemId)) {
      return { shop_id: shopId, item_id: itemId };
    }
    return null;
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

  function pageNumberFromHref(value) {
    try {
      const page = Number.parseInt(new URL(value, window.location.href).searchParams.get("page") || "", 10);
      return Number.isFinite(page) ? page : null;
    } catch (_error) {
      return null;
    }
  }

  function shopeePaginationController() {
    return document.querySelector('nav.shopee-page-controller[role="navigation"]') ||
      document.querySelector(".shopee-page-controller");
  }

  function readPaginationInfo() {
    const controller = shopeePaginationController();
    if (!controller) return null;
    const anchors = [...controller.querySelectorAll("a[href]")];
    const currentAnchor = controller.querySelector('a[aria-current="true"]') ||
      anchors.find((anchor) => /shopee-button-solid--primary/.test(anchor.className || ""));
    const nextAnchor = controller.querySelector("a.shopee-icon-button--right[href]") ||
      anchors.find((anchor) => /shopee-icon-button--right/.test(anchor.className || ""));
    const isDisabled = (anchor) => anchor?.getAttribute("aria-disabled") === "true" ||
      /(?:^|\s)--disabled/.test(anchor.className || "");
    const currentPage = currentAnchor ? pageNumberFromHref(currentAnchor.getAttribute("href")) : pageNumberFromHref(window.location.href);
    const nextUrl = nextAnchor && !isDisabled(nextAnchor)
      ? new URL(nextAnchor.getAttribute("href"), window.location.href).href
      : null;
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
      current_page: currentPage,
      total_pages: Number.isFinite(totalPages) ? totalPages : null,
      has_next: nextUrl !== null,
      next_url: nextUrl,
    };
  }

  function isPageBlockedByAntibot() {
    const path = window.location.pathname || "";
    if (/^\/verify\//.test(path)) return true;
    if (/crawler_?item|_?anti_?bot|abuse/i.test(window.location.search || "")) return true;
    if (document.querySelector('iframe[src*="captcha"]')) return true;
    const bodyText = normalizeText(document.body ? document.body.innerText || "" : "");
    return bodyText.includes("โปรดลองอีกครั้งในภายหลัง") || bodyText.includes("Please verify you are human");
  }

  function readPageSurfaceContext() {
    const roots = document.querySelectorAll('li.shopee-search-item-result__item[data-sqe="item"]');
    const listingShellPresent = Boolean(
      document.querySelector("section.shopee-search-item-result") || document.querySelector(".shopee-page-controller"),
    );
    return {
      listing_shell_present: listingShellPresent,
      item_roots: roots.length,
      page_title: (document.title || "").trim().slice(0, 120),
    };
  }

  function stageAtLeast(actual, required) {
    return (STAGE_RANK[actual] ?? -99) >= (STAGE_RANK[required] ?? 99);
  }

  Object.assign(ns, {
    STAGE_RANK, registerProfile, normalizeText, isMetricOnlyText, cleanProductNameText,
    numericText, integerText, randomObservationId, parseShopeeProductIdentityFromUrl,
    inferShopeeSurfaceFromUrl, pageNumberFromHref, readPaginationInfo, isPageBlockedByAntibot,
    readPageSurfaceContext, stageAtLeast,
  });
  global.__mtaProgram1Collectors = ns;
})(globalThis);