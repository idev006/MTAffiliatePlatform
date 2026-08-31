# Architecture Review — System Physiology / Component Health

Date: 2026-08-31
Review type: Senior Software Architecture + Process + QA/Testability
Status: REVIEWED — FOUNDATION REMAINS IMPLEMENTATION READY / FEATURES REMAIN GATED

## 1. Review Objective

Review the project as a coordinated operating system with explicit division of labor, management/control, communication, sensing, verification, resource management, fault detection, healing/recovery and Input/Process/Output behavior.

Documents reviewed as a set:
- `PROJECT_CHARTER.md`
- `WORKFLOW.md`
- `ARCHITECTURE.md`
- `SYSTEM_DIAGRAMS.md`
- `INTEGRATION_DIAGRAMS.md`
- `SEQUENCE_DIAGRAMS.md`
- `APPLICATION_AND_ENGINE_CONTRACTS.md`
- `DATA_MODEL.md`
- `DATABASE_CONCURRENCY_AND_PORTABILITY_SPEC.md`
- `TEST_STRATEGY_AND_QUALITY_GATES.md`
- `ENGINEERING_GOVERNANCE.md`
- Step 1/2/3 specs.

## 2. Review Findings

### A. Division of labor — PASS
Top-level authority is now explicit:
- Back Office: global business/control authority.
- Domain Engines: versioned policy/decision authority.
- Shared Job Engine: job lifecycle authority.
- Device Host Manager: device/resource authority.
- Worker Runtime: bounded execution authority.
- Adapters: technology translation only.
- Database/Ledger: durable SSOT.
- UI: presentation/operator input only.

No intentional duplicate lifecycle owner is present in the baseline.

### B. Input / Process / Output — PASS
Canonical workflow and engine contracts define inputs, processing responsibility and outputs for the three Steps. New component review template now makes this mandatory for future components.

### C. Communication / nervous system — PASS
REST, WebSocket, local IPC, worker outbox/ACK and persistence boundaries are separated by authority. WebSocket/stream/worker memory are explicitly non-authoritative.

### D. Sensing / fault detection — PASS WITH IMPLEMENTATION WORK
Architecture now identifies business and operational sensing requirements including worker heartbeat, Scene confidence, parser/schema change, queue/backlog, outbox, host resources and DB conflicts.

Implementation still needs concrete metrics/thresholds based on field/endurance tests; this is expected implementation/validation work, not an architecture ownership defect.

### E. Verification — PASS
Critical flows distinguish `action issued` from `outcome confirmed`. Durable ACK, Scene transition verification and publish-result verification/reconciliation are explicit.

### F. Healing / recovery — PASS
Layered recovery exists for jobs, workers, devices, scenes, DB conflicts and ambiguous publishing results. Irreversible actions remain fail-closed on ambiguity.

### G. Resource management / homeostasis — PASS WITH BENCHMARK GATE
CPU/RAM/disk/USB/stream/outbox/DB/API pressure are governed by admission control and controlled degradation. Numeric capacity values remain benchmark-gated by design.

### H. Testability — PASS
Health/fault/recovery paths can be simulated using fake adapters and deterministic scenario fixtures. Physical infrastructure validates adapters and capacity, not core business logic.

## 3. Defects Closed by This Review

The following prior gaps are now closed in documentation:
1. no formal system-wide Sense/Decide/Act/Verify/Recover model;
2. health detection was distributed across specs but not mandatory for every component;
3. recovery ownership was not summarized in one component matrix;
4. resource/homeostasis model was present mainly in Device Host discussions rather than as a platform-wide review lens;
5. new-component review lacked a single reusable Input/Process/Output + Health/Failure/Recovery template.

Closed through:
- `SYSTEM_PHYSIOLOGY_MODEL.md`;
- `COMPONENT_RESPONSIBILITY_AND_HEALTH_MATRIX.md`;
- updates to `ARCHITECTURE.md`;
- updates to `ENGINEERING_GOVERNANCE.md`;
- ADR-036 and ADR-037.

## 4. Remaining Feature Validation Gates

The review does not remove real-world validation requirements. Remaining notable gates include:
- Product Scoring Model v1 exact formula;
- Affiliate Offer Scoring Model v1 exact formula;
- Product/Offer identity validation against real Shopee data;
- Step 1 -> Step 2 and Step 2 -> Step 3 final handoff schemas;
- observation normalization details;
- real Shopee Android Scene inventory/signatures/selectors;
- recovery/Safe Anchor validation;
- post-submit reconciliation evidence strategy;
- perceptual fingerprint algorithm/threshold;
- device-host/screen-stream capacity benchmark;
- numeric pacing/retry/resource thresholds from endurance testing.

These are feature/production gates and must remain isolated behind accepted ports/configuration until proven.

## 5. Severity Review

Unresolved architecture defects from this review:
- CRITICAL: 0
- HIGH: 0

Open validation work is recorded as feature-specific implementation/production gates. It does not authorize guessed production behavior.

## 6. Development Handoff Decision

The foundation architecture remains suitable for development handoff.

Development may proceed on approved foundation/vertical slices provided each card satisfies the Definition of Ready and its component anatomy is documented:
- owner;
- Input/Process/Output;
- state/SSOT;
- communication;
- health signals;
- failures;
- recovery;
- resource considerations;
- test path.

If implementation discovers a conflict in ownership, state, communication, health or recovery semantics, the affected work returns to documentation/design review before continuing.
