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

test("readPaginationInfo returns null when no pagination controller exists", () => {
  const originalQuerySelector = global.document.querySelector;
  global.document.querySelector = () => null;
  assert.equal(readPaginationInfo(), null);
  global.document.querySelector = originalQuerySelector;
});
