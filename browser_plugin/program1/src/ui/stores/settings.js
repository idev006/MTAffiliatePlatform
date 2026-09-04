import { defineStore } from "pinia";
import { bridge } from "../bridge.js";
import { normalizedDelayRangeMs } from "../lib/delayRange.mjs";
import {
  DEFAULT_DELAY_MAX_SECONDS,
  DEFAULT_DELAY_MIN_SECONDS,
  DEFAULT_MAX_PAGE_RETRIES,
  DEFAULT_PAGE_LOAD_WAIT_SECONDS,
  DEFAULT_PAGE_RETRY_WAIT_SECONDS,
  DEFAULT_TARGET_URL,
  MAX_PAGE_RETRIES,
  MAX_PAGE_WAIT_SECONDS,
  MIN_PAGE_RETRIES,
  MIN_PAGE_WAIT_SECONDS,
  boundedInteger,
} from "../lib/panelCore.mjs";
import { useProcessStore } from "./process.js";

export const useSettingsStore = defineStore("settings", {
  state: () => ({
    loaded: false,
    backendUrl: "",
    workerId: "",
    targetUrl: DEFAULT_TARGET_URL,
    delayMinSeconds: DEFAULT_DELAY_MIN_SECONDS,
    delayMaxSeconds: DEFAULT_DELAY_MAX_SECONDS,
    pageLoadWaitSeconds: DEFAULT_PAGE_LOAD_WAIT_SECONDS,
    pageRetryWaitSeconds: DEFAULT_PAGE_RETRY_WAIT_SECONDS,
    maxPageRetries: DEFAULT_MAX_PAGE_RETRIES,
    autoResume: true,
    advanceAfterDelivery: true,
  }),

  getters: {
    delayRangeMs(state) {
      return normalizedDelayRangeMs(state.delayMinSeconds, state.delayMaxSeconds);
    },
    configured(state) {
      return Boolean(state.backendUrl.trim() && state.workerId.trim());
    },
    pageLoadWaitMs(state) {
      return (
        boundedInteger(
          state.pageLoadWaitSeconds,
          DEFAULT_PAGE_LOAD_WAIT_SECONDS,
          MIN_PAGE_WAIT_SECONDS,
          MAX_PAGE_WAIT_SECONDS,
        ) * 1000
      );
    },
    pageRetryWaitMs(state) {
      return (
        boundedInteger(
          state.pageRetryWaitSeconds,
          DEFAULT_PAGE_RETRY_WAIT_SECONDS,
          MIN_PAGE_WAIT_SECONDS,
          MAX_PAGE_WAIT_SECONDS,
        ) * 1000
      );
    },
    normalizedMaxPageRetries(state) {
      return boundedInteger(
        state.maxPageRetries,
        DEFAULT_MAX_PAGE_RETRIES,
        MIN_PAGE_RETRIES,
        MAX_PAGE_RETRIES,
      );
    },
  },

  actions: {
    applySettings(settings) {
      this.backendUrl = settings.backend_url ?? this.backendUrl;
      this.workerId = settings.worker_id ?? this.workerId;
      this.targetUrl = settings.target_url ?? DEFAULT_TARGET_URL;
      this.delayMinSeconds = settings.delay_min_seconds ?? DEFAULT_DELAY_MIN_SECONDS;
      this.delayMaxSeconds = settings.delay_max_seconds ?? DEFAULT_DELAY_MAX_SECONDS;
      this.pageLoadWaitSeconds = settings.page_load_wait_seconds ?? DEFAULT_PAGE_LOAD_WAIT_SECONDS;
      this.pageRetryWaitSeconds = settings.page_retry_wait_seconds ?? DEFAULT_PAGE_RETRY_WAIT_SECONDS;
      this.maxPageRetries = settings.max_page_retries ?? DEFAULT_MAX_PAGE_RETRIES;
      this.autoResume = settings.auto_resume !== false;
      this.advanceAfterDelivery = settings.advance_after_delivery !== false;
    },

    async load() {
      const response = await bridge.sendRuntimeMessage({ type: "PROGRAM1_GET_SETTINGS" });
      const settings = response?.settings || {};
      this.applySettings(settings);
      this.loaded = true;
      return response;
    },

    currentSettings() {
      const range = this.delayRangeMs;
      return {
        backend_url: this.backendUrl.trim(),
        worker_id: this.workerId.trim(),
        target_url: (this.targetUrl || DEFAULT_TARGET_URL).trim(),
        delay_min_seconds: range.min_seconds,
        delay_max_seconds: range.max_seconds,
        page_load_wait_seconds: boundedInteger(
          this.pageLoadWaitSeconds,
          DEFAULT_PAGE_LOAD_WAIT_SECONDS,
          MIN_PAGE_WAIT_SECONDS,
          MAX_PAGE_WAIT_SECONDS,
        ),
        page_retry_wait_seconds: boundedInteger(
          this.pageRetryWaitSeconds,
          DEFAULT_PAGE_RETRY_WAIT_SECONDS,
          MIN_PAGE_WAIT_SECONDS,
          MAX_PAGE_WAIT_SECONDS,
        ),
        max_page_retries: this.normalizedMaxPageRetries,
        auto_resume: this.autoResume,
        advance_after_delivery: this.advanceAfterDelivery,
      };
    },

    // Persist without the permission/registration side effects (used when the
    // auto-run advances the target URL between pages).
    async rawSave(settings) {
      return bridge.sendRuntimeMessage({ type: "PROGRAM1_SAVE_SETTINGS", settings });
    },

    // Full Save Settings flow: grant the backend origin, persist, register and
    // heartbeat, mirroring the worker registration protocol.
    async save() {
      const process = useProcessStore();
      const url = this.backendUrl.trim();
      if (url) {
        const granted = await bridge.ensurePagePermission(url);
        if (!granted.ok) {
          return { ok: false, error: "BACKEND_PERMISSION_DENIED", origin: granted.origin };
        }
      }
      const response = await this.rawSave(this.currentSettings());
      process.show(response);
      process.setView({
        state: response?.ok ? (url ? "READY" : "CONFIG_REQUIRED") : "ERROR",
        step: response?.ok
          ? url
            ? "Settings saved; ready to capture"
            : "Backend URL is empty"
          : "Settings could not be saved",
        error: response?.ok ? null : response?.error || "SETTINGS_SAVE_FAILED",
      });
      if (response?.ok && url && this.workerId.trim()) {
        const registered = await process.registerWorker();
        if (registered.ok) {
          await bridge.sendRuntimeMessage({ type: "PROGRAM1_HEARTBEAT" });
        }
      }
      return response;
    },
  },
});
