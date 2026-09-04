const KEY = "program1_outbox_v1";
const QUARANTINE_KEY = "program1_outbox_quarantine_v1";

export async function readOutbox() {
  const result = await chrome.storage.local.get(KEY);
  return Array.isArray(result[KEY]) ? result[KEY] : [];
}

export async function readQuarantine() {
  const result = await chrome.storage.local.get(QUARANTINE_KEY);
  return Array.isArray(result[QUARANTINE_KEY]) ? result[QUARANTINE_KEY] : [];
}

export async function enqueue(message) {
  const items = await readOutbox();
  items.push(message);
  await chrome.storage.local.set({ [KEY]: items });
}

export async function removeByMessageId(messageId) {
  const items = await readOutbox();
  await chrome.storage.local.set({
    [KEY]: items.filter((item) => item.message_id !== messageId),
  });
}

export async function quarantineByMessageId(messageId, reason) {
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
}