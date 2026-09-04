(function registerFixtureProfile(global) {
  const ns = global.__mtaProgram1Collectors;
  if (!ns) throw new Error("PROGRAM1_COLLECTOR_CORE_REQUIRED");
  ns.registerProfile({
    profile_id: "fixture-profile-v1",
    version: "1",
    platform: "fixture",
    locale: "test",
    surface: "fixture",
    evidence_stage: "LAB_VALIDATED",
    priority: 1000,
    required_indicators: ["[data-program1-fixture-product]"],
    optional_indicators: [".shopee-page-controller"],
    extracted_fields: ["identity","product_name","product_url","price_current","sold_signal","rating","review_count"],
    unknown_fields: [],
    compatibility_scope: "deterministic test fixture only",
    evidence_refs: [],
    fixture_refs: ["tests fixture pages"],
    failure_modes: ["PAGE_UNSUPPORTED"],
    matches() {
      return document.querySelectorAll("[data-program1-fixture-product]").length > 0;
    },
    capture() {
      const observations = [...document.querySelectorAll("[data-program1-fixture-product]")].map((node) => ({
        observation_id: ns.randomObservationId(),
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
        extractor_version: "fixture-profile-v1",
      }));
      return { observations, pagination: ns.readPaginationInfo() };
    },
  });
})(globalThis);