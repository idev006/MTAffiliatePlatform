const backendUrl = document.getElementById("backendUrl");
const workerId = document.getElementById("workerId");
const status = document.getElementById("status");

function show(value) {
  status.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function originPattern(value) {
  const url = new URL(value);
  return `${url.protocol}//${url.host}/*`;
}

chrome.runtime.sendMessage({ type: "PROGRAM1_GET_SETTINGS" }, (response) => {
  backendUrl.value = response?.settings?.backend_url || "";
  workerId.value = response?.settings?.worker_id || "";
});

document.getElementById("save").addEventListener("click", async () => {
  const url = backendUrl.value.trim();
  try {
    if (url) {
      const granted = await chrome.permissions.request({ origins: [originPattern(url)] });
      if (!granted) return show("BACKEND_PERMISSION_DENIED");
    }
    chrome.runtime.sendMessage({
      type: "PROGRAM1_SAVE_SETTINGS",
      settings: { backend_url: url, worker_id: workerId.value.trim() },
    }, show);
  } catch (error) {
    show({ ok: false, error: String(error) });
  }
});

document.getElementById("flush").addEventListener("click", () => {
  chrome.runtime.sendMessage({ type: "PROGRAM1_FLUSH_OUTBOX" }, show);
});

document.getElementById("capture").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return show("NO_ACTIVE_TAB");
  try {
    await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["src/content.js"] });
    chrome.tabs.sendMessage(tab.id, { type: "PROGRAM1_CAPTURE_FIXTURE_PAGE" }, (response) => {
      if (chrome.runtime.lastError) return show(chrome.runtime.lastError.message);
      if (!response?.ok) return show(response || "PAGE_UNSUPPORTED");
      const batch = { batch_id: crypto.randomUUID(), observations: response.observations };
      chrome.runtime.sendMessage({ type: "PROGRAM1_QUEUE_BATCH", payload: batch }, show);
    });
  } catch (error) {
    show({ ok: false, error: String(error) });
  }
});
