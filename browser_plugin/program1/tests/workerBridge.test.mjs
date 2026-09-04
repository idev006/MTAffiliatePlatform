import assert from "node:assert/strict";
import test from "node:test";

import { createWorkerBridge } from "../src/ui/lib/workerBridge.mjs";

function fakeChrome() {
  return {
    runtime: {
      lastError: undefined,
      sendMessage(_message, callback) {
        callback?.({ ok: true });
      },
    },
    tabs: {
      sendMessage(_tabId, _message, callback) {
        callback?.({ ok: true });
      },
      query: async () => [{ id: 1, url: "https://shopee.co.th/search?keyword=ssd" }],
    },
    permissions: {
      contains: async () => true,
      request: async () => true,
    },
    scripting: {},
  };
}

test("sendRuntimeMessage consumes a closed-port runtime error", async () => {
  const chrome = fakeChrome();
  chrome.runtime.sendMessage = (_message, callback) => {
    chrome.runtime.lastError = { message: "MESSAGE_PORT_CLOSED" };
    callback();
    delete chrome.runtime.lastError;
  };
  const bridge = createWorkerBridge(chrome);

  assert.deepEqual(await bridge.sendRuntimeMessage({ type: "TEST" }), {
    ok: false,
    error: "MESSAGE_PORT_CLOSED",
  });
});

test("sendTabMessage consumes a closed-port runtime error", async () => {
  const chrome = fakeChrome();
  chrome.tabs.sendMessage = (_tabId, _message, callback) => {
    chrome.runtime.lastError = { message: "The message port closed before a response was received." };
    callback();
    delete chrome.runtime.lastError;
  };
  const bridge = createWorkerBridge(chrome);

  assert.deepEqual(await bridge.sendTabMessage(1, { type: "TEST" }), {
    ok: false,
    error: "The message port closed before a response was received.",
  });
});

test("sendRuntimeMessage reports a missing runtime response", async () => {
  const chrome = fakeChrome();
  chrome.runtime.sendMessage = (_message, callback) => {
    callback();
  };
  const bridge = createWorkerBridge(chrome);

  assert.deepEqual(await bridge.sendRuntimeMessage({ type: "TEST" }), {
    ok: false,
    error: "NO_RUNTIME_RESPONSE",
  });
});

test("ensurePagePermission requests the origin when not already granted", async () => {
  const requested = [];
  const chrome = fakeChrome();
  chrome.permissions.contains = async () => false;
  chrome.permissions.request = async (request) => {
    requested.push(request);
    return true;
  };
  const bridge = createWorkerBridge(chrome);

  assert.deepEqual(await bridge.ensurePagePermission("https://shopee.co.th/search?keyword=ssd"), {
    ok: true,
    origin: "https://shopee.co.th/*",
  });
  assert.deepEqual(requested, [{ origins: ["https://shopee.co.th/*"] }]);
});

test("ensurePagePermission skips the request when already granted", async () => {
  const chrome = fakeChrome();
  let requested = false;
  chrome.permissions.request = async () => {
    requested = true;
    return true;
  };
  const bridge = createWorkerBridge(chrome);

  assert.deepEqual(await bridge.ensurePagePermission("https://shopee.co.th/search?keyword=ssd"), {
    ok: true,
    origin: "https://shopee.co.th/*",
  });
  assert.equal(requested, false);
});

test("bridge exposes tab, permission and collector injection helpers", () => {
  const chrome = fakeChrome();
  chrome.tabs.get = async (tabId) => ({ id: tabId, url: "https://shopee.co.th/search?keyword=ssd" });
  chrome.tabs.create = async ({ url }) => ({ id: 9, url });
  chrome.tabs.update = async () => ({ id: 9 });
  chrome.scripting.executeScript = async ({ files }) => files;
  const bridge = createWorkerBridge(chrome);

  assert.equal(typeof bridge.queryActiveTab, "function");
  assert.equal(typeof bridge.getTab, "function");
  assert.equal(typeof bridge.createTab, "function");
  assert.equal(typeof bridge.focusTab, "function");
  assert.equal(typeof bridge.navigateTab, "function");
  assert.equal(typeof bridge.injectCollector, "function");
});
