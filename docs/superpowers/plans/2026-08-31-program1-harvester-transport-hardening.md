# Program 1 Harvester Transport Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Program 1 Browser Plugin current-page capture report durable queue and backend delivery status accurately.

**Architecture:** The browser extension remains an adapter/worker. It collects facts and durable-delivery state, while Back Office owns ingestion, deduplication, scoring and shortlist decisions. Transport behavior stays in `browser_plugin/program1/src/background.js`; page extraction stays in `content.js`; operator display stays in `sidepanel.js`.

**Tech Stack:** Manifest V3 extension JavaScript, Chrome/Brave extension APIs, FastAPI Program 1 API, SQLite portable mode, Node built-in test.

## Global Constraints

- Project must follow the document.
- Use `D:\dev\MTAffiliatePlatform\.venv` for Python commands.
- Browser workers report facts; Back Office owns canonical business transitions.
- Unsupported/CAPTCHA/schema-drift pages fail closed and must not be reported as successful empty harvests.
- No cookies/session/token inspection or export.
- No production Shopee selector claim without evidence.

---

### Task 1: Queue/Flush Result Contract

**Files:**
- Modify: `browser_plugin/program1/src/background.js`
- Test: `browser_plugin/program1/tests/background_transport.test.cjs`

**Interfaces:**
- Consumes: `enqueue(message)`, `readOutbox()`, `removeByMessageId(messageId)`
- Produces: `flushOutbox(): Promise<{ok:boolean, attempted_count:number, sent_count:number, remaining_count:number, error:string|null}>`

- [x] **Step 1: Write failing transport tests**

Add tests that simulate missing backend configuration and successful backend ACK.

- [x] **Step 2: Implement transport result object**

Make `flushOutbox()` return counts and first error instead of silently swallowing delivery failure.

- [x] **Step 3: Wire queue responses**

Make `PROGRAM1_QUEUE_BATCH` return queued message id, queued observation count, and flush result.

- [x] **Step 4: Run Node tests**

Run: `node --test browser_plugin\program1\tests\*.test.cjs`

---

### Task 2: Operator Feedback and Worker Provenance

**Files:**
- Modify: `browser_plugin/program1/src/sidepanel.js`
- Modify: `browser_plugin/program1/README.md`

**Interfaces:**
- Consumes: content-script response `{ok, profile, observations}`
- Produces: batch payload observations with `source_worker_id` when configured

- [x] **Step 1: Add worker provenance**

When a worker id is present in the side panel, attach it to each observation as `source_worker_id`.

- [x] **Step 2: Improve status output**

Show captured count, profile, queued count, sent count, remaining count and delivery error when present.

- [x] **Step 3: Update operator docs**

Document that `ok: false` can still mean the batch is durably queued but not yet delivered.

---

### Task 3: Verify Against Program 1 API

**Files:**
- Modify: `docs/affiliate-platform/evidence/SHOPEE_PROGRAM1_MARKETPLACE_DOM_ATTEMPT_2026-08-31.md`

**Interfaces:**
- Consumes: Program 1 API endpoint `/api/v1/program1/observations`
- Produces: documented evidence for live shop-page capture and SQLite persistence

- [x] **Step 1: Run backend contract tests**

Run: `D:\dev\MTAffiliatePlatform\.venv\Scripts\python.exe -m pytest tests\contract\test_program_runtime_profiles.py`

- [x] **Step 2: Run JS parser/transport tests**

Run: `node --test browser_plugin\program1\tests\*.test.cjs`

- [x] **Step 3: Record live evidence**

Document accepted live batch counts without claiming production-ready Shopee selectors.
