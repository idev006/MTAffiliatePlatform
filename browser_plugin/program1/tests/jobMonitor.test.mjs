import test from "node:test";
import assert from "node:assert/strict";
import { jobPresentation, readJobPage } from "../src/ui/jobMonitor.mjs";

test("unknown and paused states provide honest recovery guidance", () => {
  assert.match(jobPresentation("NEW_STATE").label, /ยังไม่รู้/);
  assert.match(jobPresentation("PAUSED").guidance, /อาจยังไม่ถูกบันทึก/);
  assert.match(jobPresentation("COMPLETED").guidance, /ไม่ใช่จำนวนสินค้าใหม่/);
  for (const state of ["CREATED", "QUEUED", "LEASED", "IN_PROGRESS", "VERIFYING", "FAILED", "NEEDS_HUMAN", "CANCELLED"]) {
    assert.ok(jobPresentation(state).guidance.length > 10);
    assert.notEqual(jobPresentation(state).label, "ยังไม่รู้สถานะ");
  }
});

test("reads bounded job page without issuing mutations or retries", async () => {
  const calls = [];
  const page = { items: [], total: 0, offset: 20, limit: 20 };
  assert.deepEqual(await readJobPage(20, async (...args) => {
    calls.push(args); return { ok: true, json: async () => page };
  }), page);
  assert.deepEqual(calls, [["/api/v1/program1/discovery-jobs?limit=20&offset=20"]]);
  let failures = 0;
  await assert.rejects(readJobPage(0, async () => {
    failures++; return { ok: false, status: 503 };
  }), /HTTP 503/);
  assert.equal(failures, 1);
  await assert.rejects(readJobPage(0, async () => { throw new Error("offline"); }), /offline/);
});
