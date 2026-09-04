# Program 1 Extension Message Port Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure every Program 1 extension runtime message receives a deterministic response and never leaves an unchecked `chrome.runtime.lastError` in the side panel.

**Architecture:** Keep transport error handling at the Chrome extension boundary. The background service worker converts rejected or synchronous operations into `{ ok: false, error }` responses, while the side panel uses one Promise wrapper that consumes `chrome.runtime.lastError` and normalizes missing responses.

**Tech Stack:** Chrome Manifest V3 extension APIs, JavaScript, Node.js built-in test runner

## Global Constraints

- Preserve the durable outbox and ACK validation behavior.
- Do not move business policy into extension UI handlers.
- Keep changed source files below 800 lines.
- Do not overwrite unrelated dirty-worktree changes.

---

### Task 1: Background Response Settlement

**Files:**
- Modify: `browser_plugin/program1/src/background.js`
- Test: `browser_plugin/program1/tests/background_transport.test.cjs`

**Interfaces:**
- Consumes: Chrome `runtime.onMessage` listener operations and `sendResponse`
- Produces: `respondAsync(operation, sendResponse)` with deterministic success or `{ ok: false, error }`

- [x] **Step 1: Write a failing test for a rejected background operation**

Configure the test storage adapter to reject `get()` and assert that `PROGRAM1_GET_SETTINGS` responds with `{ ok: false, error: "STORAGE_READ_FAILED" }`.

- [x] **Step 2: Run the narrow background test**

Run: `node --test browser_plugin/program1/tests/background_transport.test.cjs`

Expected: FAIL because the message callback is never settled.

- [x] **Step 3: Implement the response helper**

Add a helper that invokes an operation through a Promise boundary, sends its result, and converts rejection or synchronous failure to a stable error response. Route every asynchronous background message branch through it.

- [x] **Step 4: Run the narrow background test again**

Run: `node --test browser_plugin/program1/tests/background_transport.test.cjs`

Expected: PASS.

### Task 2: Side Panel Runtime Error Consumption

**Files:**
- Modify: `browser_plugin/program1/src/sidepanel.js`
- Test: `browser_plugin/program1/tests/sidepanel.test.cjs`

**Interfaces:**
- Consumes: `chrome.runtime.sendMessage(message, callback)`
- Produces: `sendRuntimeMessage(message): Promise<object>`

- [x] **Step 1: Write a failing test for a closed runtime message port**

Simulate `chrome.runtime.lastError.message` during the callback and assert that the wrapper resolves `{ ok: false, error: "MESSAGE_PORT_CLOSED" }`.

- [x] **Step 2: Run the narrow side-panel test**

Run: `node --test browser_plugin/program1/tests/sidepanel.test.cjs`

Expected: FAIL because the wrapper does not exist.

- [x] **Step 3: Implement and adopt the runtime message wrapper**

Read `chrome.runtime.lastError` inside the callback, normalize missing responses, and replace direct runtime messaging for initialization, settings, status, flush, and queued batches. Added equivalent tab-message handling for active-tab capture so content-script transport errors are consumed at the side-panel boundary.

- [x] **Step 4: Run all extension tests**

Run: `node --test browser_plugin/program1/tests/*.test.cjs`

Expected: PASS with zero unhandled runtime errors.

### Task 3: Runtime Verification

**Files:**
- No source changes expected

**Interfaces:**
- Consumes: local Program 1 FastAPI backend
- Produces: verified `/health` response and extension reload instructions

- [x] **Step 1: Verify the backend health endpoint**

Run: `Invoke-RestMethod http://127.0.0.1:8000/health`

Expected: response status `ok`.

- [x] **Step 2: Inspect the final focused diff**

Run: `git diff --check -- browser_plugin/program1/src/background.js browser_plugin/program1/src/sidepanel.js browser_plugin/program1/tests`

Expected: no whitespace errors.
