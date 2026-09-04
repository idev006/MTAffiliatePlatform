import { enqueue, readOutbox, removeByMessageId } from "./outbox.js";

const SETTINGS_KEY = "program1_worker_settings_v1";
const INSTALLATION_KEY = "program1_installation_id_v1";
const RUN_STATE_KEY = "program1_run_state_v1";
const HEARTBEAT_ALARM = "program1-heartbeat";
const HEARTBEAT_PERIOD_MINUTES = 1;
const WORKER_TYPE = "DISCOVERY_BROWSER_WORKER";
const EXTENSION_CAPABILITIES = [
  "collector:shopee-current-page-lab-v2",
  "collector:fixture-profile-v1",
  "mode:capture-current-page",
];
let outboxDrain = Promise.resolve();
let registryState = {
  registered: false,
  worker_id: "",
  last_error: null,
  last_seen_at: null,
};

if (chrome.sidePanel?.setPanelBehavior) {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {
    // Some Chromium-family browsers expose partial sidePanel support.
  });
}

async function getSettings() {
  const result = await chrome.storage.local.get(SETTINGS_KEY);
  return result[SETTINGS_KEY] || { backend_url: "", worker_id: "" };
}

async function getRunState() {
  const result = await chrome.storage.local.get(RUN_STATE_KEY);
  return result[RUN_STATE_KEY] || {
    desired: false,
    active_target_tab_id: null,
    cycle_count: 0,
    session_accepted_count: 0,
    session_started_at: null,
    last_step: "Auto run is not active",
    last_error: null,
    updated_at: null,
  };
}

async function saveRunState(runState) {
  const current = await getRunState();
  const next = {
    ...current,
    ...runState,
    updated_at: new Date().toISOString(),
  };
  await chrome.storage.local.set({ [RUN_STATE_KEY]: next });
  return next;
}

async function postJson(path, payload) {
  const settings = await getSettings();
  if (!settings.backend_url) {
    throw new Error("BACKEND_URL_NOT_CONFIGURED");
  }
  const response = await fetch(`${settings.backend_url.replace(/\/$/, "")}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP_${response.status}`);
  return response.json();
}

function validateObservationBatchAck(payload, ack) {
  const observationCount = payload?.observations?.length || 0;
  if (ack?.batch_id !== payload?.batch_id) {
    throw new Error("ACK_BATCH_ID_MISMATCH");
  }
  if (ack?.received_count !== observationCount) {
    throw new Error("ACK_RECEIVED_COUNT_MISMATCH");
  }
  if (ack?.accepted_count !== observationCount) {
    throw new Error("ACK_ACCEPTED_COUNT_MISMATCH");
  }
}

async function drainOutboxOnce() {
  let attemptedCount = 0;
  let sentCount = 0;
  let acceptedObservationCount = 0;
  let error = null;

  for (const message of await readOutbox()) {
    attemptedCount += 1;
    try {
      const ack = await postJson("/api/v1/program1/observations", message.payload);
      validateObservationBatchAck(message.payload, ack);
      await removeByMessageId(message.message_id);
      sentCount += 1;
      acceptedObservationCount += ack.accepted_count;
    } catch (_error) {
      error = _error instanceof Error ? _error.message : String(_error);
      break;
    }
  }

  return {
    ok: error === null,
    attempted_count: attemptedCount,
    sent_count: sentCount,
    accepted_observation_count: acceptedObservationCount,
    remaining_count: (await readOutbox()).length,
    error,
  };
}

function flushOutbox() {
  outboxDrain = outboxDrain.then(drainOutboxOnce, drainOutboxOnce);
  return outboxDrain;
}

function errorMessage(error) {
  return error && typeof error.message === "string" ? error.message : String(error);
}

function respondAsync(operation, sendResponse) {
  Promise.resolve()
    .then(operation)
    .then(sendResponse, (error) => sendResponse({ ok: false, error: errorMessage(error) }));
  return true;
}

async function getOrCreateInstallationId() {
  const result = await chrome.storage.local.get(INSTALLATION_KEY);
  if (result[INSTALLATION_KEY]) return result[INSTALLATION_KEY];
  const installationId = crypto.randomUUID();
  await chrome.storage.local.set({ [INSTALLATION_KEY]: installationId });
  return installationId;
}

function scheduleHeartbeatAlarm() {
  if (typeof chrome.alarms === "undefined") return;
  try {
    const result = chrome.alarms.create(HEARTBEAT_ALARM, {
      periodInMinutes: HEARTBEAT_PERIOD_MINUTES,
    });
    // Chromium-family browsers return void here; promise-based wrappers (e.g.
    // Firefox-style shims) may return a promise. Handle both without crashing
    // the service worker, which would surface as a closed message port.
    if (result && typeof result.catch === "function") {
      result.catch(() => {
        // Alarms are best-effort background scheduling; side panel messages also
        // trigger registration/heartbeats when the panel is open.
      });
    }
  } catch (_error) {
    // Best-effort only.
  }
}

function extensionVersion() {
  return chrome.runtime?.getManifest?.()?.version || "unknown";
}

async function registerWorker() {
  const settings = await getSettings();
  if (!settings.worker_id) {
    registryState = {
      registered: false,
      worker_id: "",
      last_error: "WORKER_ID_NOT_CONFIGURED",
      last_seen_at: null,
    };
    return { ok: false, registered: false, error: registryState.last_error };
  }
  if (!settings.backend_url) {
    registryState = {
      registered: false,
      worker_id: settings.worker_id,
      last_error: "BACKEND_URL_NOT_CONFIGURED",
      last_seen_at: null,
    };
    return { ok: false, registered: false, error: registryState.last_error };
  }
  const installationId = await getOrCreateInstallationId();
  const payload = {
    schema_version: "worker-registration-v1",
    worker_id: settings.worker_id,
    worker_type: WORKER_TYPE,
    installation_id: installationId,
    version: extensionVersion(),
    capabilities: EXTENSION_CAPABILITIES,
  };
  try {
    const record = await postJson("/api/v1/workers/register", payload);
    registryState = {
      registered: true,
      worker_id: record.worker_id,
      last_error: null,
      last_seen_at: record.last_seen_at || null,
    };
    scheduleHeartbeatAlarm();
    return { ok: true, registered: true, worker_id: record.worker_id, record };
  } catch (error) {
    const message = errorMessage(error);
    registryState = {
      registered: false,
      worker_id: settings.worker_id,
      last_error: message,
      last_seen_at: null,
    };
    return { ok: false, registered: false, error: message };
  }
}

async function heartbeatNow() {
  const settings = await getSettings();
  if (!settings.backend_url || !settings.worker_id) {
    const error = settings.backend_url
      ? "WORKER_ID_NOT_CONFIGURED"
      : "BACKEND_URL_NOT_CONFIGURED";
    registryState = { ...registryState, last_error: error };
    return { ok: false, registered: false, error };
  }
  if (!registryState.registered) {
    const registration = await registerWorker();
    if (!registration.ok) return registration;
  }
  const remaining = (await readOutbox()).length;
  const healthState = remaining > 0 ? "DEGRADED" : "ONLINE_IDLE";
  try {
    const path = `/api/v1/workers/${encodeURIComponent(settings.worker_id)}/heartbeat`;
    const record = await postJson(path, {
      schema_version: "worker-heartbeat-v1",
      health_state: healthState,
    });
    registryState = {
      registered: true,
      worker_id: record.worker_id,
      last_error: null,
      last_seen_at: record.last_seen_at || null,
    };
    return {
      ok: true,
      registered: true,
      worker_id: record.worker_id,
      health_state: healthState,
      last_seen_at: registryState.last_seen_at,
    };
  } catch (error) {
    const message = errorMessage(error);
    registryState = { ...registryState, last_error: message };
    return { ok: false, registered: false, error: message };
  }
}

if (typeof chrome.alarms !== "undefined") {
  chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === HEARTBEAT_ALARM) {
      heartbeatNow().catch(() => {
        // Heartbeat failures are surfaced through registryState on status reads.
      });
    }
  });
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "PROGRAM1_SAVE_SETTINGS") {
    return respondAsync(async () => {
      await chrome.storage.local.set({ [SETTINGS_KEY]: message.settings });
      return { ok: true };
    }, sendResponse);
  }
  if (message.type === "PROGRAM1_GET_SETTINGS") {
    return respondAsync(async () => ({ ok: true, settings: await getSettings() }), sendResponse);
  }
  if (message.type === "PROGRAM1_GET_PROCESS_STATUS") {
    return respondAsync(async () => {
      const [settings, outbox, runState] = await Promise.all([
        getSettings(),
        readOutbox(),
        getRunState(),
      ]);
      return {
        ok: true,
        backend_configured: Boolean(settings.backend_url),
        worker_configured: Boolean(settings.worker_id),
        outbox_remaining_count: outbox.length,
        state: runState.desired ? "RECOVERABLE" : settings.backend_url ? "IDLE" : "CONFIG_REQUIRED",
        registry: { ...registryState },
        run_state: runState,
      };
    }, sendResponse);
  }
  if (message.type === "PROGRAM1_GET_RUN_STATE") {
    return respondAsync(async () => ({ ok: true, run_state: await getRunState() }), sendResponse);
  }
  if (message.type === "PROGRAM1_SAVE_RUN_STATE") {
    return respondAsync(async () => ({
      ok: true,
      run_state: await saveRunState(message.run_state || {}),
    }), sendResponse);
  }
  if (message.type === "PROGRAM1_QUEUE_BATCH") {
    return respondAsync(async () => {
      const envelope = {
        message_id: crypto.randomUUID(),
        created_at: new Date().toISOString(),
        payload: message.payload,
      };
      await enqueue(envelope);
      const flush = await flushOutbox();
      return {
        ok: flush.ok,
        queued: true,
        queued_message_id: envelope.message_id,
        queued_observation_count: message.payload?.observations?.length || 0,
        flush,
      };
    }, sendResponse);
  }
  if (message.type === "PROGRAM1_FLUSH_OUTBOX") {
    return respondAsync(flushOutbox, sendResponse);
  }
  if (message.type === "PROGRAM1_REGISTER_WORKER") {
    return respondAsync(registerWorker, sendResponse);
  }
  if (message.type === "PROGRAM1_HEARTBEAT") {
    return respondAsync(heartbeatNow, sendResponse);
  }
  return false;
});

chrome.runtime.onStartup.addListener(async () => {
  flushOutbox().catch(() => {});
  scheduleHeartbeatAlarm();
  const settings = await getSettings();
  if (settings.backend_url && settings.worker_id) {
    registerWorker().catch(() => {});
  }
});
