(function registerShopeeSearch(global) {
  const ns = global.__mtaProgram1Collectors;
  if (!ns?.shopeeCommon) throw new Error("PROGRAM1_SHOPEE_COMMON_REQUIRED");
  ns.registerProfile({
    profile_id: "shopee-search-lab-v1", version: "1", platform: "shopee", locale: "th-TH",
    surface: "search", evidence_stage: "LAB_VALIDATED", priority: 100,
    required_indicators: ["URL:/search","identity-backed product links"],
    optional_indicators: [".shopee-page-controller"], extracted_fields: ["identity","product_name","product_url","source_query"],
    unknown_fields: ["price_current","sold_signal"], compatibility_scope: "shopee.co.th search",
    evidence_refs: ["SHOPEE_PROGRAM1_MARKETPLACE_DOM_ATTEMPT_2026-08-31.md"], fixture_refs: ["shopee_marketplace_surfaces.fixture.json"],
    failure_modes: ["PAGE_UNSUPPORTED","PAGE_BLOCKED_BY_ANTIBOT"],
    matches(ctx) { return ctx.hostname === "shopee.co.th" && ctx.surface === "search"; },
    capture() { return { observations: ns.shopeeCommon.listingObservations("search","shopee-search-lab-v1"), pagination: ns.readPaginationInfo() }; },
  });
})(globalThis);