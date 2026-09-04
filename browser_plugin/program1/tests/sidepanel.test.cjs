const assert = require("node:assert/strict");
const test = require("node:test");

const elements = new Map();

function element(id) {
  if (!elements.has(id)) {
    elements.set(id, {
      addEventListener() {},
      textContent: "",
      value: "",
    });
  }
  return elements.get(id);
}

global.document = {
  getElementById(id) {
    return element(id);
  },
};
global.window = {
  addEventListener() {},
};
global.chrome = {
  tabs: {
    async create() {
      return { id: 1 };
    },
    async get(tabId) {
      return { id: tabId, url: "https://shopee.co.th/search?keyword=ssd" };
    },
    sendMessage(_tabId, _message, callback) {
      callback?.({ ok: true });
    },
    async update(tabId) {
      return { id: tabId };
    },
  },
  permissions: {
    async contains() {
      return true;
    },
    async request() {
      return true;
    },
  },
  runtime: {
    sendMessage(_message, callback) {
      callback?.({ ok: true, settings: {} });
    },
  },
};

const {
  captureStatus,
  processViewFromCapture,
  processViewFromStatus,
  captureTargetFromTab,
  normalizedDelayRangeMs,
  normalizedWebUrl,
  nextShopeeListingPageUrl,
  originPattern,
  randomDelayMs,
  renderRegistryStatus,
  sendTabMessage,
  sendRuntimeMessage,
  stateClassName,
  withWorkerId,
} = require("../src/sidepanel.js");

test("withWorkerId attaches configured worker id to each observation", () => {
  assert.deepEqual(
    withWorkerId([{ observation_id: "obs-1" }, { observation_id: "obs-2" }], " worker-01 "),
    [
      { observation_id: "obs-1", source_worker_id: "worker-01" },
      { observation_id: "obs-2", source_worker_id: "worker-01" },
    ],
  );
});

test("withWorkerId leaves observations unchanged when worker id is blank", () => {
  const observations = [{ observation_id: "obs-1" }];
  assert.equal(withWorkerId(observations, "   "), observations);
  assert.equal(withWorkerId(observations), observations);
});

test("captureStatus reports capture, queue, delivery and remaining outbox counts", () => {
  assert.deepEqual(
    captureStatus(
      { profile: "shopee-current-page-lab-v1", observations: [{}, {}] },
      {
        ok: false,
        queued: true,
        queued_observation_count: 2,
        flush: {
          sent_count: 0,
          accepted_observation_count: 0,
          remaining_count: 1,
          error: "BACKEND_URL_NOT_CONFIGURED",
        },
      },
    ),
    {
      ok: false,
      capture: {
        profile: "shopee-current-page-lab-v1",
        observation_count: 2,
      },
      queue: {
        queued: true,
        queued_observation_count: 2,
        sent_count: 0,
        accepted_observation_count: 0,
        remaining_count: 1,
        error: "BACKEND_URL_NOT_CONFIGURED",
      },
    },
  );
});

test("processViewFromStatus shows configuration readiness and outbox count", () => {
  const view = processViewFromStatus({
    ok: true,
    backend_configured: false,
    worker_configured: false,
    outbox_remaining_count: 2,
    state: "CONFIG_REQUIRED",
  });

  assert.equal(view.state, "CONFIG_REQUIRED");
  assert.equal(view.step, "Configure Backend URL before delivery");
  assert.equal(view.outbox_count, 2);
  assert.equal(view.error, null);
  assert.equal(view.session_accepted_count, 0);
  assert.equal(view.rate_per_hour, 0);
  assert.match(view.last_event, /\d/);
});

test("process views retain runtime transport error details", () => {
  assert.equal(
    processViewFromStatus({ ok: false, error: "MESSAGE_PORT_CLOSED" }).error,
    "MESSAGE_PORT_CLOSED",
  );
  assert.equal(
    captureStatus({ observations: [{}] }, { ok: false, error: "MESSAGE_PORT_CLOSED" }).queue.error,
    "MESSAGE_PORT_CLOSED",
  );
});

test("processViewFromCapture distinguishes delivered from queued delivery block", () => {
  const view = processViewFromCapture(
    { profile: "shopee-current-page-lab-v1", observations: [{}, {}] },
    {
      ok: true,
      queued: true,
      queued_observation_count: 2,
      flush: { sent_count: 1, accepted_observation_count: 2, remaining_count: 0, error: null },
    },
  );

  assert.equal(view.state, "DELIVERED");
  assert.equal(view.step, "Captured, queued and delivered to Back Office");
  assert.equal(view.captured_count, 2);
  assert.equal(view.queued_count, 2);
  assert.equal(view.sent_count, 1);
  assert.equal(view.accepted_count, 2);
  assert.equal(view.outbox_count, 0);
  assert.equal(view.error, null);
  assert.ok(view.session_accepted_count >= 2);
  assert.ok(view.rate_per_hour > 0);
  assert.match(view.last_event, /\d/);
});

test("stateClassName maps blocked states to blocked style", () => {
  assert.equal(stateClassName("DELIVERY_BLOCKED"), "state state--blocked");
  assert.equal(stateClassName("DELIVERED"), "state state--ready");
  assert.equal(stateClassName("IDLE"), "state state--ready");
  assert.equal(stateClassName("COLLECTING"), "state state--working");
});

test("renderRegistryStatus shows a registered worker", () => {
  renderRegistryStatus({ ok: true, registered: true, worker_id: "worker-01", error: null });
  assert.equal(elements.get("registryStatus").textContent, "Registry: registered (worker-01)");
});

test("renderRegistryStatus shows registration failure details", () => {
  renderRegistryStatus({ ok: false, registered: false, worker_id: "", error: "HTTP_409" });
  assert.equal(
    elements.get("registryStatus").textContent,
    "Registry: not registered - HTTP_409",
  );
});

test("renderRegistryStatus hides absent error details", () => {
  renderRegistryStatus({ ok: false, registered: false, worker_id: "", error: null });
  assert.equal(elements.get("registryStatus").textContent, "Registry: not registered");
});

test("renderRegistryStatus handles an unknown response", () => {
  renderRegistryStatus(undefined);
  assert.equal(elements.get("registryStatus").textContent, "Registry: unknown");
});

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

test("sendRuntimeMessage consumes a closed-port runtime error", async () => {
  const originalSendMessage = chrome.runtime.sendMessage;
  chrome.runtime.sendMessage = (_message, callback) => {
    chrome.runtime.lastError = { message: "MESSAGE_PORT_CLOSED" };
    callback();
    delete chrome.runtime.lastError;
  };

  try {
    assert.deepEqual(await sendRuntimeMessage({ type: "TEST" }), {
      ok: false,
      error: "MESSAGE_PORT_CLOSED",
    });
  } finally {
    chrome.runtime.sendMessage = originalSendMessage;
  }
});

test("sendTabMessage consumes a closed-port runtime error", async () => {
  const originalSendMessage = chrome.tabs.sendMessage;
  chrome.tabs.sendMessage = (_tabId, _message, callback) => {
    chrome.runtime.lastError = { message: "The message port closed before a response was received." };
    callback();
    delete chrome.runtime.lastError;
  };

  try {
    assert.deepEqual(await sendTabMessage(1, { type: "TEST" }), {
      ok: false,
      error: "The message port closed before a response was received.",
    });
  } finally {
    chrome.tabs.sendMessage = originalSendMessage;
  }
});
