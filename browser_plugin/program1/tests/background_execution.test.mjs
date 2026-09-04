import assert from "node:assert/strict";
import test from "node:test";

import { createBackgroundExecutionController } from "../src/background_execution.mjs";

function buildHarness({
  activeJob = null,
  leasedJob = null,
  captureResult = null,
  deliveryResult = null,
  settings = {},
  tab = null,
} = {}) {
  let runState = {
    desired: false,
    active_target_tab_id: null,
    cycle_count: 0,
    session_accepted_count: 0,
    ...settings.run_state,
  };
  let active = activeJob;
  const wakes = [];
  const calls = [];
  const lifecycle = {
    async activeState() {
      return active;
    },
    async leaseAndStart(workerId) {
      calls.push(["leaseAndStart", workerId]);
      if (!leasedJob) {
        return { ok: true, leased: false, reason: "NO_COMPATIBLE_JOB", active_job: null };
      }
      active = leasedJob;
      return { ok: true, leased: true, active_job: active };
    },
    async reconcile(workerId) {
      calls.push(["reconcile", workerId]);
      if (!active) {
        return { ok: true, reconciled: false, reason: "NO_ACTIVE_JOB", active_job: null };
      }
      return { ok: true, renewed: true, active_job: active };
    },
    async checkpoint(workerId, checkpointType, payload) {
      calls.push(["checkpoint", workerId, checkpointType, payload]);
      return { ok: true, active_job: active };
    },
    async verifyAndComplete(workerId) {
      calls.push(["verifyAndComplete", workerId]);
      const completed = { ...(active || leasedJob), state: "COMPLETED" };
      active = null;
      return { ok: true, completed_job: completed, active_job: null };
    },
  };

  const resolvedSettings = {
    backend_url: "http://127.0.0.1:8000",
    worker_id: "worker-1",
    target_url: "https://example.invalid/list?page=0",
    page_load_wait_seconds: 4,
    page_retry_wait_seconds: 5,
    max_page_retries: 2,
    delay_min_seconds: 30,
    delay_max_seconds: 30,
    ...settings,
  };

  const controller = createBackgroundExecutionController({
    lifecycle,
    getSettings: async () => resolvedSettings,
    loadRunState: async () => runState,
    saveRunState: async (next) => {
      runState = next;
    },
    ensurePermission: async (url) => {
      calls.push(["permission", url]);
      return true;
    },
    getTab: async (tabId) => {
      calls.push(["getTab", tabId]);
      return tab || {
        id: tabId,
        url: runState.current_target_url,
        status: "complete",
      };
    },
    createTab: async (url) => {
      calls.push(["createTab", url]);
      return { id: 77, url, status: "loading" };
    },
    focusTab: async (tabId) => {
      calls.push(["focusTab", tabId]);
      return { id: tabId };
    },
    navigateTab: async (tabId, url) => {
      calls.push(["navigateTab", tabId, url]);
      return { id: tabId, url, status: "loading" };
    },
    injectCollector: async (tabId) => {
      calls.push(["injectCollector", tabId]);
    },
    captureTab: async (tabId) => {
      calls.push(["captureTab", tabId]);
      return (
        captureResult || {
          ok: true,
          observations: [{ observation_id: "obs-1" }],
          page_url: runState.current_target_url,
          pagination: {
            current_page: 0,
            total_pages: 2,
            has_next: true,
            next_url: "https://example.invalid/list?page=1",
          },
        }
      );
    },
    deliverBatch: async (payload) => {
      calls.push(["deliverBatch", payload]);
      return (
        deliveryResult || {
          ok: true,
          flush: {
            accepted_observation_count: payload.observations.length,
            remaining_count: 0,
          },
        }
      );
    },
    scheduleWake: async (when) => {
      calls.push(["scheduleWake", when]);
      wakes.push(when);
    },
    cancelWake: async () => {
      calls.push(["cancelWake"]);
      return true;
    },
    randomDelayMs: (minMs) => minMs,
    randomUUID: () => "batch-1",
    now: () => 1_800_000_000_000,
  });

  return {
    controller,
    calls,
    wakes,
    getRunState: () => runState,
    setRunState: (next) => {
      runState = next;
    },
    getActive: () => active,
  };
}

const workPackage = {
  hypothesis: { hypothesis_id: "hyp-1" },
  signals: [{ signal_id: "demand" }],
  discovery_plan: {
    plan_id: "plan-1",
    collection_targets: ["https://example.invalid/list?page=0"],
  },
};
const activeJob = {
  job_id: "job-1",
  state: "IN_PROGRESS",
  lease_token: "lease-1",
  work_package: workPackage,
};

test("start leases work and schedules immediate background wake", async () => {
  const h = buildHarness({ leasedJob: activeJob });

  const result = await h.controller.start();

  assert.equal(result.ok, true);
  assert.equal(result.active_job.job_id, "job-1");
  assert.equal(h.getRunState().desired, true);
  assert.equal(h.getRunState().current_target_url, "https://example.invalid/list?page=0");
  assert.deepEqual(h.wakes, [1_800_000_000_000]);
});

test("first cycle creates target tab and exits after durable page-load scheduling", async () => {
  const h = buildHarness({ activeJob });
  h.setRunState({
    desired: true,
    current_target_url: "https://example.invalid/list?page=0",
    cycle_count: 0,
    session_accepted_count: 0,
  });

  const result = await h.controller.runOneCycle();

  assert.equal(result.ok, true);
  assert.equal(result.waiting, true);
  assert.equal(h.getRunState().active_target_tab_id, 77);
  assert.equal(h.getRunState().in_flight, false);
  assert.equal(h.wakes[0], 1_800_000_004_000);
});

test("loaded cycle captures, delivers, checkpoints and advances using alarm", async () => {
  const h = buildHarness({
    activeJob,
    tab: {
      id: 77,
      url: "https://example.invalid/list?page=0",
      status: "complete",
    },
  });
  h.setRunState({
    desired: true,
    active_target_tab_id: 77,
    current_target_url: "https://example.invalid/list?page=0",
    cycle_count: 0,
    session_accepted_count: 0,
  });

  const result = await h.controller.runOneCycle();

  assert.equal(result.ok, true);
  assert.equal(result.completed, false);
  assert.equal(h.getRunState().current_target_url, "https://example.invalid/list?page=1");
  assert.equal(h.getRunState().session_accepted_count, 1);
  assert.equal(h.wakes.at(-1), 1_800_000_030_000);
  assert.ok(h.calls.some((call) => call[0] === "checkpoint"));
});

test("last page verifies, completes and clears desired run state", async () => {
  const h = buildHarness({
    activeJob,
    tab: {
      id: 77,
      url: "https://example.invalid/list?page=1",
      status: "complete",
    },
    captureResult: {
      ok: true,
      observations: [{ observation_id: "obs-2" }],
      page_url: "https://example.invalid/list?page=1",
      pagination: {
        current_page: 1,
        total_pages: 2,
        has_next: false,
        next_url: null,
      },
    },
  });
  h.setRunState({
    desired: true,
    active_target_tab_id: 77,
    current_target_url: "https://example.invalid/list?page=1",
    cycle_count: 1,
    session_accepted_count: 1,
  });

  const result = await h.controller.runOneCycle();

  assert.equal(result.ok, true);
  assert.equal(result.completed, true);
  assert.equal(h.getRunState().desired, false);
  assert.equal(h.getRunState().terminal, true);
  assert.equal(h.getRunState().session_accepted_count, 2);
  assert.equal(h.getActive(), null);
});

test("listing shell PAGE_UNSUPPORTED schedules bounded retry instead of sleeping", async () => {
  const h = buildHarness({
    activeJob,
    tab: {
      id: 77,
      url: "https://example.invalid/list?page=0",
      status: "complete",
    },
    captureResult: {
      ok: false,
      error: "PAGE_UNSUPPORTED",
      page_context: { listing_shell_present: true },
    },
  });
  h.setRunState({
    desired: true,
    active_target_tab_id: 77,
    current_target_url: "https://example.invalid/list?page=0",
    page_retry_attempt: 0,
  });

  const result = await h.controller.runOneCycle();

  assert.equal(result.ok, true);
  assert.equal(result.retrying, true);
  assert.equal(h.getRunState().page_retry_attempt, 1);
  assert.equal(h.wakes.at(-1), 1_800_000_005_000);
});

test("delivery block stops safely and retains durable error state", async () => {
  const h = buildHarness({
    activeJob,
    tab: {
      id: 77,
      url: "https://example.invalid/list?page=0",
      status: "complete",
    },
    deliveryResult: {
      ok: false,
      error: "HTTP_503",
      flush: { error: "HTTP_503", remaining_count: 1 },
    },
  });
  h.setRunState({
    desired: true,
    active_target_tab_id: 77,
    current_target_url: "https://example.invalid/list?page=0",
  });

  const result = await h.controller.runOneCycle();

  assert.equal(result.ok, false);
  assert.equal(h.getRunState().desired, false);
  assert.equal(h.getRunState().last_error, "HTTP_503");
});

test("resumeAfterWake does nothing when durable desired flag is false", async () => {
  const h = buildHarness({ activeJob });
  h.setRunState({ desired: false });

  const result = await h.controller.resumeAfterWake();

  assert.equal(result.skipped, true);
  assert.equal(result.reason, "RUN_NOT_DESIRED");
});
