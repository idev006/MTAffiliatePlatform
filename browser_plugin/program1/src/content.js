// Real Shopee selectors are intentionally NOT hard-coded here.
// Production collection profiles remain a validation gate.
// This content adapter currently supports only explicit fixture markup for
// deterministic laboratory/contract testing.

function readFixtureProducts() {
  return [...document.querySelectorAll("[data-program1-fixture-product]")].map((node) => ({
    observation_id: crypto.randomUUID(),
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
    extractor_version: "fixture-profile-v1"
  }));
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type !== "PROGRAM1_CAPTURE_FIXTURE_PAGE") return false;
  const observations = readFixtureProducts();
  sendResponse({
    ok: observations.length > 0,
    error: observations.length ? null : "PAGE_UNSUPPORTED",
    observations,
  });
  return false;
});
