import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { createWorkerBridge } from "../src/ui/lib/workerBridge.mjs";

test("manual capture installs a message receiver on a fresh page", async () => {
  const listeners = [];
  const context = vm.createContext({
    console, URL,
    chrome: { runtime: { onMessage: { addListener: (fn) => listeners.push(fn) } } },
  });
  const bridge = createWorkerBridge({ scripting: {
    executeScript: async ({ target, files }) => {
      assert.equal(target.tabId, 42);
      for (const file of files) {
        vm.runInContext(readFileSync(new URL(`../${file}`, import.meta.url), "utf8"), context);
      }
    },
  } });
  await bridge.injectCollector(42);
  assert.equal(listeners.length, 1);
  await bridge.injectCollector(42);
  assert.equal(listeners.length, 1, "reinjection must not duplicate message receivers");
});
