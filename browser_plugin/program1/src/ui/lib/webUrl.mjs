// Framework-free URL logic: origin permission patterns, web-page validation,
// Shopee listing next-page computation, capture-target derivation. No chrome/DOM.

export function originPattern(value) {
  const url = new URL(value);
  return `${url.protocol}//${url.host}/*`;
}

export function normalizedWebUrl(value) {
  const rawValue = String(value || "").trim();
  if (!rawValue) return { ok: false, error: "TARGET_URL_REQUIRED" };
  try {
    const url = new URL(rawValue);
    if (!["http:", "https:"].includes(url.protocol)) {
      return { ok: false, error: "TARGET_URL_NOT_A_WEB_PAGE", url: rawValue };
    }
    return { ok: true, url: url.toString() };
  } catch (_error) {
    return { ok: false, error: "TARGET_URL_INVALID", url: rawValue };
  }
}

export function nextShopeeListingPageUrl(value) {
  const normalized = normalizedWebUrl(value);
  if (!normalized.ok) return normalized;
  const url = new URL(normalized.url);
  if (url.hostname !== "shopee.co.th") {
    return { ok: false, error: "TARGET_NOT_SHOPEE", url: normalized.url };
  }
  if (/-i\.\d+\.\d+(?:\/|$)/.test(url.pathname) || /^\/product\/\d+\/\d+(?:\/|$)/.test(url.pathname)) {
    return { ok: false, error: "TARGET_IS_PRODUCT_DETAIL", url: normalized.url };
  }
  const currentPage = Number.parseInt(url.searchParams.get("page") || "0", 10);
  const nextPage = Number.isFinite(currentPage) && currentPage >= 0 ? currentPage + 1 : 1;
  url.searchParams.set("page", String(nextPage));
  return { ok: true, url: url.toString(), page: nextPage };
}

export function pageParamOf(urlValue) {
  try {
    const parsed = Number.parseInt(new URL(urlValue).searchParams.get("page") || "0", 10);
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
  } catch (_error) {
    return 0;
  }
}

export function captureTargetFromTab(tab) {
  if (!tab?.id) return { ok: false, error: "NO_ACTIVE_TAB" };
  if (!tab.url) return { ok: false, error: "ACTIVE_TAB_URL_UNAVAILABLE" };
  try {
    const url = new URL(tab.url);
    if (!["http:", "https:"].includes(url.protocol)) {
      return { ok: false, error: "ACTIVE_TAB_NOT_A_WEB_PAGE", url: tab.url };
    }
    return { ok: true, tabId: tab.id, url: tab.url };
  } catch (_error) {
    return { ok: false, error: "ACTIVE_TAB_URL_INVALID", url: tab.url };
  }
}
