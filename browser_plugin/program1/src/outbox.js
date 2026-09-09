const KEY = "program1_outbox_v1";
const QUARANTINE_KEY = "program1_outbox_quarantine_v1";
const RECEIPT_KEY = "program1_last_delivery_receipt_v1";
let mutationTail = Promise.resolve();

function mutate(operation) {
  const result = mutationTail.then(operation, operation);
  mutationTail = result.catch(() => {});
  return result;
}

export async function readLastDeliveryReceipt() {
  const result = await chrome.storage.local.get(RECEIPT_KEY);
  return result[RECEIPT_KEY] || null;
}

export async function readOutbox() {
  const result = await chrome.storage.local.get(KEY);
  return Array.isArray(result[KEY]) ? result[KEY] : [];
}

export async function readQuarantine() {
  const result = await chrome.storage.local.get(QUARANTINE_KEY);
  return Array.isArray(result[QUARANTINE_KEY]) ? result[QUARANTINE_KEY] : [];
}

export async function enqueue(message) {
  return mutate(async () => {
    const items = await readOutbox();
    items.push(message);
    await chrome.storage.local.set({ [KEY]: items });
  });
}

export async function removeByMessageId(messageId, receipt = null) {
  return mutate(async () => {
    const items = await readOutbox();
    await chrome.storage.local.set({
      [KEY]: items.filter((item) => item.message_id !== messageId),
      ...(receipt ? { [RECEIPT_KEY]: {
        ...receipt, message_id: messageId, acknowledged_at: new Date().toISOString(),
      } } : {}),
    });
  });
}

export async function quarantineByMessageId(messageId, reason) {
  return mutate(async () => {
    const [items, quarantine] = await Promise.all([readOutbox(), readQuarantine()]);
    const message = items.find((item) => item.message_id === messageId);
    if (!message) return false;
    const quarantined = {
      ...message,
      quarantined_at: new Date().toISOString(),
      quarantine_reason: reason,
    };
    await chrome.storage.local.set({
      [KEY]: items.filter((item) => item.message_id !== messageId),
      [QUARANTINE_KEY]: [...quarantine, quarantined],
    });
    return true;
  });
}
