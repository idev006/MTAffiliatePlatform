import assert from "node:assert/strict";
import test from "node:test";

import {
  classifyDeliveryFailure,
  drainObservationOutbox,
  validateObservationBatchAck,
} from "../src/delivery_reliability.mjs";

const v2 = { ack_schema_version: "program1-observation-ack-v2", batch_id: "b",
  received_count: 2, accepted_count: 1, duplicate_count: 1, accounted_count: 2 };
const batch = { batch_id: "b", observations: [{}, {}] };

test("v2 validates mixed, duplicate-only and empty accounted receipts", () => {
  assert.equal(validateObservationBatchAck(batch, v2).duplicate_count, 1);
  assert.equal(validateObservationBatchAck(batch, { ...v2, accepted_count: 0,
    duplicate_count: 2 }).accounted_count, 2);
  assert.equal(validateObservationBatchAck({ batch_id: "b", observations: [] }, {
    ...v2, received_count: 0, accepted_count: 0, duplicate_count: 0, accounted_count: 0,
  }).accounted_count, 0);
});

test("malformed and unknown v2 receipts fail closed", () => {
  for (const patch of [
    { accepted_count: -1, duplicate_count: 3 }, { accepted_count: "1" },
    { accepted_count: 0.5, duplicate_count: 1.5 }, { duplicate_count: null },
    { duplicate_count: 0 }, { accounted_count: 1 }, { accounted_count: "2" },
    { ack_schema_version: "future" }, { ack_schema_version: null },
    { batch_id: "other" }, { received_count: 3 },
  ]) assert.throws(() => validateObservationBatchAck(batch, { ...v2, ...patch }), /ACK_/);
});

test("legacy compatibility does not infer duplicates or trust extra unversioned counts", () => {
  const legacy = { batch_id: "b", received_count: 2, accepted_count: 2, duplicate_count: 99 };
  assert.equal(validateObservationBatchAck(batch, legacy).duplicate_count, 0);
  assert.throws(() => validateObservationBatchAck(batch, { ...legacy, accepted_count: 1 }),
    /ACK_ACCEPTED_COUNT_MISMATCH/);
});

test("classifies payload errors for quarantine and contract/auth/transient errors for stop", () => {
  assert.equal(classifyDeliveryFailure(new Error("HTTP_422")).action, "QUARANTINE_CONTINUE");
  assert.equal(classifyDeliveryFailure(new Error("HTTP_409")).category, "PERMANENT_PAYLOAD");
  assert.equal(classifyDeliveryFailure(new Error("HTTP_401")).category, "OPERATOR_BLOCKED");
  assert.equal(classifyDeliveryFailure(new Error("HTTP_429")).category, "TRANSIENT_RETRY");
  assert.equal(classifyDeliveryFailure(new Error("HTTP_503")).category, "TRANSIENT_RETRY");
  assert.equal(classifyDeliveryFailure(new Error("ACK_BATCH_ID_MISMATCH")).category, "AMBIGUOUS_RECONCILE");
  assert.equal(classifyDeliveryFailure(new TypeError("fetch failed")).category, "NETWORK_OR_UNKNOWN_RETRY");
});

test("permanent poison message is quarantined and later valid message continues", async () => {
  const removed = [];
  const quarantined = [];
  const messages = [
    { message_id: "bad", payload: { batch_id: "bad", observations: [{}] } },
    { message_id: "good", payload: { batch_id: "good", observations: [{}, {}] } },
  ];
  const result = await drainObservationOutbox({
    messages,
    deliver: async (message) => {
      if (message.message_id === "bad") throw new Error("HTTP_422");
      return { batch_id: "good", received_count: 2, accepted_count: 2 };
    },
    validateAck: (payload, ack) => {
      if (ack.batch_id !== payload.batch_id) throw new Error("ACK_BATCH_ID_MISMATCH");
    },
    remove: async (id) => removed.push(id),
    quarantine: async (id, reason) => quarantined.push([id, reason]),
  });
  assert.equal(result.ok, true);
  assert.equal(result.quarantined_count, 1);
  assert.equal(result.sent_count, 1);
  assert.deepEqual(removed, ["good"]);
  assert.equal(quarantined[0][0], "bad");
  assert.equal(result.last_failure.category, "PERMANENT_PAYLOAD");
  assert.equal(result.blocking_failure, null);
  assert.deepEqual(result.sent_message_ids, ["good"]);
  assert.deepEqual(result.quarantined_message_ids, ["bad"]);
});

test("transient or ambiguous failure retains current and later messages", async () => {
  const removed = [];
  const quarantined = [];
  const messages = [
    { message_id: "first", payload: { batch_id: "first", observations: [{}] } },
    { message_id: "second", payload: { batch_id: "second", observations: [{}] } },
  ];
  const result = await drainObservationOutbox({
    messages,
    deliver: async () => { throw new Error("HTTP_503"); },
    validateAck: () => {},
    remove: async (id) => removed.push(id),
    quarantine: async (id) => quarantined.push(id),
  });
  assert.equal(result.attempted_count, 1);
  assert.equal(result.sent_count, 0);
  assert.equal(result.blocking_failure.category, "TRANSIENT_RETRY");
  assert.deepEqual(removed, []);
  assert.deepEqual(quarantined, []);
});
