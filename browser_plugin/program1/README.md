# Program 1 Browser Plugin

Status: laboratory / fixture-driven implementation.

This Manifest V3 extension is the Product Discovery Worker for Program 1. It intentionally does **not** contain production Shopee selectors yet. Real collection profiles remain a validation gate in the governing documents.

Current implemented capabilities:
- Side Panel settings shell;
- backend URL and worker ID stored in extension local storage;
- local durable outbox;
- ACK-style removal only after successful backend submission;
- fixture-page capture adapter for deterministic development/testing;
- explicit PAGE_UNSUPPORTED when no supported fixture profile is found.

Next gated work:
- worker registration/heartbeat API;
- job lease/pause/resume protocol;
- saved sanitized real-page fixtures;
- versioned Shopee collection profiles after observation/validation.
