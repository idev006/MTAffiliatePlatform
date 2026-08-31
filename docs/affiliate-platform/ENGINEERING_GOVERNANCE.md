# Engineering Governance — Design-First / Error-Prevention Policy

Status: ACCEPTED PROJECT POLICY
Governing rule: **Project must follow the document.**

## Purpose
Prevent avoidable implementation rework by requiring architecture, process, data, state, reliability and interface defects to be identified and corrected in documentation before affected implementation proceeds.

## Lifecycle
`DESIGN_DRAFT -> ACCEPTED_DESIGN_BASELINE -> PRE_IMPLEMENTATION_REVIEW -> IMPLEMENTATION_READY -> IMPLEMENTED -> VERIFIED`

An accepted design baseline permits downstream design; it does not automatically make every feature implementation-ready.

## Review Roles
- Senior Software Engineer
- Senior Process Engineer
- Product/Business Strategist
- QA/Test perspective

## Mandatory Gates
### G1 Business Objective
objective, inputs/outputs, success/failure and non-goals are explicit.

### G2 Process
happy path, handoffs, retries, recovery, manual intervention, concurrency and backpressure are explicit.

### G3 Architecture
ownership and boundaries are explicit; SSOT authority is unique; adapters replaceable; scale does not require redesign.

### G4 Data
identity/provenance, unknown/null semantics, immutable history/current state, dedupe/idempotency and retention are explicit.

### G5 Interface / Contract
Back Office↔Worker and Step-to-Step contracts are versioned with request/result/error semantics.

### G6 Reliability
restart, checkpoint, ACK, ambiguous-state, failure isolation and endurance expectations are defined.

### G7 Configuration
configuration ownership, overrides and auditable effective configuration are explicit.

### G8 Security / Compliance
credentials/secrets separated and design does not depend on bypassing authentication, CAPTCHA, anti-abuse or access controls.

### G9 Testability
acceptance, failure injection, scale/concurrency, integrity and migration/recovery tests exist.

### G10 Senior Review
Senior Software Engineer and Senior Process Engineer pass; unresolved CRITICAL/HIGH design issues = 0 for affected implementation.

## Severity
- CRITICAL — implementation prohibited.
- HIGH — blocks IMPLEMENTATION_READY.
- MEDIUM — remediation plan required before affected correctness/reliability implementation.
- LOW — may defer if documented.

## Quality Priority
`Correctness > Recoverability > Traceability > Maintainability > Throughput > Raw Speed`

## Change Control
When a material design defect/change is found:
1. stop affected work when continuing compounds rework;
2. update governing docs first;
3. record ADR when material;
4. update contracts/data/state models;
5. review gates;
6. resume implementation;
7. verify conformance.
