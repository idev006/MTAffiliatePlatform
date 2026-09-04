# Development Cycle Standard

Status: GOVERNING PROJECT POLICY
Date: 2026-08-31
Applies to: Entire MTAffiliatePlatform project

## 1. Governing Principles

This project is operated as:
- DOCUMENT-DRIVEN PROJECT;
- PROJECT MUST FOLLOW DOCUMENTS;
- Agile delivery;
- Kanban flow;
- engine-first / headless-first where applicable;
- API/contract-driven integration;
- portable-first and scale-ready;
- testable-friendly by architecture;
- continuous learning from defects and field evidence.

Code that conflicts with approved governing documents is non-conforming until the discrepancy is intentionally resolved.

## 2. Standard Development Loop

```text
Need / Problem / Goal
  -> Evidence / Context
  -> Document / ADR / Contract update
  -> Definition of Ready review
  -> Kanban READY
  -> Implement smallest vertical slice
  -> Developer verification
  -> Automated quality gates
  -> Adversarial / negative / failure tests
  -> Code + architecture review
  -> Integration / compatibility tests
  -> Release candidate / controlled rollout when applicable
  -> Observe telemetry / operator feedback / incidents
  -> Problem & Lesson record
  -> Root Cause Analysis
  -> Corrective + Preventive Action
  -> Regression test / guardrail
  -> Update documents
  -> Feed next backlog
```

This loop is recursive. Learning changes the documents, tests and design before the next similar implementation proceeds.

## 2.1 Commit / Push Safety Discipline

The repository is the recoverable project SSOT. Development must not leave substantial completed work only on one local machine.

Rules:
- commit at small, coherent, reviewable checkpoints;
- push to GitHub frequently after meaningful recoverable checkpoints;
- prefer buildable/tested commits; if a temporary WIP push is necessary, label it clearly and do not represent it as verified;
- documentation/contract changes should be pushed before or with the implementation they govern;
- after a verified vertical slice, push code, tests and documentation/status evidence before starting unrelated work;
- avoid large uncommitted batches that make rollback/RCA difficult.

Useful checkpoints include:
`docs/contract -> domain/tests -> application/tests -> adapter/fixtures -> integration/resilience -> verification/handoff`.

Commit count is not a quality metric. The goal is recoverability, traceability, reviewability and reduced work-loss risk.

## 2.2 Usability as a Development Constraint

Operator-facing features must be understandable to users with limited technical knowledge.

Engineering should:
- provide safe defaults;
- use task-oriented language;
- expose a clear next action on errors;
- hide internal identifiers/protocol details from ordinary workflows;
- preserve advanced diagnostics through progressive disclosure;
- avoid making manual config-file editing a normal-user requirement.

Ease of use is evaluated alongside correctness and reliability.

## 3. Kanban States

`BACKLOG -> ANALYSIS -> DESIGN/CONTRACT -> READY -> IN DEV -> CODE REVIEW -> VERIFY -> DONE`

Exception states:
- BLOCKED
- NEEDS_DECISION
- NEEDS_REAL_DATA
- NEEDS_DEVICE_LAB
- NEEDS_HUMAN

No card may skip DESIGN/CONTRACT or VERIFY for convenience.

## 4. Definition of Ready

A card may enter READY only when proportionate to its risk it has:
1. business objective and acceptance criteria;
2. owner/component boundary;
3. inputs/outputs/contracts;
4. data/state ownership;
5. happy path plus major negative/failure paths;
6. idempotency/concurrency/retry requirements where applicable;
7. configuration/path requirements;
8. security/privacy/platform constraints;
9. test plan and test-double strategy;
10. observability/health/recovery expectations;
11. no unresolved CRITICAL/HIGH design issue.

## 5. Implementation Rule

Prefer the smallest end-to-end vertical slice that proves architecture and contracts.

Order where applicable:
`Domain -> Engine/Application -> Port -> Fake/Test -> Concrete Adapter -> API/CLI -> UI`.

Do not implement uncertain platform behavior as hard-coded business logic. Keep it behind versioned configuration/rules/adapters until validated.

## 6. World-Class Product Verification Model

Testing is risk-based and layered. A product capability is not considered verified merely because unit tests pass.

### Layer A — Static / Build Quality
- formatter/lint;
- static typing as adopted;
- dependency/security checks;
- architecture dependency rules;
- build/package reproducibility.

### Layer B — Unit / Property Tests
- pure rules;
- boundary values;
- invalid values;
- deterministic invariants;
- property-based tests for broad input spaces.

### Layer C — Component / Contract Tests
- application use cases with fakes;
- repository port contract;
- API schemas/status/error codes;
- worker message/idempotency contracts.

### Layer D — Integration / Compatibility
- SQLite real database;
- PostgreSQL real database;
- migrations;
- real HTTP stack where useful;
- browser/device adapters in controlled laboratories.

### Layer E — Resilience / Failure Injection
- duplicate delivery;
- ACK loss;
- restart mid-operation;
- stale versions;
- lock/contention/deadlock;
- network loss;
- corrupted/partial external data;
- schema/UI changes;
- resource pressure;
- uncertain outcome.

### Layer F — Performance / Capacity / Endurance
- nominal load;
- peak load;
- sustained load;
- burst traffic;
- resource saturation;
- recovery after pressure;
- large dataset behavior.

### Layer G — End-to-End / Product Acceptance
- representative user/business workflow;
- durable final state;
- auditability;
- recovery/reconciliation;
- operator experience when UI is involved.

### Layer H — Controlled Release / Operational Validation
Where production/external systems are involved:
- staged rollout;
- health metrics;
- rollback/disable plan;
- incident detection;
- post-release observation window.

## 7. Risk-Based Test Requirement

Risk determines test depth.

CRITICAL examples:
- duplicate publishing;
- irreversible external action;
- data loss/corruption;
- authentication/security boundary;
- wrong durable lifecycle state.

CRITICAL behavior requires explicit named tests for normal, negative, retry, concurrent, restart and ambiguous-outcome paths where applicable.

## 8. Quality Gate Rule

A gate failure is information, not something to suppress to make CI green.

When a gate detects a real defect:
1. record the finding;
2. identify root cause;
3. correct design/code/config;
4. add regression coverage;
5. update documents if the defect exposed a missing rule;
6. rerun the full affected gate.

Never reduce a legitimate quality rule solely to make a build pass.

## 9. Problem / Defect Record

Every meaningful defect, near miss or operational issue must capture:
- ID/date/component;
- severity and impact;
- detection source;
- observable symptom;
- expected vs actual behavior;
- reproduction/evidence;
- immediate containment;
- root cause;
- contributing factors;
- corrective action;
- preventive action;
- regression test/monitoring added;
- documents/ADR/config changed;
- owner/status;
- verification evidence.

Use 5-Whys, fault-tree or equivalent causal analysis for HIGH/CRITICAL issues. Do not stop at symptoms such as “developer mistake”.

## 10. CAPA — Corrective and Preventive Action

Corrective Action fixes the current defect.
Preventive Action changes the system so the class of defect is less likely to recur.

Examples of preventive actions:
- stronger domain constraint;
- DB unique/foreign-key constraint;
- typed configuration validation;
- architecture dependency check;
- regression/property test;
- fixture/golden dataset;
- lint/static rule;
- CI gate;
- improved telemetry;
- updated design checklist;
- changed API contract;
- updated runbook.

## 11. Lesson Learned Record

Lessons are not generic notes. Each lesson must answer:
- what did we assume?
- what evidence disproved or refined the assumption?
- what design/process/test change follows?
- where is that change enforced?
- does it apply to other programs/components?

A lesson is considered adopted only after it changes at least one durable artifact: document, ADR, checklist, test, CI rule, configuration schema, code guardrail or runbook.

## 12. Definition of Done

A card is DONE only when:
- acceptance criteria pass;
- code follows governing documents;
- tests at required layers pass;
- CRITICAL/HIGH defects are zero;
- regression tests exist for discovered defects where reproducible;
- logs/metrics/health behavior are adequate;
- documentation/contracts/config examples are updated;
- problem/lesson records are updated if issues were discovered;
- CI/verification evidence is referenced;
- no known hidden manual step is required for core correctness.

## 13. Release Readiness

Production release readiness additionally requires:
- migration/rollback validation;
- dependency/version lock review;
- security/privacy review appropriate to feature;
- capacity evidence for expected load;
- recovery/runbook readiness;
- configuration validation;
- monitoring/alerting;
- staged rollout/rollback strategy when meaningful;
- unresolved CRITICAL/HIGH = 0.

## 14. Metrics

Track trend, not vanity numbers:
- escaped defects;
- defect recurrence rate;
- mean time to detect;
- mean time to recover;
- flaky test rate;
- CI pass/fail by root cause;
- regression coverage for incidents;
- change failure rate;
- recovery success rate;
- lead time through Kanban;
- blocked time;
- coverage of critical invariants;
- capacity headroom.

Numeric line coverage is supporting evidence, never a substitute for risk coverage.

## 15. Mandatory Feedback Loop

Every verified defect or incident must end in one of:
- regression test;
- explicit documented reason why a deterministic regression test is not possible, plus alternative monitoring/control.

Every repeated defect class automatically becomes a process/design review trigger.

## 16. Program-Specific Tailoring

Each Program may add stricter gates but may not remove this baseline without an approved ADR.

Program 1 currently adds:
- ProductObservation validation;
- scoring property/boundary tests;
- batch idempotency/conflict tests;
- repository contract tests;
- SQLite/PostgreSQL compatibility;
- browser fixture/schema-change tests;
- discovery ingestion load/endurance tests.
