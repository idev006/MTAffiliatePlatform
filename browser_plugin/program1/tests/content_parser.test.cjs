const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

global.window = { location: { href: "https://shopee.co.th/search?keyword=ssd" } };
global.chrome = { runtime: { onMessage: { addListener() {} } } };
global.document = {
  title: "",
  querySelector() {
    return null;
  },
  querySelectorAll() {
    return [];
  },
};
global.crypto = { randomUUID() { return "test-uuid"; } };

const {
  captureCurrentPage,
  cleanProductNameText,
  inferShopeeSurfaceFromUrl,
  integerText,
  isMetricOnlyText,
  numericText,
  parseShopeeProductIdentityFromUrl,
  randomObservationId,
  readCurrentProductDetailName,
  readPageSurfaceContext,
  readPaginationInfo,
  readShopeeProductsFromCurrentPage,
} = require("../src/content.js");

function locationFromUrl(value) {
  const url = new URL(value);
  return {
    href: url.href,
    hostname: url.hostname,
    pathname: url.pathname,
    search: url.search,
  };
}

function fakeAnchor(item) {
  return {
    innerText: item.text,
    textContent: item.text,
    parentElement: null,
    getAttribute(name) {
      if (name === "href") return item.href;
      if (name === "title") return item.name;
      if (name === "aria-label") return null;
      return null;
    },
    querySelector(selector) {
      if (selector === "img") return { tagName: "IMG" };
      return null;
    },
  };
}

// Builds the `.shopee-page-controller` DOM stub from the sanitized pagination nav
// stored in the shared marketplace fixture, so the parser is exercised against the
// same markup the tests and future fixture pages reuse.
function anchorStubFromDescriptor(descriptor) {
  return {
    className: descriptor.class || "",
    getAttribute(name) {
      if (name === "href") return descriptor.href ?? null;
      if (name === "aria-disabled") return descriptor.aria_disabled ?? null;
      if (name === "aria-current") return descriptor.aria_current ?? null;
      return null;
    },
  };
}

function paginationControllerStub(pagination) {
  const anchors = (pagination.controller_anchors || []).map(anchorStubFromDescriptor);
  return {
    querySelectorAll(innerSelector) {
      if (innerSelector === "a[href]") {
        return anchors.filter((anchor) => anchor.getAttribute("href") !== null);
      }
      return [];
    },
    querySelector(innerSelector) {
      if (innerSelector === 'a[aria-current="true"]') {
        return anchors.find((anchor) => anchor.getAttribute("aria-current") === "true") || null;
      }
      if (innerSelector === "a.shopee-icon-button--right[href]") {
        return anchors.find((anchor) => /shopee-icon-button--right/.test(anchor.className)) || null;
      }
      return null;
    },
  };
}

function fakeListingContainer(item) {
  const anchor = fakeAnchor(item);
  const container = {
    innerText: item.text,
    textContent: item.text,
    parentElement: null,
    querySelector(selector) {
      if (selector === "a[href]") return anchor;
      if (selector === "[data-sqe='name']") return { textContent: item.name };
      if (selector === "[class*='name' i]") return { textContent: item.name };
      if (selector === "img") return { tagName: "IMG" };
      return null;
    },
  };
  anchor.parentElement = container;
  return container;
}

function installSurfaceFixture(fixture) {
  const containers = (fixture.items || []).map(fakeListingContainer);
  const anchors = containers.map((container) => container.querySelector("a[href]"));
  global.window.location = locationFromUrl(fixture.url);
  global.document.title = `${fixture.surface} fixture`;
  global.document.querySelector = (selector) => {
    if (selector === "h1" && fixture.title) return { textContent: fixture.title };
    if (
      fixture.pagination &&
      (selector === ".shopee-page-controller" || selector === 'nav.shopee-page-controller[role="navigation"]')
    ) {
      return paginationControllerStub(fixture.pagination);
    }
    if (fixture.pagination && selector === ".shopee-mini-page-controller__total") {
      return { textContent: fixture.pagination.mini_total_text };
    }
    return null;
  };
  global.document.querySelectorAll = (selector) => {
    if (
      selector === '[data-sqe="item"].shopee-search-item-result__item' &&
      ["search", "category"].includes(fixture.surface)
    ) {
      return containers;
    }
    if (selector === "a[href]" && fixture.surface === "shop") {
      return anchors;
    }
    if (selector === "[data-program1-fixture-product]") return [];
    return [];
  };
}

const surfaceFixtures = JSON.parse(
  fs.readFileSync(
    path.join(__dirname, "fixtures", "shopee_marketplace_surfaces.fixture.json"),
    "utf8",
  ),
);

test("parses Shopee product identity from -i.shop.item URL", () => {
  assert.deepEqual(
    parseShopeeProductIdentityFromUrl("https://shopee.co.th/product-name-i.12345.67890"),
    { shop_id: "12345", item_id: "67890" },
  );
  assert.deepEqual(
    parseShopeeProductIdentityFromUrl(
      "/HOME-MALL-SSD-128GB-i.207554797.43507650536?extraParams=%7B%7D",
    ),
    { shop_id: "207554797", item_id: "43507650536" },
  );
});

test("parses Shopee product identity from /product/shop/item URL", () => {
  assert.deepEqual(
    parseShopeeProductIdentityFromUrl("https://shopee.co.th/product/12345/67890"),
    { shop_id: "12345", item_id: "67890" },
  );
});

test("parses Shopee product identity from query parameters", () => {
  assert.deepEqual(
    parseShopeeProductIdentityFromUrl("https://shopee.co.th/item?shopid=12345&itemid=67890"),
    { shop_id: "12345", item_id: "67890" },
  );
});

test("rejects URL without a product identity", () => {
  assert.equal(parseShopeeProductIdentityFromUrl("https://shopee.co.th/search?keyword=ssd"), null);
});

test("parses price and sold numeric text", () => {
  assert.equal(numericText("฿1,299.50"), "1299.50");
  assert.equal(integerText("1,234 sold"), 1234);
});

test("keeps listing product names and strips trailing metrics", () => {
  assert.equal(isMetricOnlyText("5k+ sold"), true);
  assert.equal(isMetricOnlyText("฿ 10,499"), true);
  assert.equal(
    cleanProductNameText("Fikwot FS810 2.5'' SATA SSD ฿ 10,499 -42% 5.0 169 sold"),
    "Fikwot FS810 2.5'' SATA SSD",
  );
  assert.equal(isMetricOnlyText("Fikwot FS810 2.5'' SATA SSD ฿ 10,499 -42% 5.0 169 sold"), false);
});

test("infers supported Shopee marketplace surfaces from URL", () => {
  assert.equal(inferShopeeSurfaceFromUrl("https://shopee.co.th/search?keyword=ssd"), "search");
  assert.equal(
    inferShopeeSurfaceFromUrl("https://shopee.co.th/Internal-Solid-State-Drive-cat.11044958.11045198.11046028"),
    "category",
  );
  assert.equal(inferShopeeSurfaceFromUrl("https://shopee.co.th/yyf.th#product_list"), "shop");
  assert.equal(
    inferShopeeSurfaceFromUrl("https://shopee.co.th/Fikwot-FS810-i.1228919183.25473237549"),
    "product_detail",
  );
});

test("generates observation id with crypto randomUUID", () => {
  assert.match(randomObservationId(), /^[a-f0-9-]+$|^test-uuid$/);
});

test("reads current product detail name from PDP title sources before generic body text", () => {
  const originalQuerySelector = global.document.querySelector;
  const originalTitle = global.document.title;
  global.document.querySelector = (selector) => {
    if (selector === "h1") return { textContent: "Fikwot FS810 SATA SSD ฿ 10,499 169 sold" };
    return null;
  };
  global.document.title = "Fallback Product | Shopee Thailand";

  assert.equal(readCurrentProductDetailName(), "Fikwot FS810 SATA SSD");

  global.document.querySelector = originalQuerySelector;
  global.document.title = originalTitle;
});

for (const fixture of surfaceFixtures) {
  test(`extracts identity-backed observations from sanitized ${fixture.surface} fixture`, () => {
    installSurfaceFixture(fixture);

    const observations = readShopeeProductsFromCurrentPage();

    assert.equal(observations.length, fixture.expected_count);
    assert.equal(observations[0].platform, "shopee");
    assert.equal(observations[0].price_current, null);
    assert.equal(observations[0].sold_signal, null);
    assert.equal(observations[0].source_query, fixture.keyword);
    assert.match(observations[0].product_url, /^https:\/\/shopee\.co\.th\//);
    assert.equal(/฿|sold/i.test(observations[0].product_name), false);
    if (fixture.pagination) {
      assert.deepEqual(readPaginationInfo(), fixture.pagination.expected);
    }
  });
}

test("returns no Shopee observations when CAPTCHA or unsupported page has no identity evidence", () => {
  global.window.location = locationFromUrl("https://shopee.co.th/verify/captcha?scene=crawler_item");
  global.document.querySelector = () => null;
  global.document.querySelectorAll = () => [];

  assert.deepEqual(readShopeeProductsFromCurrentPage(), []);
});

test("captureCurrentPage fails closed with PAGE_BLOCKED_BY_ANTIBOT on verification pages", () => {
  global.window.location = locationFromUrl("https://shopee.co.th/verify/captcha?scene=crawler_item");
  global.document.title = "Shopee Thailand";
  global.document.querySelector = () => null;
  global.document.querySelectorAll = () => [];

  const result = captureCurrentPage();
  assert.equal(result.ok, false);
  assert.equal(result.error, "PAGE_BLOCKED_BY_ANTIBOT");
  assert.deepEqual(result.observations, []);
  assert.match(result.page_url, /verify\/captcha/);
});

test("captureCurrentPage fails closed with PAGE_UNSUPPORTED on a Shopee page without identity evidence", () => {
  global.window.location = locationFromUrl("https://shopee.co.th/some-other-page");
  global.document.title = "Some other Shopee page";
  global.document.querySelector = () => null;
  global.document.querySelectorAll = () => [];

  const result = captureCurrentPage();
  assert.equal(result.ok, false);
  assert.equal(result.error, "PAGE_UNSUPPORTED");
  assert.deepEqual(result.observations, []);
});

test("PAGE_UNSUPPORTED carries listing-shell context when an empty page still renders the listing surface", () => {
  global.window.location = locationFromUrl("https://shopee.co.th/search?keyword=ssd&page=4");
  global.document.title = "ssd - Shopee Thailand";
  global.document.querySelector = (selector) => {
    if (selector === "section.shopee-search-item-result") return { className: "shopee-search-item-result" };
    return null;
  };
  global.document.querySelectorAll = () => [];

  const result = captureCurrentPage();
  assert.equal(result.ok, false);
  assert.equal(result.error, "PAGE_UNSUPPORTED");
  assert.deepEqual(result.page_context, {
    listing_shell_present: true,
    item_roots: 0,
    page_title: "ssd - Shopee Thailand",
  });
});

function installFixturePage({ url, products, controllerAnchors = [], currentHref = null, miniTotal = null }) {
  const originals = {
    location: global.window.location,
    title: global.document.title,
    querySelector: global.document.querySelector,
    querySelectorAll: global.document.querySelectorAll,
  };
  const restore = () => {
    global.window.location = originals.location;
    global.document.title = originals.title;
    global.document.querySelector = originals.querySelector;
    global.document.querySelectorAll = originals.querySelectorAll;
  };
  global.window.location = locationFromUrl(url);
  global.document.title = "Fixture listing";
  const nodes = products.map((product) => ({
    dataset: { ...product },
    textContent: product.name || "",
  }));
  const anchors = controllerAnchors.map(({ className, href, ariaDisabled, ariaCurrent }) => ({
    className,
    getAttribute(name) {
      if (name === "href") return href;
      if (name === "aria-disabled") return ariaDisabled || null;
      if (name === "aria-current") return ariaCurrent || null;
      return null;
    },
  }));
  const currentAnchor = currentHref
    ? anchors.find((anchor) => anchor.getAttribute("href") === currentHref) || null
    : null;
  global.document.querySelector = (selector) => {
    if (selector === "section.shopee-search-item-result") return null;
    if (selector === ".shopee-page-controller") {
      if (!anchors.length && !miniTotal) return null;
      return {
        querySelectorAll(innerSelector) {
          return innerSelector === "a[href]" ? anchors : [];
        },
        querySelector(innerSelector) {
          if (innerSelector === 'a[aria-current="true"]') return currentAnchor;
          if (innerSelector === ".shopee-mini-page-controller__total") return miniTotal;
          return null;
        },
      };
    }
    return null;
  };
  global.document.querySelectorAll = (selector) => {
    if (selector === "[data-program1-fixture-product]") return nodes;
    if (selector === 'li.shopee-search-item-result__item[data-sqe="item"]') return [];
    return [];
  };
  return restore;
}

test("fixture capture is pagination-aware when the page embeds a shopee-page-controller", () => {
  const restore = installFixturePage({
    url: "http://127.0.0.1:8790/listing?page=0",
    products: [
      {
        platform: "shopee",
        shopId: "100",
        itemId: "200",
        name: "Fixture product A",
        url: "http://127.0.0.1:8790/item-a",
      },
    ],
    controllerAnchors: [
      { className: "shopee-button-no-outline", href: "/listing?page=0", ariaCurrent: "true" },
      { className: "shopee-icon-button shopee-icon-button--right", href: "/listing?page=1" },
    ],
    currentHref: "/listing?page=0",
    miniTotal: { textContent: "2" },
  });

  const result = captureCurrentPage();
  assert.equal(result.ok, true);
  assert.equal(result.profile, "fixture-profile-v1");
  assert.equal(result.observations.length, 1);
  assert.deepEqual(result.pagination, {
    current_page: 0,
    total_pages: 2,
    has_next: true,
    next_url: "http://127.0.0.1:8790/listing?page=1",
  });
  restore();
});

test("fixture capture reports null pagination when the page has no controller", () => {
  const restore = installFixturePage({
    url: "http://127.0.0.1:8790/single",
    products: [{ platform: "shopee", shopId: "100", itemId: "200", name: "A", url: "/a" }],
  });

  const result = captureCurrentPage();
  assert.equal(result.ok, true);
  assert.equal(result.profile, "fixture-profile-v1");
  assert.equal(result.pagination, null);
  restore();
});

test("readPageSurfaceContext reports no listing shell on unrelated pages", () => {
  global.document.querySelector = () => null;
  global.document.querySelectorAll = () => [];
  global.document.title = "Some unrelated page";

  assert.deepEqual(readPageSurfaceContext(), {
    listing_shell_present: false,
    item_roots: 0,
    page_title: "Some unrelated page",
  });
});

test("readPaginationInfo reads the current page, total and next URL from the pagination controller", () => {
  const originalQuerySelector = global.document.querySelector;
  const originalTitle = global.document.title;
  const controllerAnchors = [
    {
      className: "shopee-icon-button shopee-icon-button--left",
      getAttribute(name) {
        return name === "href" ? "/search?keyword=ssd&page=6" : name === "aria-disabled" ? "false" : null;
      },
    },
    {
      className: "shopee-button-no-outline",
      getAttribute(name) {
        return name === "href" ? "/search?keyword=ssd&page=7" : null;
      },
    },
    {
      className: "shopee-button-solid shopee-button-solid--primary",
      getAttribute(name) {
        if (name === "href") return "/search?keyword=ssd&page=7";
        if (name === "aria-current") return "true";
        return null;
      },
    },
    {
      className: "shopee-icon-button shopee-icon-button--right",
      getAttribute(name) {
        if (name === "href") return "/search?keyword=ssd&page=8";
        if (name === "aria-disabled") return "false";
        return null;
      },
    },
  ];
  const controller = {
    querySelector(selector) {
      if (selector === 'a[aria-current="true"]') return controllerAnchors[2];
      return null;
    },
    querySelectorAll() {
      return controllerAnchors;
    },
  };
  global.document.querySelector = (selector) => {
    if (selector === ".shopee-page-controller") return controller;
    if (selector === ".shopee-mini-page-controller__total") return { textContent: "12" };
    return null;
  };
  global.document.title = "ssd | Shopee";

  const pagination = readPaginationInfo();
  assert.deepEqual(pagination, {
    current_page: 7,
    total_pages: 12,
    has_next: true,
    next_url: "https://shopee.co.th/search?keyword=ssd&page=8",
  });

  global.document.querySelector = originalQuerySelector;
  global.document.title = originalTitle;
});

test("readPaginationInfo reports no next page when the next arrow is disabled", () => {
  const originalQuerySelector = global.document.querySelector;
  const anchors = [
    {
      className: "shopee-button-no-outline",
      getAttribute(name) {
        return name === "href" ? "/search?keyword=ssd&page=6" : null;
      },
    },
    {
      className: "shopee-icon-button shopee-icon-button--right shopee-icon-button--disabled",
      getAttribute(name) {
        if (name === "href") return "/";
        if (name === "aria-disabled") return "true";
        return null;
      },
    },
  ];
  const controller = {
    querySelector(selector) {
      if (selector === 'a[aria-current="true"]') {
        return { getAttribute: (name) => (name === "href" ? "/search?keyword=ssd&page=7" : null) };
      }
      return null;
    },
    querySelectorAll() {
      return anchors;
    },
  };
  global.document.querySelector = (selector) => {
    if (selector === ".shopee-page-controller") return controller;
    if (selector === ".shopee-mini-page-controller__total") return { textContent: "8" };
    return null;
  };

  const pagination = readPaginationInfo();
  assert.equal(pagination.has_next, false);
  assert.equal(pagination.next_url, null);
  assert.equal(pagination.current_page, 7);
  assert.equal(pagination.total_pages, 8);

  global.document.querySelector = originalQuerySelector;
});

test("readPaginationInfo handles the real controller shape with disabled left arrow, ellipsis and mini-total priority", () => {
  // The nav lives in the shared marketplace fixture (search entry); this dedicated
  // test pins the shape explicitly so a regression in the fixture data or the
  // parser is attributable instead of silently changing either.
  const searchPagination = surfaceFixtures.find((fixture) => fixture.surface === "search").pagination;
  assert.ok(searchPagination, "search fixture carries the sanitized real pagination nav");
  const originalQuerySelector = global.document.querySelector;
  global.document.querySelector = (selector) => {
    if (selector === ".shopee-page-controller" || selector === 'nav.shopee-page-controller[role="navigation"]') {
      return paginationControllerStub(searchPagination);
    }
    if (selector === ".shopee-mini-page-controller__total") {
      return { textContent: searchPagination.mini_total_text };
    }
    return null;
  };

  assert.deepEqual(readPaginationInfo(), searchPagination.expected);
  global.document.querySelector = originalQuerySelector;
});

test("readPaginationInfo follows the Shopee nav right-arrow pagination contract", () => {
  const originalQuerySelector = global.document.querySelector;
  global.window.location = locationFromUrl("https://shopee.co.th/search?keyword=ssd&page=12");
  const pagination = {
    mini_total_text: "",
    controller_anchors: [
      { class: "shopee-icon-button shopee-icon-button--left", href: "/search?keyword=ssd&page=11", aria_disabled: "false" },
      { class: "shopee-button-no-outline", href: "/search?keyword=ssd&page=0" },
      { class: "shopee-button-no-outline", href: "/search?keyword=ssd&page=1" },
      { class: "shopee-button-no-outline shopee-button-no-outline--non-click" },
      { class: "shopee-button-no-outline", href: "/search?keyword=ssd&page=10" },
      { class: "shopee-button-no-outline", href: "/search?keyword=ssd&page=11" },
      {
        class: "shopee-button-solid shopee-button-solid--primary",
        href: "/search?keyword=ssd&page=12",
        aria_current: "true",
      },
      { class: "shopee-button-no-outline", href: "/search?keyword=ssd&page=13" },
      { class: "shopee-button-no-outline", href: "/search?keyword=ssd&page=14" },
      { class: "shopee-button-no-outline shopee-button-no-outline--non-click" },
      { class: "shopee-icon-button shopee-icon-button--right", href: "/search?keyword=ssd&page=13", aria_disabled: "false" },
    ],
  };
  global.document.querySelector = (selector) => {
    if (selector === 'nav.shopee-page-controller[role="navigation"]') {
      return paginationControllerStub(pagination);
    }
    if (selector === ".shopee-mini-page-controller__total") return null;
    return null;
  };

  assert.deepEqual(readPaginationInfo(), {
    current_page: 12,
    total_pages: 15,
    has_next: true,
    next_url: "https://shopee.co.th/search?keyword=ssd&page=13",
  });
  global.document.querySelector = originalQuerySelector;
});

test("readPaginationInfo returns null when no pagination controller exists", () => {
  const originalQuerySelector = global.document.querySelector;
  global.document.querySelector = () => null;
  assert.equal(readPaginationInfo(), null);
  global.document.querySelector = originalQuerySelector;
});
