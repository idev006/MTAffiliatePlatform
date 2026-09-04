import assert from "node:assert/strict";
import test from "node:test";

import {
  boundedInteger,
  captureStatus,
  createIndicators,
  processViewFromCapture,
  processViewFromStatus,
  registryStatusText,
  stateTone,
  withWorkerId,
} from "../src/ui/lib/panelCore.mjs";

test("withWorkerId attaches configured worker id to each observation", () => {
  assert.deepEqual(
    withWorkerId([{ observation_id: "obs-1" }, { observation_id: "obs-2" }], " worker-01 "),
    [
      { observation_id: "obs-1", source_worker_id: "worker-01" },
      { observation_id: "obs-2", source_worker_id: "worker-01" },
    ],
  );
});

test("withWorkerId leaves observations unchanged when worker id is blank", () => {
  const observations = [{ observation_id: "obs-1" }];
  assert.equal(withWorkerId(observations, "   "), observations);
  assert.equal(withWorkerId(observations), observations);
});

test("captureStatus reports capture, queue, delivery and remaining outbox counts", () => {
  assert.deepEqual(
    captureStatus(
      { profile: "shopee-current-page-lab-v1", observations: [{}, {}] },
      {
        ok: false,
        queued: true,
        queued_observation_count: 2,
        flush: {
          sent_count: 0,
          accepted_observation_count: 0,
          remaining_count: 1,
          error: "BACKEND_URL_NOT_CONFIGURED",
        },
      },
    ),
    {
      ok: false,
      capture: {
        profile: "shopee-current-page-lab-v1",
        observation_count: 2,
      },
      queue: {
        queued: true,
        queued_observation_count: 2,
        sent_count: 0,
        accepted_observation_count: 0,
        remaining_count: 1,
        error: "BACKEND_URL_NOT_CONFIGURED",
      },
    },
  );
});

test("processViewFromStatus shows configuration readiness and outbox count", () => {
  const view = processViewFromStatus(
    {
      ok: true,
      backend_configured: false,
      worker_configured: false,
      outbox_remaining_count: 2,
      state: "CONFIG_REQUIRED",
    },
    createIndicators({}),
  );

  assert.equal(view.state, "CONFIG_REQUIRED");
  assert.equal(view.step, "Configure Backend URL before delivery");
  assert.equal(view.outbox_count, 2);
  assert.equal(view.error, null);
  assert.equal(view.session_accepted_count, 0);
  assert.equal(view.rate_per_hour, 0);
  assert.match(view.last_event, /\d/);
});

test("process views retain runtime transport error details", () => {
  assert.equal(
    processViewFromStatus({ ok: false, error: "MESSAGE_PORT_CLOSED" }, createIndicators({})).error,
    "MESSAGE_PORT_CLOSED",
  );
  assert.equal(
    captureStatus({ observations: [{}] }, { ok: false, error: "MESSAGE_PORT_CLOSED" }).queue.error,
    "MESSAGE_PORT_CLOSED",
  );
});

test("processViewFromCapture distinguishes delivered from queued delivery block", () => {
  const view = processViewFromCapture(
    { profile: "shopee-current-page-lab-v1", observations: [{}, {}] },
    {
      ok: true,
      queued: true,
      queued_observation_count: 2,
      flush: { sent_count: 1, accepted_observation_count: 2, remaining_count: 0, error: null },
    },
    createIndicators({ autoRunCount: 3, sessionAcceptedTotal: 2, sessionStartedAt: Date.now() - 60000 }),
  );

  assert.equal(view.state, "DELIVERED");
  assert.equal(view.step, "Captured, queued and delivered to Back Office");
  assert.equal(view.captured_count, 2);
  assert.equal(view.queued_count, 2);
  assert.equal(view.sent_count, 1);
  assert.equal(view.accepted_count, 2);
  assert.equal(view.outbox_count, 0);
  assert.equal(view.error, null);
  assert.equal(view.cycle_count, 3);
  assert.ok(view.rate_per_hour > 0);
  assert.match(view.last_event, /\d/);
});

test("createIndicators accumulates session totals and derives rate per hour", () => {
  const now = 1_800_000_000_000;
  const base = createIndicators({ sessionStartedAt: now - 3_600_000, sessionAcceptedTotal: 12, now });
  assert.equal(base.session_accepted_count, 12);
  assert.equal(base.rate_per_hour, 12);
  assert.equal(base.cycle_count, 0);

  const grown = createIndicators({
    sessionStartedAt: now - 3_600_000,
    sessionAcceptedTotal: 12,
    acceptedDelta: 4,
    now,
  });
  assert.equal(grown.session_accepted_count, 16);
  assert.equal(grown.rate_per_hour, 16);
});

test("boundedInteger clamps configurable recovery knobs", () => {
  assert.equal(boundedInteger("10", 2, 0, 60), 10);
  assert.equal(boundedInteger("-5", 2, 0, 60), 0);
  assert.equal(boundedInteger("90", 2, 0, 60), 60);
  assert.equal(boundedInteger("bad", 2, 0, 60), 2);
});

test("stateTone maps worker states to semantic tones", () => {
  assert.equal(stateTone("DELIVERY_BLOCKED"), "error");
  assert.equal(stateTone("PAGE_BLOCKED_BY_ANTIBOT"), "error");
  assert.equal(stateTone("PAGE_UNSUPPORTED"), "error");
  assert.equal(stateTone("CONFIG_REQUIRED"), "error");
  assert.equal(stateTone("ERROR"), "error");
  assert.equal(stateTone("DELIVERED"), "success");
  assert.equal(stateTone("READY"), "success");
  assert.equal(stateTone("IDLE"), "success");
  assert.equal(stateTone("COLLECTING"), "info");
  assert.equal(stateTone("QUEUED"), "info");
  assert.equal(stateTone("RECOVERABLE"), "warning");
  assert.equal(stateTone("STRANGE"), "idle");
});

test("registryStatusText shows a registered worker", () => {
  assert.equal(
    registryStatusText({ ok: true, registered: true, worker_id: "worker-01", error: null }),
    "Registry: registered (worker-01)",
  );
});

test("registryStatusText shows registration failure details", () => {
  assert.equal(
    registryStatusText({ ok: false, registered: false, worker_id: "", error: "HTTP_409" }),
    "Registry: not registered - HTTP_409",
  );
});

test("registryStatusText hides absent error details", () => {
  assert.equal(
    registryStatusText({ ok: false, registered: false, worker_id: "", error: null }),
    "Registry: not registered",
  );
});

test("registryStatusText handles an unknown response", () => {
  assert.equal(registryStatusText(undefined), "Registry: unknown");
});
