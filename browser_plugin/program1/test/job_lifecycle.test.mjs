import assert from "node:assert/strict";
import test from "node:test";

import { createProgram1JobLifecycle } from "../src/job_lifecycle.mjs";

function harness({ leasedJob = null, workPackage = null, authoritativeJob = null } = {}) {
  let state = null;
  const calls = [];
  const postJson = async (path, payload) => {
    calls.push(["POST", path, payload]);
    if (path === "/api/v1/jobs/lease-next") return leasedJob;
    if (path.endsWith("/start")) {
      return { ...leasedJob, state: "IN_PROGRESS" };
    }
    if (path.endsWith("/renew")) {
      return {
        ...leasedJob,
        state: state?.state || "IN_PROGRESS",
        lease_until: "2026-09-04T14:10:00Z",
      };
    }
    if (path.endsWith("/checkpoint")) {
      return { ...leasedJob, state: "IN_PROGRESS", lease_until: "2026-09-04T14:10:00Z" };
    }
    if (path.endsWith("/verify")) {
      return { ...leasedJob, state: "VERIFYING", lease_until: "2026-09-04T14:10:00Z" };
    }
    if (path.endsWith("/complete")) {
      return { ...leasedJob, state: "COMPLETED", lease_token: null, lease_until: null };
    }
    throw new Error(`unexpected POST ${path}`);
  };
  const getJson = async (path) => {
    calls.push(["GET", path]);
    if (path.endsWith("/work-package")) return workPackage;
    if (path.startsWith("/api/v1/jobs/")) return authoritativeJob;
    throw new Error(`unexpected GET ${path}`);
  };
  const lifecycle = createProgram1JobLifecycle({
    postJson,
    getJson,
    loadState: async () => state,
    saveState: async (next) => {
      state = next;
    },
    now: () => "2026-09-04T14:00:00Z",
  });
  return { lifecycle, calls, getState: () => state, setState: (next) => { state = next; } };
}

const leasedJob = {
  job_id: "job-1",
  job_type: "DISCOVER_PRODUCTS",
  payload_ref: "plan:1",
  lease_token: "lease-1",
  lease_until: "2026-09-04T14:02:00Z",
  state: "LEASED",
};
const workPackage = {
  hypothesis: { hypothesis_id: "hyp-1" },
  signals: [{ signal_id: "demand" }],
  discovery_plan: {
    plan_id: "plan-1",
    capability_requirements: ["collector:search-lab"],
  },
};

test("leaseAndStart persists lease before fetching work package, then starts", async () => {
  const h = harness({ leasedJob, workPackage });
  const result = await h.lifecycle.leaseAndStart("worker-1");

  assert.equal(result.ok, true);
  assert.equal(result.leased, true);
  assert.equal(result.active_job.state, "IN_PROGRESS");
  assert.equal(result.active_job.work_package.discovery_plan.plan_id, "plan-1");
  assert.deepEqual(h.calls.map((x) => [x[0], x[1]]), [
    ["POST", "/api/v1/jobs/lease-next"],
    ["GET", "/api/v1/program1/discovery-jobs/job-1/work-package"],
    ["POST", "/api/v1/jobs/job-1/start"],
  ]);
});

test("leaseAndStart refuses a second lease while durable active state exists", async () => {
  const h = harness({ leasedJob, workPackage });
  h.setState({ job_id: "job-existing", state: "IN_PROGRESS" });

  const result = await h.lifecycle.leaseAndStart("worker-1");
  assert.equal(result.leased, false);
  assert.equal(result.reason, "ACTIVE_JOB_EXISTS");
  assert.equal(h.calls.length, 0);
});

test("leaseAndStart handles no compatible job without creating state", async () => {
  const h = harness({ leasedJob: null });
  const result = await h.lifecycle.leaseAndStart("worker-1");

  assert.equal(result.ok, true);
  assert.equal(result.leased, false);
  assert.equal(result.reason, "NO_COMPATIBLE_JOB");
  assert.equal(h.getState(), null);
});

test("checkpoint is durable only after authoritative API acknowledgement", async () => {
  const h = harness({ leasedJob, workPackage });
  h.setState({
    ...leasedJob,
    state: "IN_PROGRESS",
    work_package: workPackage,
  });

  const result = await h.lifecycle.checkpoint(
    "worker-1",
    "OBSERVATION_BATCH_ACK",
    { batch_id: "batch-1", accepted_count: 3 },
  );
  assert.equal(result.ok, true);
  assert.equal(h.getState().last_checkpoint.payload.batch_id, "batch-1");
  assert.equal(h.calls[0][1], "/api/v1/jobs/job-1/checkpoint");
});

test("verifyAndComplete clears durable active state only after completion", async () => {
  const h = harness({ leasedJob, workPackage });
  h.setState({
    ...leasedJob,
    state: "IN_PROGRESS",
    work_package: workPackage,
  });

  const result = await h.lifecycle.verifyAndComplete("worker-1");
  assert.equal(result.completed_job.state, "COMPLETED");
  assert.equal(h.getState(), null);
  assert.deepEqual(h.calls.map((x) => x[1]), [
    "/api/v1/jobs/job-1/verify",
    "/api/v1/jobs/job-1/complete",
  ]);
});

test("reconcile renews active authoritative leases after service-worker restart", async () => {
  const h = harness({
    leasedJob,
    workPackage,
    authoritativeJob: { ...leasedJob, state: "IN_PROGRESS" },
  });
  h.setState({ ...leasedJob, state: "IN_PROGRESS", work_package: workPackage });

  const result = await h.lifecycle.reconcile("worker-1");
  assert.equal(result.ok, true);
  assert.equal(result.renewed, true);
  assert.equal(h.getState().lease_until, "2026-09-04T14:10:00Z");
});

test("reconcile clears durable local state when backend is terminal", async () => {
  const h = harness({
    leasedJob,
    authoritativeJob: { ...leasedJob, state: "NEEDS_HUMAN" },
  });
  h.setState({ ...leasedJob, state: "IN_PROGRESS" });

  const result = await h.lifecycle.reconcile("worker-1");
  assert.equal(result.ok, true);
  assert.equal(result.terminal, true);
  assert.equal(h.getState(), null);
});

test("reconcile fails closed for non-active non-terminal state", async () => {
  const h = harness({
    leasedJob,
    authoritativeJob: { ...leasedJob, state: "QUEUED" },
  });
  h.setState({ ...leasedJob, state: "IN_PROGRESS" });

  const result = await h.lifecycle.reconcile("worker-1");
  assert.equal(result.ok, false);
  assert.equal(result.error, "RECONCILIATION_REQUIRED_QUEUED");
  assert.equal(h.getState().job_id, "job-1");
});
