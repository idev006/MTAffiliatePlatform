const backendUrl = document.getElementById("backendUrl");
const workerId = document.getElementById("workerId");
const targetUrl = document.getElementById("targetUrl");
const advanceAfterDelivery = document.getElementById("advanceAfterDelivery");
const delayMinSeconds = document.getElementById("delayMinSeconds");
const delayMaxSeconds = document.getElementById("delayMaxSeconds");
const delayRangeLabel = document.getElementById("delayRangeLabel");
const delayMaxReadout = document.getElementById("delayMaxReadout");
const delayRangeFill = document.getElementById("delayRangeFill");
const delayPreview = document.getElementById("delayPreview");
const startAuto = document.getElementById("startAuto");
const stopAuto = document.getElementById("stopAuto");
const status = document.getElementById("status");
const state = document.getElementById("state");
const step = document.getElementById("step");
const lastError = document.getElementById("lastError");
const registryStatus = document.getElementById("registryStatus");
const capturedCount = document.getElementById("capturedCount");
const acceptedCount = document.getElementById("acceptedCount");
const sentCount = document.getElementById("sentCount");
const queuedCount = document.getElementById("queuedCount");
const outboxCount = document.getElementById("outboxCount");
const cycleCount = document.getElementById("cycleCount");
const sessionAcceptedCount = document.getElementById("sessionAcceptedCount");
const ratePerHour = document.getElementById("ratePerHour");
const lastEvent = document.getElementById("lastEvent");
const DEFAULT_TARGET_URL = "https://shopee.co.th/search?keyword=ssd";
const DEFAULT_DELAY_MIN_SECONDS = 30;
const DEFAULT_DELAY_MAX_SECONDS = 120;
const MIN_DELAY_SECONDS = 0;
const MAX_DELAY_SECONDS = 600;
const TARGET_LOAD_WAIT_MS = 3500;
const TARGET_CAPTURE_RETRY_WAIT_MS = 5000;
let activeTargetTabId = null;
let autoTimerId = null;
let autoTickTimerId = null;
let autoTimerDeadline = 0;
let autoRunning = false;
let autoInFlight = false;
let autoRunCount = 0;
let sessionAcceptedTotal = 0;
let sessionStartedAt = null;

function show(value) {
  status.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

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

function renderRegistryStatus(response) {
  if (!registryStatus) return;
  if (!response) {
    registryStatus.textContent = "Registry: unknown";
    return;
  }
  if (response.ok && response.registered) {
    registryStatus.textContent = `Registry: registered (${response.worker_id})`;
    return;
  }
  registryStatus.textContent = `Registry: not registered${
    response.error ? ` - ${response.error}` : ""
  }`;
}

async function registerCurrentWorker() {
  const response = await sendRuntimeMessage({ type: "PROGRAM1_REGISTER_WORKER" });
  renderRegistryStatus(response);
  return response;
}

function stateClassName(value) {
  if (["IDLE", "READY", "DELIVERED"].includes(value)) return "state state--ready";
  if (["COLLECTING", "QUEUED"].includes(value)) return "state state--working";
  if (
    [
      "CONFIG_REQUIRED",
      "DELIVERY_BLOCKED",
      "PAGE_UNSUPPORTED",
      "PAGE_BLOCKED_BY_ANTIBOT",
      "ERROR",
    ].includes(value)
  ) {
    return "state state--blocked";
  }
  return "state state--idle";
}

function updateProcess(view) {
  if (!state) return;
  state.textContent = view.state;
  state.className = stateClassName(view.state);
  step.textContent = view.step;
  lastError.textContent = view.error || "";
  capturedCount.textContent = String(view.captured_count || 0);
  acceptedCount.textContent = String(view.accepted_count || 0);
  sentCount.textContent = String(view.sent_count || 0);
  queuedCount.textContent = String(view.queued_count || 0);
  outboxCount.textContent = String(view.outbox_count || 0);
  if (typeof view.cycle_count === "number") cycleCount.textContent = String(view.cycle_count);
  if (typeof view.session_accepted_count === "number") {
    sessionAcceptedCount.textContent = String(view.session_accepted_count);
  }
  if (typeof view.rate_per_hour === "number") {
    ratePerHour.textContent = String(view.rate_per_hour);
  }
  if (view.last_event) lastEvent.textContent = `Last event: ${view.last_event}`;
}

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function withWorkerId(observations, workerIdValue) {
  const sourceWorkerId = String(workerIdValue || "").trim();
  if (!sourceWorkerId) return observations;
  return observations.map((observation) => ({
    ...observation,
    source_worker_id: sourceWorkerId,
  }));
}

function captureStatus(captureResponse, queueResponse) {
  const acceptedObservationCount = queueResponse?.flush?.accepted_observation_count || 0;
  return {
    ok: Boolean(queueResponse?.ok),
    capture: {
      profile: captureResponse?.profile || null,
      observation_count: captureResponse?.observations?.length || 0,
    },
    queue: {
      queued: Boolean(queueResponse?.queued),
      queued_observation_count: queueResponse?.queued_observation_count || 0,
      sent_count: queueResponse?.flush?.sent_count || 0,
      accepted_observation_count: acceptedObservationCount,
      remaining_count: queueResponse?.flush?.remaining_count || 0,
      error: queueResponse?.flush?.error || queueResponse?.error || null,
    },
  };
}

function currentMachineIndicators(acceptedDelta = 0) {
  if (sessionStartedAt === null) sessionStartedAt = Date.now();
  sessionAcceptedTotal += acceptedDelta;
  const elapsedHours = Math.max((Date.now() - sessionStartedAt) / 3600000, 1 / 3600);
  return {
    cycle_count: autoRunCount,
    session_accepted_count: sessionAcceptedTotal,
    rate_per_hour: Math.round(sessionAcceptedTotal / elapsedHours),
    last_event: new Date().toLocaleTimeString(),
  };
}

function processViewFromCapture(captureResponse, queueResponse) {
  const summary = captureStatus(captureResponse, queueResponse);
  const error = summary.queue.error;
  const indicators = currentMachineIndicators(summary.queue.accepted_observation_count);
  return {
    state: summary.ok ? "DELIVERED" : "DELIVERY_BLOCKED",
    step: summary.ok
      ? "Captured, queued and delivered to Back Office"
      : "Captured and queued locally; delivery is blocked",
    captured_count: summary.capture.observation_count,
    queued_count: summary.queue.queued_observation_count,
    sent_count: summary.queue.sent_count,
    accepted_count: summary.queue.accepted_observation_count,
    outbox_count: summary.queue.remaining_count,
    error,
    ...indicators,
  };
}

function processViewFromStatus(response) {
  return {
    state: response?.state || "ERROR",
    step: response?.backend_configured
      ? "Ready to capture the active Shopee page"
      : "Configure Backend URL before delivery",
    captured_count: 0,
    queued_count: 0,
    sent_count: 0,
    accepted_count: 0,
    outbox_count: response?.outbox_remaining_count || 0,
    error: response?.ok ? null : response?.error || "STATUS_UNAVAILABLE",
    ...currentMachineIndicators(0),
  };
}

function originPattern(value) {
  const url = new URL(value);
  return `${url.protocol}//${url.host}/*`;
}

function normalizedWebUrl(value) {
  const rawValue = String(value || "").trim();
  if (!rawValue) return { ok: false, error: "TARGET_URL_REQUIRED" };
  try {
    const url = new URL(rawValue);
    if (!["http:", "https:"].includes(url.protocol)) {
      return { ok: false, error: "TARGET_URL_NOT_A_WEB_PAGE", url: rawValue };
    }
    return { ok: true, url: url.toString() };
  } catch (_error) {
    return { ok: false, error: "TARGET_URL_INVALID", url: rawValue };
  }
}

function nextShopeeListingPageUrl(value) {
  const normalized = normalizedWebUrl(value);
  if (!normalized.ok) return normalized;
  const url = new URL(normalized.url);
  if (url.hostname !== "shopee.co.th") {
    return { ok: false, error: "TARGET_NOT_SHOPEE", url: normalized.url };
  }
  if (/-i\.\d+\.\d+(?:\/|$)/.test(url.pathname) || /^\/product\/\d+\/\d+(?:\/|$)/.test(url.pathname)) {
    return { ok: false, error: "TARGET_IS_PRODUCT_DETAIL", url: normalized.url };
  }
  const currentPage = Number.parseInt(url.searchParams.get("page") || "0", 10);
  const nextPage = Number.isFinite(currentPage) && currentPage >= 0 ? currentPage + 1 : 1;
  url.searchParams.set("page", String(nextPage));
  return { ok: true, url: url.toString(), page: nextPage };
}

function boundedDelaySeconds(value, defaultValue) {
  const seconds = Number.parseInt(String(value ?? ""), 10);
  const safeSeconds = Number.isFinite(seconds) ? seconds : defaultValue;
  return Math.min(MAX_DELAY_SECONDS, Math.max(MIN_DELAY_SECONDS, safeSeconds));
}

function normalizedDelayRangeMs(minValue, maxValue) {
  const first = boundedDelaySeconds(minValue, DEFAULT_DELAY_MIN_SECONDS);
  const second = boundedDelaySeconds(maxValue, DEFAULT_DELAY_MAX_SECONDS);
  const minSeconds = Math.min(first, second);
  const maxSeconds = Math.max(first, second);
  return {
    min_seconds: minSeconds,
    max_seconds: maxSeconds,
    min_ms: minSeconds * 1000,
    max_ms: maxSeconds * 1000,
  };
}

function randomDelayMs(range, randomSource = Math.random) {
  const minMs = Math.min(range.min_ms, range.max_ms);
  const maxMs = Math.max(range.min_ms, range.max_ms);
  if (minMs === maxMs) return minMs;
  return Math.floor(minMs + randomSource() * (maxMs - minMs + 1));
}

function currentDelayRangeMs() {
  return normalizedDelayRangeMs(delayMinSeconds.value, delayMaxSeconds.value);
}

function updateDelayRangeLabel() {
  const range = currentDelayRangeMs();
  delayMinSeconds.value = String(range.min_seconds);
  delayMaxSeconds.value = String(range.max_seconds);
  delayRangeLabel.textContent = String(range.min_seconds);
  if (delayMaxReadout) delayMaxReadout.textContent = String(range.max_seconds);
  if (delayRangeFill?.style) {
    const minPercent = (range.min_seconds / MAX_DELAY_SECONDS) * 100;
    const widthPercent = ((range.max_seconds - range.min_seconds) / MAX_DELAY_SECONDS) * 100;
    delayRangeFill.style.left = `${minPercent}%`;
    delayRangeFill.style.width = `${Math.max(0, widthPercent)}%`;
  }
  if (delayPreview) {
    delayPreview.textContent = `Next cycle delay: random ${range.min_seconds}-${range.max_seconds} s`;
  }
  return range;
}

function syncDelayRange(updatedThumb) {
  const minValue = Number.parseInt(delayMinSeconds.value, 10);
  const maxValue = Number.parseInt(delayMaxSeconds.value, 10);
  if (!Number.isFinite(minValue) || !Number.isFinite(maxValue)) {
    updateDelayRangeLabel();
    return;
  }
  if (updatedThumb === "min" && minValue > maxValue) {
    delayMaxSeconds.value = String(minValue);
  }
  if (updatedThumb === "max" && maxValue < minValue) {
    delayMinSeconds.value = String(maxValue);
  }
  updateDelayRangeLabel();
}

function currentSettings() {
  const range = updateDelayRangeLabel();
  return {
    backend_url: backendUrl.value.trim(),
    worker_id: workerId.value.trim(),
    target_url: (targetUrl.value || DEFAULT_TARGET_URL).trim(),
    delay_min_seconds: range.min_seconds,
    delay_max_seconds: range.max_seconds,
    advance_after_delivery: Boolean(advanceAfterDelivery.checked),
  };
}

function captureTargetFromTab(tab) {
  if (!tab?.id) return { ok: false, error: "NO_ACTIVE_TAB" };
  if (!tab.url) return { ok: false, error: "ACTIVE_TAB_URL_UNAVAILABLE" };
  try {
    const url = new URL(tab.url);
    if (!["http:", "https:"].includes(url.protocol)) {
      return { ok: false, error: "ACTIVE_TAB_NOT_A_WEB_PAGE", url: tab.url };
    }
    return { ok: true, tabId: tab.id, url: tab.url };
  } catch (_error) {
    return { ok: false, error: "ACTIVE_TAB_URL_INVALID", url: tab.url };
  }
}

async function ensurePagePermission(tabUrl) {
  const origin = originPattern(tabUrl);
  const hasPermission = await chrome.permissions.contains({ origins: [origin] });
  if (hasPermission) return { ok: true, origin };
  const granted = await chrome.permissions.request({ origins: [origin] });
  return { ok: granted, origin };
}

async function getActiveWebCaptureTarget() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return captureTargetFromTab(tab);
}

async function getOrOpenTargetTab() {
  if (activeTargetTabId !== null) {
    try {
      const tab = await chrome.tabs.get(activeTargetTabId);
      const captureTarget = captureTargetFromTab(tab);
      if (captureTarget.ok) {
        await chrome.tabs.update(activeTargetTabId, { active: true });
        return captureTarget;
      }
    } catch (_error) {
      activeTargetTabId = null;
    }
  }

  const target = normalizedWebUrl(targetUrl.value || DEFAULT_TARGET_URL);
  if (!target.ok) return target;
  const tab = await chrome.tabs.create({ url: target.url, active: true });
  activeTargetTabId = tab.id;
  await sleep(TARGET_LOAD_WAIT_MS);
  return captureTargetFromTab({ ...tab, url: target.url });
}

sendRuntimeMessage({ type: "PROGRAM1_GET_SETTINGS" }).then((response) => {
  const settings = response?.settings || {};
  backendUrl.value = settings.backend_url || "";
  workerId.value = settings.worker_id || "";
  targetUrl.value = settings.target_url || DEFAULT_TARGET_URL;
  delayMinSeconds.value = String(settings.delay_min_seconds ?? DEFAULT_DELAY_MIN_SECONDS);
  delayMaxSeconds.value = String(settings.delay_max_seconds ?? DEFAULT_DELAY_MAX_SECONDS);
  advanceAfterDelivery.checked = settings.advance_after_delivery !== false;
  updateDelayRangeLabel();
  if (!response?.ok) show(response);
});
targetUrl.value = DEFAULT_TARGET_URL;

sendRuntimeMessage({ type: "PROGRAM1_GET_PROCESS_STATUS" }).then((response) => {
  updateProcess(processViewFromStatus(response));
  renderRegistryStatus({
    ok: Boolean(response?.ok),
    registered: Boolean(response?.registry?.registered),
    worker_id: response?.registry?.worker_id || "",
    error: response?.registry?.last_error || null,
  });
});

async function ensureWorkerRegistered() {
  const settingsResponse = await sendRuntimeMessage({ type: "PROGRAM1_GET_SETTINGS" });
  const settings = settingsResponse?.settings || {};
  if (!settings.backend_url || !settings.worker_id) {
    renderRegistryStatus({ ok: false, registered: false, error: null });
    return;
  }
  const registered = await registerCurrentWorker();
  if (registered.ok) {
    await sendRuntimeMessage({ type: "PROGRAM1_HEARTBEAT" });
  }
}

document.getElementById("save").addEventListener("click", async () => {
  const settings = currentSettings();
  const url = settings.backend_url;
  try {
    if (url) {
      const granted = await chrome.permissions.request({ origins: [originPattern(url)] });
      if (!granted) return show("BACKEND_PERMISSION_DENIED");
    }
    const response = await sendRuntimeMessage({
      type: "PROGRAM1_SAVE_SETTINGS",
      settings,
    });
    show(response);
    updateProcess({
      state: response?.ok ? (url ? "READY" : "CONFIG_REQUIRED") : "ERROR",
      step: response?.ok
        ? (url ? "Settings saved; ready to capture" : "Backend URL is empty")
        : "Settings could not be saved",
      captured_count: 0,
      queued_count: 0,
      sent_count: 0,
      accepted_count: 0,
      outbox_count: 0,
      error: response?.ok ? null : response?.error || "SETTINGS_SAVE_FAILED",
    });
    if (response?.ok && url && workerId.value.trim()) {
      const registered = await registerCurrentWorker();
      if (registered.ok) {
        await sendRuntimeMessage({ type: "PROGRAM1_HEARTBEAT" });
      }
    }
  } catch (error) {
    updateProcess({
      state: "ERROR",
      step: "Settings could not be saved",
      error: String(error),
    });
    show({ ok: false, error: String(error) });
  }
});

document.getElementById("flush").addEventListener("click", async () => {
  updateProcess({
    state: "COLLECTING",
    step: "Flushing local outbox",
  });
  const response = await sendRuntimeMessage({ type: "PROGRAM1_FLUSH_OUTBOX" });
  updateProcess({
    state: response?.ok ? "DELIVERED" : "DELIVERY_BLOCKED",
    step: response?.ok ? "Outbox delivered" : "Outbox delivery is blocked",
    sent_count: response?.sent_count || 0,
    accepted_count: response?.accepted_observation_count || 0,
    outbox_count: response?.remaining_count || 0,
    error: response?.error || null,
  });
  show(response);
});

document.getElementById("openTarget").addEventListener("click", async () => {
  const target = normalizedWebUrl(targetUrl.value || DEFAULT_TARGET_URL);
  if (!target.ok) {
    updateProcess({
      state: "PAGE_UNSUPPORTED",
      step: "Target page URL is not valid",
      error: target.error,
    });
    return show(target);
  }
  const tab = await chrome.tabs.create({ url: target.url, active: true });
  activeTargetTabId = tab.id;
  updateProcess({
    state: "READY",
    step: "Target page opened; wait for it to load, then capture",
    error: null,
  });
  show({ ok: true, opened_url: target.url });
});

async function captureTargetOnce(captureTarget) {
  if (!captureTarget.ok) {
    updateProcess({
      state: "PAGE_UNSUPPORTED",
      step: "Open a Shopee web page before capture",
      error: captureTarget.error,
    });
    show(captureTarget);
    return { ok: false, error: captureTarget.error };
  }
  try {
    updateProcess({
      state: "COLLECTING",
      step: "Checking page permission",
    });
    const pagePermission = await ensurePagePermission(captureTarget.url);
    if (!pagePermission.ok) {
      updateProcess({
        state: "ERROR",
        step: "Page permission was not granted",
        error: `PAGE_PERMISSION_DENIED ${pagePermission.origin}`,
      });
      const result = { ok: false, error: "PAGE_PERMISSION_DENIED", origin: pagePermission.origin };
      show(result);
      return result;
    }
    updateProcess({
      state: "COLLECTING",
      step: "Injecting collector into active page",
    });
    await chrome.scripting.executeScript({
      target: { tabId: captureTarget.tabId },
      files: ["src/content.js"],
    });
    updateProcess({
      state: "COLLECTING",
      step: "Reading visible product observations",
    });
    const response = await sendTabMessage(captureTarget.tabId, {
      type: "PROGRAM1_CAPTURE_CURRENT_PAGE",
    });
    if (!response?.ok) {
      const failure = response?.error || "PAGE_UNSUPPORTED";
      const failureState =
        failure === "PAGE_UNSUPPORTED" || failure === "PAGE_BLOCKED_BY_ANTIBOT"
          ? failure
          : "ERROR";
      const failureStep =
        failure === "PAGE_BLOCKED_BY_ANTIBOT"
          ? "Blocked by Shopee verification/anti-bot; not treated as a harvest"
          : failure === "PAGE_UNSUPPORTED"
            ? "Active page is not supported by the current profile"
            : "Collector could not read the active tab";
      const pageUrl = response?.page_url || captureTarget.url;
      updateProcess({
        state: failureState,
        step: `${failureStep}${pageUrl ? ` (${pageUrl})` : ""}`,
        error: failure,
      });
      const result = response || { ok: false, error: "PAGE_UNSUPPORTED" };
      show(result);
      return result;
    }
    const observations = withWorkerId(response.observations, workerId.value);
    const batch = { batch_id: crypto.randomUUID(), observations };
    updateProcess({
      state: "QUEUED",
      step: `Captured ${observations.length} observations; queueing batch`,
      captured_count: observations.length,
    });
    const queueResponse = await sendRuntimeMessage({ type: "PROGRAM1_QUEUE_BATCH", payload: batch });
    const view = processViewFromCapture(response, queueResponse);
    updateProcess(view);
    const result = {
      ...captureStatus(response, queueResponse),
      pagination: response?.pagination || null,
      page_url: response?.page_url || captureTarget.url,
    };
    show(result);
    return result;
  } catch (error) {
    const result = { ok: false, error: String(error) };
    updateProcess({
      state: "ERROR",
      step: "Capture failed before collector response",
      error: String(error),
    });
    show(result);
    return result;
  }
}

async function captureTargetWithRetry(captureTarget) {
  const firstResult = await captureTargetOnce(captureTarget);
  if (
    firstResult?.ok ||
    !["PAGE_UNSUPPORTED"].includes(firstResult?.error || "")
  ) {
    return firstResult;
  }
  updateProcess({
    state: "COLLECTING",
    step: "Page not ready; waiting and retrying once",
    error: null,
    ...currentMachineIndicators(0),
  });
  await sleep(TARGET_CAPTURE_RETRY_WAIT_MS);
  return captureTargetOnce(captureTarget);
}

function humanPageText(pagination) {
  if (!pagination) return "";
  const current = pagination.current_page === null ? "" : `page ${pagination.current_page + 1}`;
  const total = pagination.total_pages === null ? "" : ` of ${pagination.total_pages}`;
  return `${current}${total}`;
}

async function advanceTargetAfterDelivery(result) {
  if (!advanceAfterDelivery.checked || !result?.ok) return;
  const pagination = result?.pagination || null;
  if (pagination && pagination.has_next === false) {
    const where = humanPageText(pagination);
    const message = `Delivered; this listing is complete${where ? ` (${where})` : ""}`;
    if (autoRunning) {
      stopAutoRun(`Auto run finished: reached the last page${where ? ` (${where})` : ""}`);
    } else {
      updateProcess({
        state: "DELIVERED",
        step: message,
        error: null,
        ...currentMachineIndicators(0),
      });
    }
    return;
  }
  const nextTarget =
    pagination?.next_url !== null && pagination?.next_url !== undefined
      ? normalizedWebUrl(pagination.next_url)
      : nextShopeeListingPageUrl(targetUrl.value || DEFAULT_TARGET_URL);
  if (!nextTarget.ok) {
    updateProcess({
      state: "DELIVERED",
      step: `Delivered; target advance skipped: ${nextTarget.error}`,
      error: null,
      ...currentMachineIndicators(0),
    });
    return;
  }
  if (nextTarget.page === undefined) {
    const parsed = Number.parseInt(new URL(nextTarget.url).searchParams.get("page") || "0", 10);
    nextTarget.page = Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
  }
  targetUrl.value = nextTarget.url;
  await sendRuntimeMessage({ type: "PROGRAM1_SAVE_SETTINGS", settings: currentSettings() });
  if (activeTargetTabId !== null) {
    try {
      await chrome.tabs.update(activeTargetTabId, { url: nextTarget.url, active: true });
      await sleep(TARGET_LOAD_WAIT_MS);
    } catch (_error) {
      activeTargetTabId = null;
    }
  }
  const totalText =
    pagination?.total_pages === null || pagination?.total_pages === undefined
      ? ""
      : ` of ${pagination.total_pages}`;
  updateProcess({
    state: "READY",
    step: `Delivered; advanced target to page ${nextTarget.page + 1}${totalText}`,
    error: null,
    ...currentMachineIndicators(0),
  });
}

async function captureActiveTabOnce() {
  return captureTargetOnce(await getActiveWebCaptureTarget());
}

function setAutoControls(running) {
  autoRunning = running;
  startAuto.disabled = running;
  stopAuto.disabled = !running;
}

function stopCountdownTicker() {
  if (autoTickTimerId !== null) {
    clearInterval(autoTickTimerId);
    autoTickTimerId = null;
  }
  autoTimerDeadline = 0;
}

function startCountdownTicker(delayMs) {
  stopCountdownTicker();
  autoTimerDeadline = Date.now() + delayMs;
  const tick = () => {
    if (!autoRunning || autoTimerDeadline <= 0) {
      stopCountdownTicker();
      return;
    }
    const remainingSeconds = Math.max(0, Math.ceil((autoTimerDeadline - Date.now()) / 1000));
    step.textContent = `Next auto cycle in ${remainingSeconds}s`;
    if (remainingSeconds <= 0) stopCountdownTicker();
  };
  tick();
  autoTickTimerId = setInterval(tick, 250);
}

function stopAutoRun(reason = "Auto run stopped") {
  if (autoTimerId !== null) {
    clearTimeout(autoTimerId);
    autoTimerId = null;
  }
  stopCountdownTicker();
  setAutoControls(false);
  updateProcess({
    state: "IDLE",
    step: reason,
    error: null,
  });
}

function scheduleNextAutoCapture() {
  if (!autoRunning) return;
  if (autoTimerId !== null) {
    clearTimeout(autoTimerId);
    autoTimerId = null;
  }
  const range = updateDelayRangeLabel();
  const delayMs = randomDelayMs(range);
  startCountdownTicker(delayMs);
  autoTimerId = setTimeout(runAutoCaptureCycle, delayMs);
}

async function runAutoCaptureCycle() {
  if (!autoRunning || autoInFlight) return;
  autoInFlight = true;
  stopCountdownTicker();
  autoRunCount += 1;
  try {
    updateProcess({
      state: "COLLECTING",
      step: `Auto run cycle ${autoRunCount}: preparing target page`,
      error: null,
    });
    const captureTarget = await getOrOpenTargetTab();
    const result = await captureTargetWithRetry(captureTarget);
    if (!result?.ok) {
      stopAutoRun(`Auto run stopped: ${result?.error || "capture failed"}`);
    } else {
      await advanceTargetAfterDelivery(result);
    }
  } finally {
    autoInFlight = false;
    scheduleNextAutoCapture();
  }
}

function startAutoRun() {
  updateDelayRangeLabel();
  autoRunCount = 0;
  sessionAcceptedTotal = 0;
  sessionStartedAt = Date.now();
  setAutoControls(true);
  runAutoCaptureCycle();
}

document.getElementById("capture").addEventListener("click", async () => {
  await captureActiveTabOnce();
});

startAuto.addEventListener("click", startAutoRun);
stopAuto.addEventListener("click", () => stopAutoRun());
delayMinSeconds.addEventListener("input", () => syncDelayRange("min"));
delayMaxSeconds.addEventListener("input", () => syncDelayRange("max"));
updateDelayRangeLabel();
window.addEventListener("beforeunload", () => stopAutoRun("Auto run stopped because panel closed"));

ensureWorkerRegistered();

if (typeof module !== "undefined") {
  module.exports = {
    captureStatus,
    processViewFromCapture,
    processViewFromStatus,
    captureTargetFromTab,
    ensurePagePermission,
    normalizedDelayRangeMs,
    normalizedWebUrl,
    nextShopeeListingPageUrl,
    originPattern,
    randomDelayMs,
    registerCurrentWorker,
    renderRegistryStatus,
    sendTabMessage,
    sendRuntimeMessage,
    stateClassName,
    withWorkerId,
  };
}
