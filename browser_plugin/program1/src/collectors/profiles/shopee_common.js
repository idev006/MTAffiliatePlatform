(function initShopeeCommon(global) {
  const ns = global.__mtaProgram1Collectors;
  if (!ns) throw new Error("PROGRAM1_COLLECTOR_CORE_REQUIRED");

  function nearestProductContainer(anchor) {
    let current = anchor;
    for (let depth = 0; current && depth < 6; depth += 1) {
      const text = ns.normalizeText(current.innerText || current.textContent);
      if (current.querySelector?.("img") && /฿|\bsold\b|ขายแล้ว|คะแนน|rating/i.test(text)) return current;
      current = current.parentElement;
    }
    return anchor;
  }

  function listingTargets(surface) {
    if (surface === "search" || surface === "category") {
      return [...document.querySelectorAll('[data-sqe="item"].shopee-search-item-result__item')]
        .map((container) => ({ anchor: container.querySelector?.("a[href]"), container }))
        .filter((target) => target.anchor);
    }
    if (surface === "shop") {
      return [...document.querySelectorAll("a[href]")]
        .filter((anchor) => ns.parseShopeeProductIdentityFromUrl(anchor.getAttribute("href")))
        .map((anchor) => ({ anchor, container: nearestProductContainer(anchor) }));
    }
    return [];
  }

  function readProductName(anchor, container) {
    const candidates = [
      anchor.innerText || anchor.textContent,
      anchor.getAttribute("title"),
      anchor.getAttribute("aria-label"),
      container.querySelector?.("[data-sqe='name']")?.textContent,
      container.querySelector?.("[class*='name' i]")?.textContent,
    ];
    for (const candidate of candidates) {
      const text = ns.normalizeText(candidate);
      if (text && !ns.isMetricOnlyText(text)) return ns.cleanProductNameText(text).slice(0, 240);
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
      const text = ns.normalizeText(candidate);
      if (text && !ns.isMetricOnlyText(text)) return ns.cleanProductNameText(text).slice(0, 240);
    }
    return "Shopee product";
  }

  function listingObservations(surface, extractorVersion) {
    if (window.location.hostname !== "shopee.co.th") return [];
    const sourceQuery = new URL(window.location.href).searchParams.get("keyword");
    const seen = new Set();
    const observations = [];
    for (const { anchor, container } of listingTargets(surface)) {
      const identity = ns.parseShopeeProductIdentityFromUrl(anchor.getAttribute("href"));
      if (!identity) continue;
      const key = `${identity.shop_id}:${identity.item_id}`;
      if (seen.has(key)) continue;
      seen.add(key);
      observations.push({
        observation_id: ns.randomObservationId(),
        platform: "shopee",
        shop_id: identity.shop_id,
        item_id: identity.item_id,
        collected_at: new Date().toISOString(),
        product_name: readProductName(anchor, container),
        product_url: new URL(anchor.getAttribute("href"), window.location.href).href.split("?")[0],
        price_current: null,
        sold_signal: null,
        source_query: sourceQuery || null,
        extractor_version: extractorVersion,
      });
    }
    return observations;
  }

  function pdpObservation(extractorVersion) {
    if (window.location.hostname !== "shopee.co.th") return [];
    const identity = ns.parseShopeeProductIdentityFromUrl(window.location.href);
    if (!identity) return [];
    return [{
      observation_id: ns.randomObservationId(),
      platform: "shopee",
      shop_id: identity.shop_id,
      item_id: identity.item_id,
      collected_at: new Date().toISOString(),
      product_name: readCurrentProductDetailName(),
      product_url: window.location.href.split("?")[0],
      price_current: null,
      sold_signal: null,
      source_query: new URL(window.location.href).searchParams.get("keyword") || null,
      extractor_version: extractorVersion,
    }];
  }

  ns.shopeeCommon = { nearestProductContainer, listingTargets, readProductName, readCurrentProductDetailName, listingObservations, pdpObservation };
})(globalThis);