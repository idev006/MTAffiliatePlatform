import { enqueue, readOutbox, removeByMessageId } from "./outbox.js";

const SETTINGS_KEY = "program1_worker_settings_v1";

async function getSettings() {
  const result = await chrome.storage.local.get(SETTINGS_KEY);
  return result[SETTINGS_KEY] || { backend_url: "", worker_id: "" };
}

async function postJson(path, payload) {
  const settings = await getSettings();
  if (!settings.backend_url) {
    throw new Error("BACKEND_URL_NOT_CONFIGURED");
  }
  const response = await fetch(`${settings.backend_url.replace(/\/$/, "")}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP_${response.status}`);
  return response.json();
}

async function flushOutbox() {
  for (const message of await readOutbox()) {
    try {
      await postJson("/api/v1/program1/observations", message.payload);
      await removeByMessageId(message.message_id);
    } catch (_error) {
      break;
    }
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "PROGRAM1_SAVE_SETTINGS") {
    chrome.storage.local.set({ [SETTINGS_KEY]: message.settings }).then(() => sendResponse({ ok: true }));
    return true;
  }
  if (message.type === "PROGRAM1_GET_SETTINGS") {
    getSettings().then((settings) => sendResponse({ ok: true, settings }));
    return true;
  }
  if (message.type === "PROGRAM1_QUEUE_BATCH") {
    const envelope = {
      message_id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      payload: message.payload,
    };
    enqueue(envelope).then(flushOutbox).then(() => sendResponse({ ok: true }));
    return true;
  }
  if (message.type === "PROGRAM1_FLUSH_OUTBOX") {
    flushOutbox().then(() => sendResponse({ ok: true }));
    return true;
  }
  return false;
});

chrome.runtime.onStartup.addListener(flushOutbox);
