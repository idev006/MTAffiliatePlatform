const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function loadBackground({ fetchImpl, initialStorage = {}, storageGetError = null, alarmsCreateVoid = false } = {}) {
  const storage = { ...initialStorage };
  const listeners = [];
  const context = {
    chrome: {
      runtime: {
        onMessage: {
          addListener(listener) {
            listeners.push(listener);
          },
        },
        onStartup: {
          addListener() {},
        },
        getManifest() {
          return { version: "0.1.9-test" };
        },
      },
      sidePanel: {
        setPanelBehavior() {
          return Promise.resolve();
        },
      },
      alarms: {
        create() {
          if (alarmsCreateVoid) return undefined;
          return Promise.resolve();
        },
        onAlarm: {
          addListener() {},
        },
      },
      storage: {
        local: {
          async get(key) {
            if (storageGetError) throw storageGetError;
            return { [key]: storage[key] };
          },
          async set(values) {
            Object.assign(storage, values);
          },
          async remove(key) {
            delete storage[key];
          },
        },
      },
    },
    crypto: {
      randomUUID() {
        return "message-1";
      },
    },
    fetch: fetchImpl,
    console,
    enqueue: async (message) => {
      const items = Array.isArray(storage.program1_outbox_v1)
        ? storage.program1_outbox_v1
        : [];
      storage.program1_outbox_v1 = [...items, message];
    },
    readOutbox: async () => storage.program1_outbox_v1 || [],
    removeByMessageId: async (messageId) => {
      storage.program1_outbox_v1 = (storage.program1_outbox_v1 || []).filter(
        (message) => message.message_id !== messageId,
      );
    },
    readQuarantine: async () => storage.program1_outbox_quarantine_v1 || [],
    quarantineByMessageId: async (messageId, reason) => {
      const items = storage.program1_outbox_v1 || [];
      const message = items.find((item) => item.message_id === messageId);
      if (!message) return false;
      storage.program1_outbox_v1 = items.filter((item) => item.message_id !== messageId);
      storage.program1_outbox_quarantine_v1 = [
        ...(storage.program1_outbox_quarantine_v1 || []),
        { ...message, quarantine_reason: reason, quarantined_at: "2026-09-05T00:00:00Z" },
      ];
      return true;
    },
    drainObservationOutbox: async ({ messages, deliver, validateAck, remove, quarantine }) => {
      let attemptedCount = 0;
      let sentCount = 0;
      let acceptedObservationCount = 0;
      const sentMessageIds = [];
      const quarantinedMessageIds = [];
      let lastFailure = null;
      let blockingFailure = null;
      for (const message of messages) {
        attemptedCount += 1;
        try {
          const ack = await deliver(message);
          validateAck(message.payload, ack);
          await remove(message.message_id);
          sentCount += 1;
          sentMessageIds.push(message.message_id);
          acceptedObservationCount += ack.accepted_count;
        } catch (error) {
          const detail = error && typeof error.message === "string" ? error.message : String(error);
          const permanent = ["HTTP_400", "HTTP_409", "HTTP_413", "HTTP_415", "HTTP_422"].includes(detail);
          lastFailure = {
            category: permanent ? "PERMANENT_PAYLOAD" : detail.startsWith("ACK_")
              ? "AMBIGUOUS_RECONCILE"
              : "TRANSIENT_OR_BLOCKED",
            message: detail,
            message_id: message.message_id,
          };
          if (permanent) {
            await quarantine(message.message_id, {
              category: lastFailure.category,
              error: detail,
            });
            quarantinedMessageIds.push(message.message_id);
            continue;
          }
          blockingFailure = lastFailure;
          break;
        }
      }
      return {
        ok: blockingFailure === null,
        attempted_count: attemptedCount,
        sent_count: sentCount,
        sent_message_ids: sentMessageIds,
        quarantined_count: quarantinedMessageIds.length,
        quarantined_message_ids: quarantinedMessageIds,
        accepted_observation_count: acceptedObservationCount,
        last_failure: lastFailure,
        blocking_failure: blockingFailure,
      };
    },
    createBackgroundExecutionController: () => ({
      async start() {
        return { ok: true, run_state: storage.program1_run_state_v1 || null };
      },
      async stop() {
        return { desired: false };
      },
      async runOneCycle() {
        return { ok: true, skipped: true };
      },
      async resumeAfterWake() {
        return { ok: true, skipped: true };
      },
    }),
    createProgram1JobLifecycle: () => ({
      async activeState() {
        return storage.program1_active_job_v1 || null;
      },
      async leaseAndStart() {
        return { ok: true, leased: false, reason: "NO_COMPATIBLE_JOB", active_job: null };
      },
      async renew() {
        return { ok: true, renewed: false, reason: "NO_ACTIVE_JOB", active_job: null };
      },
      async checkpoint() {
        return { ok: true, active_job: storage.program1_active_job_v1 || null };
      },
      async verifyAndComplete() {
        delete storage.program1_active_job_v1;
        return { ok: true, active_job: null };
      },
      async reconcile() {
        return { ok: true, reconciled: false, reason: "NO_ACTIVE_JOB", active_job: null };
      },
    }),
  };
  vm.createContext(context);

  const filePath = path.join(__dirname, "..", "src", "background.js");
  const source = fs
    .readFileSync(filePath, "utf8")
    .replace('import { createBackgroundExecutionController } from "./background_execution.mjs";', "")
    .replace('import { createProgram1JobLifecycle } from "./job_lifecycle.mjs";', "")
    .replace('import { drainObservationOutbox } from "./delivery_reliability.mjs";', "")
    .replace(/import \{[\s\S]*?\} from "\.\/outbox\.js";/, "");
  new vm.Script(source, { filename: filePath }).runInContext(context);

  async function sendMessage(message) {
    return await new Promise((resolve) => {
      const keepAlive = listeners[0](message, {}, resolve);
      assert.equal(keepAlive, true);
    });
  }

  return { sendMessage, storage };
}

function jsonResponse(body) {
  return {
    ok: true,
    async json() {
      return body;
    },
  };
}

test("queue batch reports backend configuration failure and keeps durable outbox item", async () => {
  const { sendMessage, storage } = loadBackground();

  const response = await sendMessage({
    type: "PROGRAM1_QUEUE_BATCH",
    payload: { batch_id: "batch-1", observations: [{ observation_id: "obs-1" }] },
  });

  assert.equal(response.ok, false);
  assert.equal(response.queued, true);
  assert.equal(response.queued_observation_count, 1);
  assert.equal(response.flush.sent_count, 0);
  assert.equal(response.flush.accepted_observation_count, 0);
  assert.equal(response.flush.remaining_count, 1);
  assert.equal(response.flush.error, "BACKEND_URL_NOT_CONFIGURED");
  assert.equal(storage.program1_outbox_v1.length, 1);
});

test("queue batch reports sent counts after backend acknowledgement and clears outbox", async () => {
  const { sendMessage, storage } = loadBackground({
    initialStorage: {
      program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000", worker_id: "worker-01" },
    },
    fetchImpl: async () =>
      jsonResponse({ batch_id: "batch-1", received_count: 1, accepted_count: 1 }),
  });

  const response = await sendMessage({
    type: "PROGRAM1_QUEUE_BATCH",
    payload: { batch_id: "batch-1", observations: [{ observation_id: "obs-1" }] },
  });

  assert.equal(response.ok, true);
  assert.equal(response.queued, true);
  assert.equal(response.flush.sent_count, 1);
  assert.equal(response.flush.accepted_observation_count, 1);
  assert.equal(response.flush.remaining_count, 0);
  assert.equal(response.flush.error, null);
  assert.deepEqual(storage.program1_outbox_v1, []);
});

test("queue batch keeps outbox item when backend ack does not match payload", async () => {
  const { sendMessage, storage } = loadBackground({
    initialStorage: {
      program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000", worker_id: "worker-01" },
    },
    fetchImpl: async () =>
      jsonResponse({ batch_id: "different-batch", received_count: 1, accepted_count: 1 }),
  });

  const response = await sendMessage({
    type: "PROGRAM1_QUEUE_BATCH",
    payload: { batch_id: "batch-1", observations: [{ observation_id: "obs-1" }] },
  });

  assert.equal(response.ok, false);
  assert.equal(response.flush.error, "ACK_BATCH_ID_MISMATCH");
  assert.equal(response.flush.remaining_count, 1);
  assert.equal(storage.program1_outbox_v1.length, 1);
});

test("process status reports configuration, outbox and registry state", async () => {
  const { sendMessage } = loadBackground({
    initialStorage: {
      program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000", worker_id: "worker-01" },
      program1_outbox_v1: [{ message_id: "queued-1" }],
    },
  });

  const response = await sendMessage({ type: "PROGRAM1_GET_PROCESS_STATUS" });

  assert.deepEqual(JSON.parse(JSON.stringify(response)), {
    ok: true,
    backend_configured: true,
    worker_configured: true,
    outbox_remaining_count: 1,
    outbox_quarantine_count: 0,
    state: "IDLE",
    registry: {
      registered: false,
      worker_id: "",
      last_error: null,
      last_seen_at: null,
    },
    run_state: {
      desired: false,
      active_target_tab_id: null,
      cycle_count: 0,
      session_accepted_count: 0,
      session_started_at: null,
      last_step: "Auto run is not active",
      last_error: null,
      updated_at: null,
    },
    active_job: null,
  });
});

test("process status reports durable quarantine requiring operator attention", async () => {
  const { sendMessage } = loadBackground({
    initialStorage: {
      program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000", worker_id: "worker-01" },
      program1_outbox_quarantine_v1: [{ message_id: "poison-1" }],
    },
  });

  const response = await sendMessage({ type: "PROGRAM1_GET_PROCESS_STATUS" });
  assert.equal(response.outbox_remaining_count, 0);
  assert.equal(response.outbox_quarantine_count, 1);
});

test("run state is durable and makes process status recoverable", async () => {
  const { sendMessage, storage } = loadBackground({
    initialStorage: {
      program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000", worker_id: "worker-01" },
    },
  });

  const saved = await sendMessage({
    type: "PROGRAM1_SAVE_RUN_STATE",
    run_state: {
      desired: true,
      active_target_tab_id: 42,
      cycle_count: 7,
      session_accepted_count: 120,
      session_started_at: 1800000000000,
      last_step: "Next auto cycle scheduled in 30s",
      last_error: null,
    },
  });

  assert.equal(saved.ok, true);
  assert.equal(saved.run_state.desired, true);
  assert.equal(saved.run_state.active_target_tab_id, 42);
  assert.equal(saved.run_state.updated_at.length > 0, true);
  assert.equal(storage.program1_run_state_v1.cycle_count, 7);

  const status = await sendMessage({ type: "PROGRAM1_GET_PROCESS_STATUS" });
  assert.equal(status.state, "RECOVERABLE");
  assert.equal(status.run_state.desired, true);
  assert.equal(status.run_state.session_accepted_count, 120);
});

test("background rejection still settles the runtime message response", async () => {
  const { sendMessage } = loadBackground({
    storageGetError: new Error("STORAGE_READ_FAILED"),
  });

  const response = await sendMessage({ type: "PROGRAM1_GET_SETTINGS" });

  assert.deepEqual(JSON.parse(JSON.stringify(response)), {
    ok: false,
    error: "STORAGE_READ_FAILED",
  });
});

test("register worker posts discovery payload and marks worker registered", async () => {
  const calls = [];
  const { sendMessage } = loadBackground({
    initialStorage: {
      program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000/", worker_id: "worker-01" },
    },
    fetchImpl: async (url, options) => {
      calls.push({ url, body: JSON.parse(options.body) });
      return jsonResponse({
        worker_id: "worker-01",
        worker_type: "DISCOVERY_BROWSER_WORKER",
        health_state: "ONLINE_IDLE",
        last_seen_at: "2026-09-04T00:00:00Z",
        version_no: 1,
      });
    },
  });

  const response = await sendMessage({ type: "PROGRAM1_REGISTER_WORKER" });

  assert.equal(response.ok, true);
  assert.equal(response.registered, true);
  assert.equal(response.worker_id, "worker-01");
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "http://127.0.0.1:8000/api/v1/workers/register");
  assert.equal(calls[0].body.schema_version, "worker-registration-v1");
  assert.equal(calls[0].body.worker_id, "worker-01");
  assert.equal(calls[0].body.worker_type, "DISCOVERY_BROWSER_WORKER");
  assert.equal(calls[0].body.installation_id, "message-1");
  assert.equal(calls[0].body.version, "0.1.9-test");
  assert.deepEqual(calls[0].body.capabilities, [
    "collector:profile-router-v1",
    "collector:fixture-profile-v1",
    "collector:shopee-search-lab-v1",
    "collector:shopee-category-lab-v1",
    "collector:shopee-shop-lab-v1",
    "collector:shopee-pdp-lab-v1",
    "mode:capture-current-page",
  ]);

  const status = await sendMessage({ type: "PROGRAM1_GET_PROCESS_STATUS" });
  assert.equal(status.registry.registered, true);
  assert.equal(status.registry.worker_id, "worker-01");
  assert.equal(status.registry.last_error, null);
  assert.equal(status.registry.last_seen_at, "2026-09-04T00:00:00Z");
});

test("register worker survives Chromium-style void alarms.create", async () => {
  const { sendMessage } = loadBackground({
    initialStorage: {
      program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000", worker_id: "worker-01" },
    },
    alarmsCreateVoid: true,
    fetchImpl: async () =>
      jsonResponse({
        worker_id: "worker-01",
        worker_type: "DISCOVERY_BROWSER_WORKER",
        health_state: "ONLINE_IDLE",
        last_seen_at: "2026-09-04T00:00:00Z",
        version_no: 1,
      }),
  });

  const response = await sendMessage({ type: "PROGRAM1_REGISTER_WORKER" });
  assert.equal(response.ok, true);
  assert.equal(response.registered, true);
  assert.equal(response.worker_id, "worker-01");

  const status = await sendMessage({ type: "PROGRAM1_GET_PROCESS_STATUS" });
  assert.equal(status.registry.registered, true);
  assert.equal(status.registry.last_error, null);
});

test("register worker conflict surfaces a visible error and stays unregistered", async () => {
  const { sendMessage } = loadBackground({
    initialStorage: {
      program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000", worker_id: "worker-01" },
    },
    fetchImpl: async () => ({ ok: false, status: 409 }),
  });

  const response = await sendMessage({ type: "PROGRAM1_REGISTER_WORKER" });
  assert.equal(response.ok, false);
  assert.equal(response.registered, false);
  assert.equal(response.error, "HTTP_409");

  const status = await sendMessage({ type: "PROGRAM1_GET_PROCESS_STATUS" });
  assert.equal(status.registry.registered, false);
  assert.equal(status.registry.last_error, "HTTP_409");
});

test("register without worker id fails closed with configuration error", async () => {
  const { sendMessage } = loadBackground({
    initialStorage: {
      program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000", worker_id: "" },
    },
  });

  const response = await sendMessage({ type: "PROGRAM1_REGISTER_WORKER" });
  assert.equal(response.ok, false);
  assert.equal(response.error, "WORKER_ID_NOT_CONFIGURED");
});

test("heartbeat self-heals registration then reports online idle", async () => {
  const calls = [];
  const { sendMessage } = loadBackground({
    initialStorage: {
      program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000", worker_id: "worker-01" },
    },
    fetchImpl: async (url, options) => {
      calls.push({ url, body: JSON.parse(options.body) });
      if (calls.length === 1) {
        return jsonResponse({
          worker_id: "worker-01",
          worker_type: "DISCOVERY_BROWSER_WORKER",
          health_state: "ONLINE_IDLE",
          last_seen_at: "2026-09-04T00:00:00Z",
          version_no: 1,
        });
      }
      return jsonResponse({
        worker_id: "worker-01",
        worker_type: "DISCOVERY_BROWSER_WORKER",
        health_state: "ONLINE_IDLE",
        last_seen_at: "2026-09-04T00:00:30Z",
        version_no: 2,
      });
    },
  });

  const response = await sendMessage({ type: "PROGRAM1_HEARTBEAT" });

  assert.equal(response.ok, true);
  assert.equal(response.registered, true);
  assert.equal(response.worker_id, "worker-01");
  assert.equal(response.health_state, "ONLINE_IDLE");
  assert.equal(response.last_seen_at, "2026-09-04T00:00:30Z");
  assert.equal(calls.length, 2);
  assert.equal(calls[0].url, "http://127.0.0.1:8000/api/v1/workers/register");
  assert.equal(calls[1].url, "http://127.0.0.1:8000/api/v1/workers/worker-01/heartbeat");
  assert.equal(calls[1].body.schema_version, "worker-heartbeat-v1");
  assert.equal(calls[1].body.health_state, "ONLINE_IDLE");
});

test("heartbeat reports degraded while the local outbox retains undelivered work", async () => {
  const calls = [];
  const { sendMessage } = loadBackground({
    initialStorage: {
      program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000", worker_id: "worker-01" },
      program1_outbox_v1: [{ message_id: "undelivered-1" }],
    },
    fetchImpl: async (url, options) => {
      calls.push({ url, body: JSON.parse(options.body) });
      return jsonResponse({
        worker_id: "worker-01",
        worker_type: "DISCOVERY_BROWSER_WORKER",
        health_state: calls.length === 1 ? "ONLINE_IDLE" : "DEGRADED",
        last_seen_at: "2026-09-04T00:00:00Z",
        version_no: calls.length,
      });
    },
  });

  const response = await sendMessage({ type: "PROGRAM1_HEARTBEAT" });

  assert.equal(response.ok, true);
  assert.equal(response.health_state, "DEGRADED");
  assert.equal(calls.length, 2);
  assert.equal(calls[1].body.health_state, "DEGRADED");
});

test("heartbeat without backend configuration fails closed", async () => {
  const { sendMessage } = loadBackground();

  const response = await sendMessage({ type: "PROGRAM1_HEARTBEAT" });
  assert.equal(response.ok, false);
  assert.equal(response.registered, false);
  assert.equal(response.error, "BACKEND_URL_NOT_CONFIGURED");
});
