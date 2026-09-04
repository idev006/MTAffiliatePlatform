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
  };
  vm.createContext(context);

  const filePath = path.join(__dirname, "..", "src", "background.js");
  const source = fs
    .readFileSync(filePath, "utf8")
    .replace('import { enqueue, readOutbox, removeByMessageId } from "./outbox.js";', "");
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
    state: "IDLE",
    registry: {
      registered: false,
      worker_id: "",
      last_error: null,
      last_seen_at: null,
    },
  });
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
    "collector:shopee-current-page-lab-v2",
    "collector:fixture-profile-v1",
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
