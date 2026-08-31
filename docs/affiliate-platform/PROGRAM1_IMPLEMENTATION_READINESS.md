# โปรแกรมที่ 1 — Product Discovery / Product Intelligence — Implementation Readiness

Status: IMPLEMENTATION READY FOR FOUNDATION + MVP THIN SLICE
Date: 2026-08-31
Governing method: DOCUMENT-DRIVEN PROJECT / PROJECT MUST FOLLOW DOCUMENTS / AGILE KANBAN

## 1. Naming Decision

From this baseline onward, former **Step 1 — Product Discovery / Product Intelligence** is referred to operationally as **โปรแกรมที่ 1 (Program 1)**.

Historical documents may still contain the label `Step 1`; they refer to the same bounded capability unless explicitly superseded.

## 2. Program 1 Goal

Answer the business question:

> Which products should we market next, and why?

Program 1 includes two major capability groups:

1. Product Discovery Worker / acquisition adapter
2. Product Intelligence Engine / normalization, qualification, scoring, ranking and shortlist

Workers collect facts. Back Office/Engine decides.

## 3. Implementation Readiness Decision

### GO — coding may begin

The development team is authorized to implement:
- Program 1 package/module skeleton;
- application commands/queries/contracts;
- ProductObservation domain/value types;
- normalization pipeline framework;
- canonical identity abstraction without hard-freezing unvalidated Shopee assumptions;
- Product Intelligence Engine interfaces and deterministic rules framework;
- qualification/filter framework;
- explainable scoring framework with configurable model/ruleset input;
- shortlist engine;
- repository ports and in-memory implementations;
- SQLAlchemy persistence adapters after shared persistence foundation exists;
- worker registration/heartbeat/job lease integration;
- Product Discovery Worker message/outbox/state machinery;
- parser profile abstraction;
- sanitized fixture-based parser tests;
- fake ProductSourcePort;
- API/CLI test harness;
- TOML configuration profile for Program 1;
- PathManager-based filesystem references;
- structured telemetry/audit/error contracts;
- fake-driven end-to-end thin slice: observation -> normalize -> persist -> qualify/score -> shortlist.

### HOLD — do not freeze into production policy yet

The following remain validation gates:
- exact Product Scoring Model v1 formula/weights;
- minimum data sufficiency thresholds;
- final canonical Shopee product identity constraints after real observation validation;
- final observation normalization details for all Shopee surfaces;
- final Step/Program 1 -> Program 2 DTO schema;
- real Shopee search/category/shop DOM/parser profiles;
- production pacing, page limits, retry intervals and refresh frequencies;
- performance thresholds proven by endurance/scale tests.

These gates do not block architecture-conforming foundation development because they must be isolated behind configuration, rulesets, contracts and adapters.

## 4. Mandatory Architecture

Program 1 follows:

```text
Browser Worker / Import Adapter
          |
          v
ProductSourcePort / Observation Contract
          |
          v
Application Use Case
          |
          v
Normalization + Product Intelligence Engine
          |
          v
Repository / UnitOfWork Port
          |
          v
SQLite / PostgreSQL Adapter
```

The Product Intelligence Engine must run headless with fake/in-memory dependencies.

## 5. Program 1 Inputs

Conceptual inputs:
- discovery campaign/job;
- worker/source provenance;
- raw/surface product observations;
- versioned normalization rules;
- qualification ruleset;
- scoring model/ruleset;
- shortlist rules;
- current/reference time via ClockPort.

## 6. Program 1 Outputs

Conceptual outputs:
- canonical Product records/references;
- immutable ProductObservations;
- normalization findings;
- qualification decisions/reasons;
- product scores + component scores + explanation;
- shortlist decisions/rank/reasons;
- audit/domain events;
- stable Program 1 output references for Program 2.

## 7. Testability Requirement

Business logic must be testable without:
- live Shopee;
- browser;
- network;
- graphical UI;
- PostgreSQL;
- physical Android devices.

Required baseline test layers:
- unit tests for normalization/value rules;
- component tests for Product Intelligence Engine;
- contract tests for ProductSourcePort/repositories;
- fixture tests for browser parser profiles;
- integration tests for SQLite/PostgreSQL repository semantics;
- resilience tests for ACK/outbox/worker crash/job retry;
- end-to-end fake-driven Program 1 thin slice.

## 8. Path and Configuration Rules

Program 1 must follow `PATH_AND_CONFIGURATION_POLICY.md`.

Mandatory:
- `pathlib.Path`;
- PathManager/RuntimePaths;
- relative-first project/runtime paths;
- no machine-specific path literals;
- TOML configuration profiles;
- typed validated settings;
- no scattered operational/business hard-coded constants.

Candidate config organization:

```text
config/
  default.toml
  portable.toml
  farm.toml
  program1.toml
  local.toml.example
```

Exact file split may evolve, but effective settings must remain typed, traceable and testable.

## 9. Agile Kanban Start Boundary

Recommended initial Program 1 cards:

### P1-001 Program 1 package skeleton
- domain/application/engine/ports/adapters/test package boundaries
- architecture dependency test

### P1-002 ProductObservation contract + domain primitives
- typed identities
- provenance
- null/unknown semantics
- deterministic tests

### P1-003 Program 1 TOML settings + PathManager integration
- discovery limits
- profile references
- ruleset references
- data/fixture/artifact logical paths

### P1-004 In-memory repositories + UnitOfWork contracts
- product/observation/score/shortlist semantics

### P1-005 Normalization pipeline framework
- deterministic normalization stages
- reason/error model

### P1-006 Product Intelligence Engine framework
- qualification
- scoring strategy interface
- explainability
- ranking

### P1-007 Fake ProductSourcePort thin slice
- ingest -> normalize -> persist -> score -> shortlist

### P1-008 Worker protocol integration
- registration/heartbeat/job/ACK/outbox

### P1-009 Browser parser profile harness
- saved sanitized fixtures
- schema-change detection

### P1-010 Search/current-page adapter laboratory
- real authorized browser validation
- no production hard-freeze until evidence reviewed

## 10. Definition of Ready for Each Program 1 Card

Every card must identify:
- governing documents;
- objective/input/output/non-goal;
- authority owner;
- engine/use case;
- ports/adapters;
- path/config requirements;
- state/invariants;
- persistence/transaction boundary;
- idempotency/retry behavior;
- health signals and recovery;
- tests/fixtures/fakes;
- acceptance criteria;
- unresolved risks.

CRITICAL = 0 and HIGH = 0 before moving to `IN DEV`.

## 11. Definition of Done

A card is Done only when:
- code conforms to governing docs;
- tests pass;
- architecture dependency checks pass;
- no UI/business logic coupling is introduced;
- no direct worker/UI canonical DB mutation exists;
- TOML/config/path policy is followed;
- telemetry/errors/audit are implemented where required;
- docs/ADR are updated for material change;
- no known CRITICAL/HIGH defect remains.

## 12. Readiness Conclusion

**Program 1 is READY TO START CODING for foundation and fake-driven MVP vertical slices.**

Production completion remains feature-gated by real Shopee evidence, scoring-model validation, identity validation and endurance/performance validation.

This is intentional and does not represent missing foundation architecture.