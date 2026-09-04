import assert from "node:assert/strict";
import test from "node:test";

import {
  delayRangeGeometry,
  delayRangeLabel,
  delayRangePreview,
  normalizedDelayRangeMs,
  randomDelayMs,
  syncDelayRangeValues,
} from "../src/ui/lib/delayRange.mjs";
import {
  captureTargetFromTab,
  nextShopeeListingPageUrl,
  normalizedWebUrl,
  originPattern,
} from "../src/ui/lib/webUrl.mjs";

test("originPattern converts page URL to host permission pattern", () => {
  assert.equal(originPattern("https://shopee.co.th/search?keyword=ssd"), "https://shopee.co.th/*");
});

test("normalizedWebUrl accepts http and https URLs only", () => {
  assert.deepEqual(normalizedWebUrl(" https://shopee.co.th/search?keyword=ssd "), {
    ok: true,
    url: "https://shopee.co.th/search?keyword=ssd",
  });
  assert.deepEqual(normalizedWebUrl("brave://extensions/"), {
    ok: false,
    error: "TARGET_URL_NOT_A_WEB_PAGE",
    url: "brave://extensions/",
  });
  assert.deepEqual(normalizedWebUrl(""), {
    ok: false,
    error: "TARGET_URL_REQUIRED",
  });
});

test("nextShopeeListingPageUrl advances Shopee listing pages only", () => {
  assert.deepEqual(nextShopeeListingPageUrl("https://shopee.co.th/search?keyword=ssd"), {
    ok: true,
    url: "https://shopee.co.th/search?keyword=ssd&page=1",
    page: 1,
  });
  assert.deepEqual(nextShopeeListingPageUrl("https://shopee.co.th/search?keyword=ssd&page=3"), {
    ok: true,
    url: "https://shopee.co.th/search?keyword=ssd&page=4",
    page: 4,
  });
  assert.deepEqual(nextShopeeListingPageUrl("https://example.com/search?keyword=ssd"), {
    ok: false,
    error: "TARGET_NOT_SHOPEE",
    url: "https://example.com/search?keyword=ssd",
  });
  assert.deepEqual(nextShopeeListingPageUrl("https://shopee.co.th/abc-i.1.2"), {
    ok: false,
    error: "TARGET_IS_PRODUCT_DETAIL",
    url: "https://shopee.co.th/abc-i.1.2",
  });
});

test("captureTargetFromTab accepts normal web pages", () => {
  assert.deepEqual(captureTargetFromTab({ id: 7, url: "https://shopee.co.th/search?keyword=ssd" }), {
    ok: true,
    tabId: 7,
    url: "https://shopee.co.th/search?keyword=ssd",
  });
});

test("captureTargetFromTab rejects missing and non-web tab URLs before URL construction", () => {
  assert.deepEqual(captureTargetFromTab({ id: 7 }), {
    ok: false,
    error: "ACTIVE_TAB_URL_UNAVAILABLE",
  });
  assert.deepEqual(captureTargetFromTab({ id: 7, url: "chrome://extensions/" }), {
    ok: false,
    error: "ACTIVE_TAB_NOT_A_WEB_PAGE",
    url: "chrome://extensions/",
  });
  assert.deepEqual(captureTargetFromTab({ id: 7, url: "http://127..0.1:8000/" }), {
    ok: false,
    error: "ACTIVE_TAB_URL_INVALID",
    url: "http://127..0.1:8000/",
  });
});

test("normalizedDelayRangeMs clamps and orders random delay slider bounds", () => {
  assert.deepEqual(normalizedDelayRangeMs("0", "600"), {
    min_seconds: 0,
    max_seconds: 600,
    min_ms: 0,
    max_ms: 600000,
  });
  assert.deepEqual(normalizedDelayRangeMs("700", "-10"), {
    min_seconds: 0,
    max_seconds: 600,
    min_ms: 0,
    max_ms: 600000,
  });
  assert.deepEqual(normalizedDelayRangeMs("120", "30"), {
    min_seconds: 30,
    max_seconds: 120,
    min_ms: 30000,
    max_ms: 120000,
  });
  assert.deepEqual(normalizedDelayRangeMs("bad", ""), {
    min_seconds: 30,
    max_seconds: 120,
    min_ms: 30000,
    max_ms: 120000,
  });
});

test("randomDelayMs chooses a value inside the normalized delay range", () => {
  const range = normalizedDelayRangeMs("10", "20");
  assert.equal(randomDelayMs(range, () => 0), 10000);
  assert.equal(randomDelayMs(range, () => 0.5), 15000);
  assert.equal(randomDelayMs(range, () => 0.9999) <= 20000, true);
});

test("delayRangeGeometry maps seconds to fill geometry percentages", () => {
  const range = normalizedDelayRangeMs("100", "240");
  assert.deepEqual(delayRangeGeometry(range), {
    leftPercent: `${(100 / 600) * 100}%`,
    widthPercent: `${((240 - 100) / 600) * 100}%`,
  });
  const collapsed = normalizedDelayRangeMs("0", "0");
  assert.equal(delayRangeGeometry(collapsed).widthPercent, "0%");
});

test("syncDelayRangeValues enforces min <= max while dragging either thumb", () => {
  assert.deepEqual(syncDelayRangeValues(240, 100, "min"), { min_seconds: 240, max_seconds: 240 });
  assert.deepEqual(syncDelayRangeValues(100, 240, "min"), { min_seconds: 100, max_seconds: 240 });
  assert.deepEqual(syncDelayRangeValues(100, 60, "max"), { min_seconds: 60, max_seconds: 60 });
  assert.deepEqual(syncDelayRangeValues("bad", "bad", "min"), {
    min_seconds: 30,
    max_seconds: 120,
  });
});

test("delayRange labels describe the active random window", () => {
  const range = normalizedDelayRangeMs("30", "120");
  assert.equal(delayRangeLabel(range), "Random from 30 to 120 s");
  assert.equal(delayRangePreview(range), "Next cycle delay: random 30-120 s");
});
