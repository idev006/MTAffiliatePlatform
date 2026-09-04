# Engineering Governance — Design-First / Error-Prevention Policy

Status: ACCEPTED PROJECT POLICY
Updated: 2026-08-31
Governing rule: **Project must follow the document.**

## Purpose
Prevent avoidable implementation rework by requiring architecture, process, data, state, reliability, interface and testability defects to be identified and corrected in documentation before affected implementation proceeds.

## Lifecycle
`DESIGN_DRAFT -> ACCEPTED_DESIGN_BASELINE -> PRE_IMPLEMENTATION_REVIEW -> IMPLEMENTATION_READY -> IMPLEMENTED -> VERIFIED`

An accepted design baseline permits downstream design; it does not automatically make every feature implementation-ready.

## Review Roles
- Senior Software Engineer / Architect
- Senior Process Engineer
- Product/Business Strategist
- QA/Test perspective
- Security/Compliance perspective where affected

## Mandatory Gates

### G1 Business Objective
Objective, inputs/outputs, success/failure and non-goals are explicit.

### G2 Process
Happy path, handoffs, retries, recovery, manual intervention, concurrency and backpressure are explicit.

The process must be explainable through the control loop:
`Input -> Sense -> Validate -> Decide -> Act -> Verify -> Record -> Feedback/Recover`.

### G3 Architecture
Ownership and boundaries are explicit; SSOT authority is unique; adapters replaceable; scale does not require redesign.

Additional mandatory rules:
- business logic is engine/application owned, not UI/adapter owned;
- dependency direction is inward;
- composition root owns concrete wiring;
- UI remains optional for core execution;
- every significant component has one authority owner;
- a component cannot be considered complete if health detection or recovery ownership is undefined.

Governing detail:
- `SYSTEM_PHYSIOLOGY_MODEL.md`
- `COMPONENT_RESPONSIBILITY_AND_HEALTH_MATRIX.md`

### G4 Data
Identity/provenance, unknown/null semantics, immutable history/current state, dedupe/idempotency and retention are explicit.

### G5 Interface / Contract
Back Office↔Worker and Step-to-Step contracts are versioned with request/result/error semantics.

Commands/queries/results must use stable DTO/contracts rather than exposing UI widgets, ORM entities, DOM structures or Android selector details as business interfaces.

### G6 Reliability
Restart, checkpoint, ACK, ambiguous-state, failure isolation and endurance expectations are defined.

Before Implementation Ready, reviewers must know:
- how the component reports health;
- how abnormal state is detected;
- whether failure is retryable/non-retryable/ambiguous;
- smallest failure-containment zone;
- checkpoint/resume/reconciliation behavior;
- quarantine/failover/human-escalation path;
- how overload is handled without destabilizing unrelated work.

### G7 Configuration
Configuration ownership, overrides and auditable effective configuration are explicit.

Business policy that may vary operationally must not be buried as unexplained implementation constants.

### G8 Security / Compliance
Credentials/secrets separated and design does not depend on bypassing authentication, CAPTCHA, anti-abuse or access controls.

### G9 Testability
Testability is an architecture gate, not a post-implementation activity.

Before Implementation Ready:
- critical domain behavior can run without graphical UI;
- external side effects are behind ports/adapters;
- deterministic time/ID/randomness can be controlled where behavior depends on them;
- unit/component acceptance cases are defined;
- error/failure/recovery cases are defined;
- required fake/in-memory adapters are known;
- integration/compatibility environment needs are known;
- physical devices/browser sessions are not required to test business logic that can be simulated;
- critical state transitions and invariants have a test plan;
- sensing/health/fault signals can be simulated for resilience tests.

Governing detail: `TEST_STRATEGY_AND_QUALITY_GATES.md`.

### G9A Operator Usability

For affected operator-facing slices:
- the normal workflow is understandable without implementation knowledge;
- safe defaults exist where reasonable;
- error states explain impact and next action;
- internal transport/job/selector details are not required for ordinary use;
- advanced diagnostics remain available for support;
- UI close/restart cannot invalidate durable work.

A technically correct feature that requires unnecessary specialist knowledge for normal operation has a usability design defect.

### G9B Automated / Headless Verification

Core correctness must be executable through automated non-UI paths whenever technically possible.

Before Implementation Ready:
- business rules have deterministic unit/component paths;
- application use cases can run through fakes/in-memory ports;
- UI is not the only way to exercise a state transition;
- external/platform behavior is isolated behind adapters/fixtures;
- CI or repeatable scripts can verify affected critical flows.

Manual UI testing may complement but must not substitute for automatable core correctness.

### G10 Senior Review
Senior Software Engineer/Architect and Senior Process Engineer pass; QA/Testability review passes for affected slice; unresolved CRITICAL/HIGH design issues = 0 for affected implementation.

## Implementation-Ready Slice Requirement

Every coding card/slice must satisfy `IMPLEMENTATION_READINESS_AND_DEFINITION_OF_READY.md`.

A team may begin foundation code only for areas whose boundaries/contracts are ready. Pending real-world validation must remain isolated behind ports/configuration and cannot be guessed into production policy.

Every new component must also complete the component anatomy defined in `SYSTEM_PHYSIOLOGY_MODEL.md`: purpose, authority, input, process, output, communication, state, health, failure, recovery, resource budget and test path.

## Severity
- CRITICAL — implementation prohibited.
- HIGH — blocks IMPLEMENTATION_READY.
- MEDIUM — remediation plan required before affected correctness/reliability implementation.
- LOW — may defer if documented.

## Quality Priority
`Correctness > Recoverability > Traceability > Testability > Maintainability > Stable Throughput > Raw Speed`

## Architecture Drift Triggers

The following require review before merge:
- business logic added to PySide6/View/ViewModel event handlers;
- UI or worker directly mutates canonical database tables;
- domain/engine imports infrastructure framework/library;
- concrete browser/Android/database implementation leaks into public application contracts;
- new lifecycle owner duplicates existing SSOT;
- retry is added without idempotency/reconciliation analysis;
- long DB transaction spans remote/browser/device work;
- physical-infrastructure-only implementation makes otherwise deterministic logic untestable;
- a new component has no documented health signal or recovery/escalation path;
- overload behavior relies on unbounded queue growth;
- a silent/empty observation is interpreted as success without a validation rule;
- an irreversible action is treated as successful merely because it was issued.

## Change Control
When a material design defect/change is found:
1. stop affected work when continuing compounds rework;
2. update governing docs first;
3. record ADR when material;
4. update contracts/data/state models;
5. update tests/test plan;
6. review health/failure/recovery implications;
7. review gates;
8. resume implementation;
9. verify conformance.

## Governing Companion Documents
- `PROJECT_STRUCTURE_AND_ENGINE_ARCHITECTURE.md`
- `SYSTEM_PHYSIOLOGY_MODEL.md`
- `COMPONENT_RESPONSIBILITY_AND_HEALTH_MATRIX.md`
- `TEST_STRATEGY_AND_QUALITY_GATES.md`
- `UI_SHELL_AND_PRESENTATION_ARCHITECTURE.md`
- `IMPLEMENTATION_READINESS_AND_DEFINITION_OF_READY.md`
- `DEVELOPMENT_HANDOFF_MASTER.md`