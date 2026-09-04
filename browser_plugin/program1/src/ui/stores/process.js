import { defineStore } from "pinia";
import { bridge } from "../bridge.js";
import { randomDelayMs } from "../lib/delayRange.mjs";
import {
  captureStatus,
  createIndicators,
  DEFAULT_TARGET_URL,
  humanPageText,
  processViewFromCapture,
  processViewFromStatus,
  registryStatusText,
  withWorkerId,
} from "../lib/panelCore.mjs";
import { captureTargetFromTab, nextShopeeListingPageUrl, normalizedWebUrl, pageParamOf } from "../lib/webUrl.mjs";
import { useSettingsStore } from "./settings.js";

const TICK_MS = 250;
const ACTIVITY_LIMIT = 500;

// Non-reactive machine timers (one process store per panel page).
let autoTimerId = null;
let autoTickTimerId = null;
let autoTimerDeadline = 0;

function localeNow() {
  return new Date().toLocaleTimeString();
}

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

export const useProcessStore = defineStore("process", {
  state: () => ({
    state: "LOADING",
    step: "Checking worker settings",
    lastError: "",
    lastEvent: "waiting",
    capturedCount: 0,
    queuedCount: 0,
    sentCount: 0,
    acceptedCount: 0,
    outboxCount: 0,
    cycleCount: 0,
    sessionAcceptedCount: 0,
    ratePerHour: 0,
    autoRunning: false,
    autoInFlight: false,
    sessionStartedAt: null,
    registryText: "Registry: not registered",
    activeTargetTabId: null,
    countdownSeconds: null,
    lastPayload: null,
    activity: [],
  }),

  getters: {
    // The status line shows the countdown while one is scheduled (the old panel
    // wrote "Next auto cycle in Ns" into the same status element between cycles).
    displayStep(state) {
      if (state.autoRunning && state.countdownSeconds !== null) {
        return `Next auto cycle in ${state.countdownSeconds}s`;
      }
      return state.step;
    },
    lastPayloadText() {
      return this.lastPayload === null ? "" : JSON.stringify(this.lastPayload, null, 2);
    },
  },

  actions: {
    activityEntry(kind, text, payload) {
      this.activity.push({ at: localeNow(), kind, text, payload: payload ?? null });
      if (this.activity.length > ACTIVITY_LIMIT) {
        this.activity.splice(0, this.activity.length - ACTIVITY_LIMIT);
      }
    },

    // Merge a process view into the store; only provided keys are applied so
    // metric rows are not zeroed by incidental UI steps.
    setView(view) {
      if (view.state !== undefined) this.state = view.state;
      if (view.step !== undefined) {
        this.step = view.step;
        this.activityEntry("process", view.step);
      }
      if (view.error !== undefined) this.lastError = view.error ?? "";
      if (view.captured_count !== undefined) this.capturedCount = view.captured_count || 0;
      if (view.queued_count !== undefined) this.queuedCount = view.queued_count || 0;
      if (view.sent_count !== undefined) this.sentCount = view.sent_count || 0;
      if (view.accepted_count !== undefined) this.acceptedCount = view.accepted_count || 0;
      if (view.outbox_count !== undefined) this.outboxCount = view.outbox_count || 0;
      if (view.cycle_count !== undefined) this.cycleCount = view.cycle_count || 0;
      if (view.session_accepted_count !== undefined) this.sessionAcceptedCount = view.session_accepted_count || 0;
      if (view.rate_per_hour !== undefined) this.ratePerHour = view.rate_per_hour || 0;
      if (view.last_event !== undefined) this.lastEvent = view.last_event;
    },

    indicators(acceptedDelta = 0) {
      return createIndicators({
        autoRunCount: this.cycleCount,
        sessionAcceptedTotal: this.sessionAcceptedCount,
        sessionStartedAt: this.sessionStartedAt,
        acceptedDelta,
      });
    },

    show(payload) {
      this.lastPayload = payload;
      this.activityEntry("payload", "Result payload", payload);
      return payload;
    },

    async refreshStatus() {
      const response = await bridge.sendRuntimeMessage({ type: "PROGRAM1_GET_PROCESS_STATUS" });
      this.setView(processViewFromStatus(response, this.indicators(0)));
      if (response?.run_state) {
        this.applyRunState(response.run_state);
      }
      this.renderRegistry({
        ok: Boolean(response?.ok),
        registered: Boolean(response?.registry?.registered),
        worker_id: response?.registry?.worker_id || "",
        error: response?.registry?.last_error || null,
      });
      return response;
    },

    applyRunState(runState) {
      if (!runState) return;
      this.autoRunning = Boolean(runState.desired);
      this.activeTargetTabId = runState.active_target_tab_id ?? this.activeTargetTabId;
      this.cycleCount = runState.cycle_count ?? this.cycleCount;
      this.sessionAcceptedCount = runState.session_accepted_count ?? this.sessionAcceptedCount;
      this.sessionStartedAt = runState.session_started_at ?? this.sessionStartedAt;
      if (runState.last_step) this.step = runState.last_step;
      if (runState.last_error) this.lastError = runState.last_error;
    },

    async persistRunState(desired = this.autoRunning, extra = {}) {
      return bridge.sendRuntimeMessage({
        type: "PROGRAM1_SAVE_RUN_STATE",
        run_state: {
          desired,
          active_target_tab_id: this.activeTargetTabId,
          cycle_count: this.cycleCount,
          session_accepted_count: this.sessionAcceptedCount,
          session_started_at: this.sessionStartedAt,
          last_step: this.displayStep,
          last_error: this.lastError || null,
          ...extra,
        },
      });
    },

    renderRegistry(response) {
      this.registryText = registryStatusText(response);
      this.activityEntry("registry", this.registryText);
    },

    async registerWorker() {
      const response = await bridge.sendRuntimeMessage({ type: "PROGRAM1_REGISTER_WORKER" });
      this.renderRegistry(response);
      return response;
    },

    // Panel bootstrap: load settings + status, then register if a worker is
    // configured so the panel shows a live registry line even before any save.
    async init() {
      const settings = useSettingsStore();
      await settings.load();
      this.sessionStartedAt = Date.now();
      await this.refreshStatus();
      if (settings.configured) {
        const registered = await this.registerWorker();
        if (registered.ok) {
          await bridge.sendRuntimeMessage({ type: "PROGRAM1_HEARTBEAT" });
        }
      }
      this.activityEntry("process", `Panel ready (${localeNow()})`);
      const runState = await bridge.sendRuntimeMessage({ type: "PROGRAM1_GET_RUN_STATE" });
      if (runState?.run_state) {
        this.applyRunState(runState.run_state);
        if (runState.run_state.desired) {
          this.activityEntry(
            "process",
            "Background run remains active independently of the Side Panel",
          );
        }
      }
    },

    async flushOutbox() {
      const response = await bridge.sendRuntimeMessage({ type: "PROGRAM1_FLUSH_OUTBOX" });
      this.setView({
        state: response?.ok ? "DELIVERED" : "DELIVERY_BLOCKED",
        step: response?.ok ? "Outbox delivered" : "Outbox delivery is blocked",
        sent_count: response?.sent_count || 0,
        accepted_count: response?.accepted_observation_count || 0,
        outbox_count: response?.remaining_count || 0,
        error: response?.error || null,
      });
      await this.persistRunState(this.autoRunning);
      this.show(response);
      return response;
    },

    async openTargetPage() {
      const settings = useSettingsStore();
      const target = normalizedWebUrl(settings.targetUrl);
      if (!target.ok) {
        this.setView({ state: "PAGE_UNSUPPORTED", step: "Target page URL is not valid", error: target.error });
        return this.show(target);
      }
      const tab = await bridge.createTab(target.url);
      this.activeTargetTabId = tab.id;
      this.setView({ state: "READY", step: "Target page opened; wait for it to load, then capture", error: null });
      return this.show({ ok: true, opened_url: target.url });
    },

    async manualCapture() {
      const tab = await bridge.queryActiveTab();
      return this.captureTargetOnce(captureTargetFromTab(tab));
    },

    async captureTargetOnce(captureTarget) {
      if (!captureTarget.ok) {
        this.setView({
          state: "PAGE_UNSUPPORTED",
          step: "Open a Shopee web page before capture",
          error: captureTarget.error,
        });
        this.show(captureTarget);
        return { ok: false, error: captureTarget.error };
      }
      try {
        this.setView({ state: "COLLECTING", step: "Checking page permission", error: null });
        const pagePermission = await bridge.ensurePagePermission(captureTarget.url);
        if (!pagePermission.ok) {
          this.setView({
            state: "ERROR",
            step: "Page permission was not granted",
            error: `PAGE_PERMISSION_DENIED ${pagePermission.origin}`,
          });
          const result = { ok: false, error: "PAGE_PERMISSION_DENIED", origin: pagePermission.origin };
          this.show(result);
          return result;
        }
        this.setView({ state: "COLLECTING", step: "Injecting collector into active page", error: null });
        await bridge.injectCollector(captureTarget.tabId);
        this.setView({ state: "COLLECTING", step: "Reading visible product observations", error: null });
        const response = await bridge.sendTabMessage(captureTarget.tabId, {
          type: "PROGRAM1_CAPTURE_CURRENT_PAGE",
        });
        if (!response?.ok) {
          const failure = response?.error || "PAGE_UNSUPPORTED";
          const failureState =
            failure === "PAGE_UNSUPPORTED" || failure === "PAGE_BLOCKED_BY_ANTIBOT" ? failure : "ERROR";
          const failureStep =
            failure === "PAGE_BLOCKED_BY_ANTIBOT"
              ? "Blocked by Shopee verification/anti-bot; not treated as a harvest"
              : failure === "PAGE_UNSUPPORTED"
                ? "Active page is not supported by the current profile"
                : "Collector could not read the active tab";
          const pageUrl = response?.page_url || captureTarget.url;
          this.setView({
            state: failureState,
            step: `${failureStep}${pageUrl ? ` (${pageUrl})` : ""}`,
            error: failure,
          });
          const result = response || { ok: false, error: "PAGE_UNSUPPORTED" };
          this.show(result);
          return result;
        }
        const settings = useSettingsStore();
        const observations = withWorkerId(response.observations, settings.workerId);
        const batch = { batch_id: crypto.randomUUID(), observations };
        this.setView({
          state: "QUEUED",
          step: `Captured ${observations.length} observations; queueing batch`,
          error: null,
          captured_count: observations.length,
        });
        const queueResponse = await bridge.sendRuntimeMessage({ type: "PROGRAM1_QUEUE_BATCH", payload: batch });
        this.setView(
          processViewFromCapture(
            response,
            queueResponse,
            this.indicators(queueResponse?.flush?.accepted_observation_count || 0),
          ),
        );
        await this.persistRunState(this.autoRunning);
        const result = {
          ...captureStatus(response, queueResponse),
          pagination: response?.pagination || null,
          page_url: response?.page_url || captureTarget.url,
        };
        this.show(result);
        return result;
      } catch (error) {
        const message = error && typeof error.message === "string" ? error.message : String(error);
        const result = { ok: false, error: message };
        this.setView({ state: "ERROR", step: "Capture failed before collector response", error: message });
        this.show(result);
        return result;
      }
    },

    // Bounded retry for mid-run PAGE_UNSUPPORTED: a Shopee listing page can render
    // its shell before products hydrate (throttle/slow render). A genuine listing
    // shell gets one 5 s retry and, if it still has zero hydrated items, one more
    // 12 s retry before the run fails closed — never an unbounded wait, and never a
    // fake empty harvest.
    async captureTargetWithRetry(captureTarget) {
      const firstResult = await this.captureTargetOnce(captureTarget);
      if (firstResult?.ok || firstResult?.error !== "PAGE_UNSUPPORTED") {
        return firstResult;
      }
      const settings = useSettingsStore();
      let lastResult = firstResult;
      for (let attempt = 1; attempt <= settings.normalizedMaxPageRetries; attempt += 1) {
        await this.retryCaptureAfter(
          captureTarget,
          `Page not ready; retry ${attempt}/${settings.normalizedMaxPageRetries}`,
          settings.pageRetryWaitMs,
        );
        lastResult = await this.captureTargetOnce(captureTarget);
        if (lastResult?.ok || lastResult?.error !== "PAGE_UNSUPPORTED") {
          return lastResult;
        }
      }
      return lastResult;
    },

    async retryCaptureAfter(captureTarget, stepText, waitMs) {
      this.setView({
        state: "COLLECTING",
        step: stepText,
        error: null,
        ...this.indicators(0),
      });
      await sleep(waitMs);
    },

    async getOrOpenTargetTab() {
      if (this.activeTargetTabId !== null) {
        try {
          const tab = await bridge.getTab(this.activeTargetTabId);
          const captureTarget = captureTargetFromTab(tab);
          if (captureTarget.ok) {
            await bridge.focusTab(this.activeTargetTabId);
            return captureTarget;
          }
        } catch (_error) {
          this.activeTargetTabId = null;
        }
      }
      const settings = useSettingsStore();
      const target = normalizedWebUrl(settings.targetUrl);
      if (!target.ok) return target;
      const tab = await bridge.createTab(target.url);
      this.activeTargetTabId = tab.id;
      await this.persistRunState(this.autoRunning);
      await sleep(settings.pageLoadWaitMs);
      return captureTargetFromTab({ ...tab, url: target.url });
    },

    async advanceTargetAfterDelivery(result) {
      const settings = useSettingsStore();
      if (!settings.advanceAfterDelivery || !result?.ok) return;
      const pagination = result?.pagination || null;
      if (pagination && pagination.has_next === false) {
        const where = humanPageText(pagination);
        if (this.autoRunning) {
          this.stopAutoRun(`Auto run finished: reached the last page${where ? ` (${where})` : ""}`);
        } else {
          this.setView({
            state: "DELIVERED",
            step: `Delivered; this listing is complete${where ? ` (${where})` : ""}`,
            error: null,
            ...this.indicators(0),
          });
        }
        return;
      }
      const currentUrl = settings.targetUrl || DEFAULT_TARGET_URL;
      const nextTarget =
        pagination?.next_url !== null && pagination?.next_url !== undefined
          ? normalizedWebUrl(pagination.next_url)
          : nextShopeeListingPageUrl(currentUrl);
      if (!nextTarget.ok) {
        this.setView({
          state: "DELIVERED",
          step: `Delivered; target advance skipped: ${nextTarget.error}`,
          error: null,
          ...this.indicators(0),
        });
        return;
      }
      if (nextTarget.page === undefined) {
        nextTarget.page = pageParamOf(nextTarget.url);
      }
      settings.targetUrl = nextTarget.url;
      await settings.rawSave(settings.currentSettings());
      if (this.activeTargetTabId !== null) {
        try {
          await bridge.navigateTab(this.activeTargetTabId, nextTarget.url);
          await this.persistRunState(this.autoRunning, { last_step: `Navigated target to ${nextTarget.url}` });
          await sleep(settings.pageLoadWaitMs);
        } catch (_error) {
          this.activeTargetTabId = null;
        }
      }
      const totalText =
        pagination?.total_pages === null || pagination?.total_pages === undefined
          ? ""
          : ` of ${pagination.total_pages}`;
      this.setView({
        state: "READY",
        step: `Delivered; advanced target to page ${nextTarget.page + 1}${totalText}`,
        error: null,
        ...this.indicators(0),
      });
      await this.persistRunState(this.autoRunning);
    },

    stopCountdownTicker() {
      if (autoTickTimerId !== null) {
        clearInterval(autoTickTimerId);
        autoTickTimerId = null;
      }
      this.countdownSeconds = null;
      autoTimerDeadline = 0;
    },

    startCountdownTicker(delayMs) {
      this.stopCountdownTicker();
      autoTimerDeadline = Date.now() + delayMs;
      const tick = () => {
        if (!this.autoRunning || autoTimerDeadline <= 0) {
          this.stopCountdownTicker();
          return;
        }
        const remainingSeconds = Math.max(0, Math.ceil((autoTimerDeadline - Date.now()) / 1000));
        this.countdownSeconds = remainingSeconds;
        if (remainingSeconds <= 0) this.stopCountdownTicker();
      };
      tick();
      autoTickTimerId = setInterval(tick, TICK_MS);
    },

    async stopAutoRun(reason = "Background run stopped by operator") {
      this.stopCountdownTicker();
      const response = await bridge.sendRuntimeMessage({
        type: "PROGRAM1_STOP_BACKGROUND_RUN",
      });
      this.autoRunning = false;
      this.setView({
        state: response?.last_error ? "ERROR" : "IDLE",
        step: reason,
        error: response?.last_error || null,
      });
      await this.refreshStatus();
      return this.show(response);
    },

    scheduleNextAutoCapture() {
      if (!this.autoRunning) return;
      if (autoTimerId !== null) {
        clearTimeout(autoTimerId);
        autoTimerId = null;
      }
      const settings = useSettingsStore();
      const delayMs = randomDelayMs(settings.delayRangeMs);
      this.startCountdownTicker(delayMs);
      void this.persistRunState(true, { last_step: `Next auto cycle scheduled in ${Math.round(delayMs / 1000)}s` });
      autoTimerId = setTimeout(() => this.runAutoCaptureCycle(), delayMs);
    },

    async runAutoCaptureCycle() {
      if (!this.autoRunning || this.autoInFlight) return;
      this.autoInFlight = true;
      this.stopCountdownTicker();
      this.cycleCount += 1;
      try {
        this.setView({
          state: "COLLECTING",
          step: `Auto run cycle ${this.cycleCount}: preparing target page`,
          error: null,
        });
        await this.persistRunState(true);
        const captureTarget = await this.getOrOpenTargetTab();
        const result = await this.captureTargetWithRetry(captureTarget);
        if (!result?.ok) {
          const pageUrl = result?.page_url || (captureTarget.ok ? captureTarget.url : "");
          this.stopAutoRun(
            `Auto run stopped: ${result?.error || "capture failed"}${pageUrl ? ` (${pageUrl})` : ""}`,
          );
        } else {
          await this.advanceTargetAfterDelivery(result);
        }
      } finally {
        this.autoInFlight = false;
        this.scheduleNextAutoCapture();
      }
    },

    async startAutoRun() {
      this.setView({
        state: "COLLECTING",
        step: "Requesting background-owned discovery run",
        error: null,
      });
      const response = await bridge.sendRuntimeMessage({
        type: "PROGRAM1_START_BACKGROUND_RUN",
      });
      if (!response?.ok) {
        this.autoRunning = false;
        this.setView({
          state: "ERROR",
          step: "Background run could not start",
          error: response?.error || "BACKGROUND_RUN_START_FAILED",
        });
        return this.show(response);
      }
      this.autoRunning = Boolean(response?.run_state?.desired);
      this.applyRunState(response?.run_state);
      await this.refreshStatus();
      return this.show(response);
    },
  },
});
