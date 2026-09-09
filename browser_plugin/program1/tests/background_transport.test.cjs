const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function loadBackground({ fetchImpl, initialStorage = {}, storageGetError = null,
  failReceiptStorage = false, alarmsCreateVoid = false } = {}) {
  const storage = { ...initialStorage };
  const listeners = [];
  const checkpoints = [];
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
            return structuredClone({ [key]: storage[key] });
          },
          async set(values) {
            if (failReceiptStorage && values.program1_last_delivery_receipt_v1) {
              throw new Error("STORAGE_WRITE_FAILED");
            }
            Object.assign(storage, structuredClone(values));
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
      async checkpoint(...args) {
        checkpoints.push(args);
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
  for (const file of ["outbox.js", "delivery_reliability.mjs"]) {
    const actual = fs.readFileSync(path.join(__dirname, "..", "src", file), "utf8")
      .replace(/export /g, "");
    new vm.Script(actual, { filename: file }).runInContext(context);
  }

  const filePath = path.join(__dirname, "..", "src", "background.js");
  const source = fs
    .readFileSync(filePath, "utf8")
    .replace('import { createBackgroundExecutionController } from "./background_execution.mjs";', "")
    .replace('import { createProgram1JobLifecycle } from "./job_lifecycle.mjs";', "")
    .replace('import { drainObservationOutbox, validateObservationBatchAck } from "./delivery_reliability.mjs";', "")
    .replace(/import \{[\s\S]*?\} from "\.\/outbox\.js";/, "");
  new vm.Script(source, { filename: filePath }).runInContext(context);

  async function sendMessage(message) {
    return await new Promise((resolve) => {
      const keepAlive = listeners[0](message, {}, resolve);
      assert.equal(keepAlive, true);
    });
  }

  return { sendMessage, storage, outbox: context, checkpoints };
}

function jsonResponse(body) {
  return {
    ok: true,
    async json() {
      return body;
    },
  };
}

test("duplicate-only v2 ACK drains safely and survives background restart", async () => {
  const receipt = {
    ack_schema_version: "program1-observation-ack-v2",
    batch_id: "duplicate-batch", received_count: 1, accepted_count: 0,
    duplicate_count: 1, accounted_count: 1,
  };
  const harness = loadBackground({
    initialStorage: { program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000" } },
    fetchImpl: async () => jsonResponse(receipt),
  });
  const result = await harness.sendMessage({ type: "PROGRAM1_QUEUE_BATCH",
    payload: { batch_id: "duplicate-batch", observations: [{ observation_id: "old" }] } });
  assert.equal(result.ok, true);
  assert.equal(result.receipt.duplicate_count, 1);
  assert.equal(harness.storage.program1_outbox_v1.length, 0);
  const restarted = loadBackground({ initialStorage: harness.storage });
  const status = await restarted.sendMessage({ type: "PROGRAM1_GET_PROCESS_STATUS" });
  assert.equal(status.last_delivery_receipt.batch_id, "duplicate-batch");
  assert.equal(status.last_delivery_receipt.accepted_count, 0);
});

test("backlog drain checkpoints only current receipt and hides another backend's receipt", async () => {
  const h = loadBackground({
    initialStorage: {
      program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000", worker_id: "w" },
      program1_active_job_v1: { job_id: "job" },
      program1_outbox_v1: [{ message_id: "backlog", payload: { batch_id: "old",
        observations: [{}, {}, {}] } }],
    },
    fetchImpl: async (_url, options) => {
      const payload = JSON.parse(options.body);
      const count = payload.observations.length;
      return jsonResponse({ ack_schema_version: "program1-observation-ack-v2",
        batch_id: payload.batch_id, received_count: count, accepted_count: count,
        duplicate_count: 0, accounted_count: count });
    },
  });
  const result = await h.sendMessage({ type: "PROGRAM1_QUEUE_BATCH",
    payload: { batch_id: "current", observations: [{}] } });
  assert.equal(result.flush.accepted_observation_count, 4);
  assert.equal(result.receipt.accepted_count, 1);
  assert.equal(h.checkpoints[0][2].accepted_count, 1);
  h.storage.program1_worker_settings_v1.backend_url = "http://127.0.0.1:9000";
  const status = await h.sendMessage({ type: "PROGRAM1_GET_PROCESS_STATUS" });
  assert.equal(status.last_delivery_receipt, null);
});

test("receipt storage failure retains outbox and cannot claim delivery", async () => {
  const h = loadBackground({ failReceiptStorage: true,
    initialStorage: { program1_worker_settings_v1: { backend_url: "http://127.0.0.1:8000" } },
    fetchImpl: async () => jsonResponse({ batch_id: "b", received_count: 1, accepted_count: 1 }),
  });
  const result = await h.sendMessage({ type: "PROGRAM1_QUEUE_BATCH",
    payload: { batch_id: "b", observations: [{}] } });
  assert.equal(result.ok, false);
  assert.equal(result.flush.sent_count, 0);
  assert.equal(h.storage.program1_outbox_v1.length, 1);
  assert.equal(h.storage.program1_last_delivery_receipt_v1, undefined);
});

test("concurrent outbox mutations preserve new messages and quarantine evidence", async () => {
  const h = loadBackground({ initialStorage: {
    program1_outbox_v1: [{ message_id: "old" }, { message_id: "poison" }],
  } });
  await Promise.all([
    h.outbox.enqueue({ message_id: "new-1" }),
    h.outbox.removeByMessageId("old", { batch_id: "old", accepted_count: 1 }),
    h.outbox.enqueue({ message_id: "new-2" }),
    h.outbox.quarantineByMessageId("poison", { error: "HTTP_422" }),
  ]);
  assert.deepEqual(h.storage.program1_outbox_v1.map(item => item.message_id), ["new-1", "new-2"]);
  assert.equal(h.storage.program1_outbox_quarantine_v1[0].message_id, "poison");
  assert.equal(h.storage.program1_last_delivery_receipt_v1.batch_id, "old");
});

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
  assert.equal(storage.program1_outbox_v1.length, 0);
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
    last_delivery_receipt: null,
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
