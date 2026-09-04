# Program 1 — Chromium E2E and MV3 Restart/Reconcile Specification

Status: GOVERNING IMPLEMENTATION DESIGN
Date: 2026-09-05
Card: P1-H

## Objective

Prove the real unpacked Program 1 MV3 extension can execute a deterministic Shared Job across an actual Chromium browser restart without relying on the Side Panel UI or live Shopee.

This test validates adapter/runtime collaboration. It does not replace lower-level domain, contract or persistence tests.

## Scenario

```mermaid
sequenceDiagram
  participant H as E2E Harness
  participant B as Mock Back Office
  participant C1 as Chromium Context #1
  participant SW as Extension MV3 Background
  participant F as Fixture Page
  participant S as chrome.storage.local
  participant C2 as Chromium Context #2

  H->>B: start deterministic server
  H->>C1: launch persistent context + unpacked extension
  H->>SW: save worker settings + register
  H->>SW: START_BACKGROUND_RUN
  SW->>B: lease-next / work-package / start
  SW->>S: persist active job + desired run state
  H->>SW: RUN_BACKGROUND_CYCLE
  SW->>F: create fixture page 1
  H->>SW: RUN_BACKGROUND_CYCLE after load
  SW->>F: inject core/profiles/router/bootstrap
  F-->>SW: fixture observations + next page
  SW->>B: observation batch
  B-->>SW: authoritative ACK
  SW->>B: checkpoint page 1
  SW->>S: persist page 2 target + counters

  H->>C1: close browser context (simulated browser/MV3 loss)

  H->>C2: reopen same persistent profile
  C2->>SW: startup
  SW->>B: register + reconcile/renew active job
  SW->>S: recover active job/run state
  H->>SW: read status; assert same job and desired run
  H->>SW: RUN_BACKGROUND_CYCLE
  SW->>F: recreate stale/missing target tab for page 2
  H->>SW: RUN_BACKGROUND_CYCLE after load
  SW->>B: second observation batch
  B-->>SW: authoritative ACK
  SW->>B: checkpoint
  SW->>B: verify / complete
  SW->>S: clear active job; mark terminal run
  H->>B: assert exactly two batches / no duplicate page
```

## Environment

Portable requirements:
- Python 3.12;
- Playwright Python package;
- Playwright Chromium;
- Node/npm only to build the extension Side Panel before launch;
- local loopback HTTP only;
- no Shopee/network dependency;
- no operator interaction.

Linux CI uses headed Chromium under Xvfb because unpacked MV3 extension service workers are not treated as a headless-core correctness substitute.

Windows/local runs may use Playwright Chromium without machine-specific Brave paths.

## Mock Back Office contract

The harness implements only the production-level HTTP contracts consumed by the extension:

- worker register;
- worker heartbeat;
- Shared Job lease-next;
- Program 1 work-package read;
- job start;
- authoritative job read;
- lease renew;
- checkpoint;
- verify;
- complete;
- Program 1 observation ingestion ACK.

The mock must retain authoritative job state across Chromium context restart.

## Acceptance criteria

1. extension service worker is detected in both browser contexts;
2. worker registers without Side Panel interaction;
3. the same job id/lease lineage is recovered after browser restart;
4. desired run state remains durable;
5. stale tab id does not crash recovery; a new controlled tab is created;
6. page 1 and page 2 each yield exactly one observation batch;
7. each batch is ACKed before checkpoint;
8. page 1 checkpoint exists before restart;
9. second context performs reconcile/renew before continuing bounded work;
10. final job state is COMPLETED;
11. local active-job state is cleared only after authoritative completion;
12. run state becomes terminal/not desired;
13. outbox remaining count is zero;
14. no duplicate batch/page observation is accepted;
15. no graphical UI click is required.

## Failure assertions

The harness must fail if:
- extension service worker is missing;
- register/start/lease/reconcile contract deviates;
- page collection fails;
- ACK mismatches;
- browser restart loses canonical local state;
- completion happens before page 2;
- duplicate page observations are sent;
- active job remains locally after backend completion.

## CI placement

A dedicated `program1-browser-e2e` job runs after deterministic source checkout and installs only the dependencies required for the real browser adapter test.

This job is separate from `program1-extension` unit/component tests so failures identify the correct architecture layer.

## Safety

- fixture pages are local only;
- no Shopee login/session/cookies;
- no anti-bot interaction;
- no external browser automation target;
- no production side effects.

## Definition of Done

P1-H is Done when:
- portable harness committed;
- Linux CI job passes;
- restart/reconcile scenario passes;
- docs/Kanban updated;
- extension/core/SQLite/stress/conformance remain green;
- defects discovered during implementation have RCA/CAPA and regression coverage.
