function messageOf(error) {
  return error && typeof error.message === "string" ? error.message : String(error);
}

export function classifyDeliveryFailure(error) {
  const message = messageOf(error);
  if (message.startsWith("ACK_")) {
    return { category: "AMBIGUOUS_RECONCILE", message, action: "STOP" };
  }
  const match = /^HTTP_(\d{3})$/.exec(message);
  if (match) {
    const status = Number(match[1]);
    if ([400, 409, 413, 415, 422].includes(status)) {
      return { category: "PERMANENT_PAYLOAD", message, action: "QUARANTINE_CONTINUE" };
    }
    if ([401, 403, 404, 405, 410].includes(status)) {
      return { category: "OPERATOR_BLOCKED", message, action: "STOP" };
    }
    if ([408, 425, 429].includes(status) || status >= 500) {
      return { category: "TRANSIENT_RETRY", message, action: "STOP" };
    }
    return { category: "HTTP_UNKNOWN", message, action: "STOP" };
  }
  if (message === "BACKEND_URL_NOT_CONFIGURED") {
    return { category: "OPERATOR_BLOCKED", message, action: "STOP" };
  }
  return { category: "NETWORK_OR_UNKNOWN_RETRY", message, action: "STOP" };
}

export async function drainObservationOutbox({
  messages,
  deliver,
  validateAck,
  remove,
  quarantine,
}) {
  let attemptedCount = 0;
  let sentCount = 0;
  let quarantinedCount = 0;
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
      const classified = classifyDeliveryFailure(error);
      lastFailure = { ...classified, message_id: message.message_id };
      if (classified.action === "QUARANTINE_CONTINUE") {
        await quarantine(message.message_id, {
          category: classified.category,
          error: classified.message,
        });
        quarantinedCount += 1;
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
    quarantined_count: quarantinedCount,
    quarantined_message_ids: quarantinedMessageIds,
    accepted_observation_count: acceptedObservationCount,
    last_failure: lastFailure,
    blocking_failure: blockingFailure,
  };
}