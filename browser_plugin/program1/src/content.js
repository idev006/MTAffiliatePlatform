// Program 1 content-script bootstrap.
// Collection behavior lives in src/collectors/* and is injected before this file.

(function initProgram1ContentBridge(global) {
  const ns = global.__mtaProgram1Collectors;
  if (!ns?.captureCurrentPage) throw new Error("PROGRAM1_COLLECTION_ROUTER_REQUIRED");

  if (global.__mtaProgram1CollectorBridgeVersion !== "collection-router-v1") {
    global.__mtaProgram1CollectorBridgeVersion = "collection-router-v1";
    chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
      if (
        message.type !== "PROGRAM1_CAPTURE_FIXTURE_PAGE" &&
        message.type !== "PROGRAM1_CAPTURE_CURRENT_PAGE"
      ) {
        return false;
      }
      sendResponse(ns.captureCurrentPage());
      return false;
    });
  }

  if (typeof module !== "undefined") {
    module.exports = {
      captureCurrentPage: ns.captureCurrentPage,
      selectProfile: ns.selectProfile,
      registeredProfiles: () => ns.profiles.map((profile) => ({
        profile_id: profile.profile_id,
        profile_version: profile.version,
        profile_evidence_stage: profile.evidence_stage,
        surface: profile.surface,
      })),
      cleanProductNameText: ns.cleanProductNameText,
      inferShopeeSurfaceFromUrl: ns.inferShopeeSurfaceFromUrl,
      integerText: ns.integerText,
      isMetricOnlyText: ns.isMetricOnlyText,
      isPageBlockedByAntibot: ns.isPageBlockedByAntibot,
      numericText: ns.numericText,
      pageNumberFromHref: ns.pageNumberFromHref,
      parseShopeeProductIdentityFromUrl: ns.parseShopeeProductIdentityFromUrl,
      randomObservationId: ns.randomObservationId,
      readCurrentProductDetailName: ns.shopeeCommon.readCurrentProductDetailName,
      readPageSurfaceContext: ns.readPageSurfaceContext,
      readPaginationInfo: ns.readPaginationInfo,
      readShopeeProductsFromCurrentPage: () => {
        const surface = ns.inferShopeeSurfaceFromUrl(window.location.href);
        if (surface === "product_detail") return ns.shopeeCommon.pdpObservation("shopee-pdp-lab-v1");
        if (["search","category","shop"].includes(surface)) {
          return ns.shopeeCommon.listingObservations(surface, `shopee-${surface}-lab-v1`);
        }
        return [];
      },
    };
  }
})(globalThis);
