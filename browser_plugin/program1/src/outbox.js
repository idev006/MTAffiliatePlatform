const KEY = "program1_outbox_v1";

export async function readOutbox() {
  const result = await chrome.storage.local.get(KEY);
  return Array.isArray(result[KEY]) ? result[KEY] : [];
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
