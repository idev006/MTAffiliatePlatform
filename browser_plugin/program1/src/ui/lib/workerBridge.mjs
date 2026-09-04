// Messaging/permission bridge between the Vue panel and the extension runtime.
// A factory over an injected chrome-like object so node:test can exercise the
// transport error paths with a fake, without a DOM or a real browser.

import { originPattern } from "./webUrl.mjs";

export function createWorkerBridge(chromeApi) {
  const chrome = chromeApi;

  function sendRuntimeMessage(message) {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage(message, (response) => {
          const runtimeError = chrome.runtime.lastError;
          if (runtimeError) {
            resolve({ ok: false, error: runtimeError.message || String(runtimeError) });
            return;
          }
          resolve(response ?? { ok: false, error: "NO_RUNTIME_RESPONSE" });
        });
      } catch (error) {
        resolve({
          ok: false,
          error: error && typeof error.message === "string" ? error.message : String(error),
        });
      }
    });
  }

  function sendTabMessage(tabId, message) {
    return new Promise((resolve) => {
      try {
        chrome.tabs.sendMessage(tabId, message, (response) => {
          const runtimeError = chrome.runtime.lastError;
          if (runtimeError) {
            resolve({ ok: false, error: runtimeError.message || String(runtimeError) });
            return;
          }
          resolve(response ?? { ok: false, error: "NO_TAB_RESPONSE" });
        });
      } catch (error) {
        resolve({
          ok: false,
          error: error && typeof error.message === "string" ? error.message : String(error),
        });
      }
    });
  }

  async function ensurePagePermission(tabUrl) {
    const origin = originPattern(tabUrl);
    const hasPermission = await chrome.permissions.contains({ origins: [origin] });
    if (hasPermission) return { ok: true, origin };
    const granted = await chrome.permissions.request({ origins: [origin] });
    return { ok: granted, origin };
  }

  async function queryActiveTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab;
  }

  async function getTab(tabId) {
    return chrome.tabs.get(tabId);
  }

  async function createTab(url) {
    return chrome.tabs.create({ url, active: true });
  }

  async function focusTab(tabId) {
    return chrome.tabs.update(tabId, { active: true });
  }

  async function navigateTab(tabId, url) {
    return chrome.tabs.update(tabId, { url, active: true });
  }

  async function injectCollector(tabId) {
    return chrome.scripting.executeScript({
      target: { tabId },
      files: ["src/content.js"],
    });
  }

  return {
    ensurePagePermission,
    sendRuntimeMessage,
    sendTabMessage,
    queryActiveTab,
    getTab,
    createTab,
    focusTab,
    navigateTab,
    injectCollector,
  };
}
