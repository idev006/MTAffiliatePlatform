const assert = require("node:assert/strict");
const test = require("node:test");

global.chrome = { runtime: { onMessage: { addListener() {} } } };
global.crypto = { randomUUID() { return "router-test-uuid"; } };
global.document = {
  title: "",
  body: null,
  querySelector() { return null; },
  querySelectorAll() { return []; },
};
global.window = {
  location: {
    href: "https://shopee.co.th/search?keyword=ssd",
    hostname: "shopee.co.th",
    pathname: "/search",
    search: "?keyword=ssd",
  },
};

require("../src/collectors/core.js");
require("../src/collectors/profiles/fixture.js");
require("../src/collectors/profiles/shopee_common.js");
require("../src/collectors/profiles/shopee_search_lab_v1.js");
require("../src/collectors/profiles/shopee_category_lab_v1.js");
require("../src/collectors/profiles/shopee_shop_lab_v1.js");
require("../src/collectors/profiles/shopee_pdp_lab_v1.js");
require("../src/collectors/router.js");
const { selectProfile, registeredProfiles } = require("../src/content.js");

function setLocation(value) {
  const url = new URL(value);
  global.window.location = {
    href: url.href,
    hostname: url.hostname,
    pathname: url.pathname,
    search: url.search,
  };
}

test("registry exposes independent versioned surface profiles", () => {
  const profiles = registeredProfiles();
  assert.deepEqual(
    profiles.map((item) => item.profile_id).sort(),
    [
      "fixture-profile-v1",
      "shopee-category-lab-v1",
      "shopee-pdp-lab-v1",
      "shopee-search-lab-v1",
      "shopee-shop-lab-v1",
    ],
  );
  assert.equal(profiles.filter((item) => item.profile_evidence_stage === "LAB_VALIDATED").length, 5);
});

for (const [url, expected] of [
  ["https://shopee.co.th/search?keyword=ssd", "shopee-search-lab-v1"],
  ["https://shopee.co.th/Internal-Drive-cat.11044958.11045198", "shopee-category-lab-v1"],
  ["https://shopee.co.th/yyf.th", "shopee-shop-lab-v1"],
  ["https://shopee.co.th/Test-product-i.123.456", "shopee-pdp-lab-v1"],
]) {
  test(`router selects only ${expected}`, () => {
    setLocation(url);
    const selected = selectProfile();
    assert.equal(selected.ok, true);
    assert.equal(selected.profile.profile_id, expected);
  });
}

test("production-approved policy refuses laboratory Shopee profile", () => {
  setLocation("https://shopee.co.th/search?keyword=ssd");
  const selected = selectProfile({ minimumEvidenceStage: "PRODUCTION_APPROVED" });
  assert.equal(selected.ok, false);
  assert.equal(selected.error, "PROFILE_NOT_ALLOWED_BY_EVIDENCE_STAGE");
  assert.equal(selected.matches[0].profile_id, "shopee-search-lab-v1");
});

test("unsupported Shopee path does not fall back to another surface profile", () => {
  setLocation("https://shopee.co.th/some/unsupported/path");
  const selected = selectProfile();
  assert.equal(selected.ok, false);
  assert.equal(selected.error, "PAGE_UNSUPPORTED");
});

test("equal-priority duplicate match fails closed as PROFILE_AMBIGUOUS", () => {
  setLocation("https://shopee.co.th/search?keyword=ssd");
  const ns = global.__mtaProgram1Collectors;
  ns.profiles.push({
    profile_id: "test-search-ambiguous",
    version: "1",
    surface: "search",
    evidence_stage: "LAB_VALIDATED",
    priority: 100,
    matches(ctx) { return ctx.surface === "search"; },
    capture() { return { observations: [] }; },
  });
  try {
    const selected = selectProfile();
    assert.equal(selected.ok, false);
    assert.equal(selected.error, "PROFILE_AMBIGUOUS");
    assert.equal(selected.matches.length, 2);
  } finally {
    ns.profiles = ns.profiles.filter((item) => item.profile_id !== "test-search-ambiguous");
  }
});
