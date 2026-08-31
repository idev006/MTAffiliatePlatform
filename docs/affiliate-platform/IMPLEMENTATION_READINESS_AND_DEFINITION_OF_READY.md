# Implementation Readiness and Definition of Ready

Status: IMPLEMENTATION HANDOFF POLICY
Date: 2026-08-31

## 1. Purpose

Convert accepted architecture into executable development work without allowing unresolved design ambiguity to leak into code.

This document defines the minimum information required before a development slice may enter implementation.

## 2. Readiness Levels

Project lifecycle remains:

`DESIGN_DRAFT -> ACCEPTED_DESIGN_BASELINE -> PRE_IMPLEMENTATION_REVIEW -> IMPLEMENTATION_READY -> IMPLEMENTED -> VERIFIED`

`IMPLEMENTATION_READY` applies per feature/slice. It does not mean the entire platform is frozen forever.

## 3. Slice Definition of Ready

A development slice may enter coding only when all applicable items are satisfied.

### Business
- objective and business outcome are explicit;
- inputs/outputs are explicit;
- non-goals are explicit;
- acceptance criteria are testable.

### Ownership
- authoritative component is named;
- no duplicate SSOT/lifecycle owner exists;
- durable vs ephemeral state is clear.

### Domain
- domain entities/value objects are identified;
- state transitions/invariants are documented;
- error/unknown/ambiguous semantics are defined.

### Engine/Application
- responsible Engine/use case is identified;
- command/query/result contract is defined;
- side effects are behind ports;
- idempotency key or duplicate policy is defined where relevant.

### Persistence
- repository operations required are named;
- transaction boundary is known;
- constraints/concurrency/versioning requirements are known;
- migration impact is known.

### Paths / Filesystem
- managed runtime paths are identified;
- path ownership/root is defined;
- relative/logical storage is used where practical;
- PathManager/RuntimePaths is the resolution boundary;
- no developer-specific absolute path assumption exists;
- test path uses a temporary/injected root;
- packaging/source-run behavior is considered if affected.

### Configuration
- mutable values are classified as config/rules/invariant;
- tunable values are not hidden source constants;
- TOML location/profile is known where applicable;
- precedence/override semantics are explicit;
- settings are typed/validated;
- secret handling is separated from committed TOML;
- running-job policy version behavior is defined where config affects semantics.

Governing detail: `PATH_AND_CONFIGURATION_POLICY.md`.

### External Adapter
- required capability is defined semantically;
- vendor/tool-specific details remain adapter-local;
- failure/error mapping is defined;
- session/auth/operator requirements are explicit.

### Testing
- unit/component cases are enumerated;
- negative/error cases are enumerated;
- required fake/fixture exists or is part of the slice;
- integration environment needs are explicit;
- resilience/concurrency cases are identified;
- filesystem/config tests use temporary roots/profiles where applicable.

### Observability
- important structured events/log fields are known;
- correlation identifiers are known;
- operational evidence required for failure/reconciliation is known.

### Security/Compliance
- credentials/secrets handling is defined;
- no workflow depends on bypassing controls;
- sensitive data retention/logging is reviewed.

### Review
- unresolved CRITICAL = 0;
- unresolved HIGH = 0;
- Senior Software/Architecture review passed;
- QA/Testability review passed for affected slice.

## 4. Definition of Done

A development slice is Done only when:
- implementation conforms to governing docs/contracts;
- unit/component/contract tests pass;
- required integration tests pass;
- migrations are tested if schema changed;
- lint/type/architecture checks pass;
- important failure paths are tested;
- telemetry/audit evidence is emitted;
- documentation and ADRs are updated for material changes;
- no known CRITICAL/HIGH defect remains;
- code review confirms UI/adapter boundaries are respected;
- rollback/recovery behavior is known where deployment/data changes occur;
- no developer-specific absolute paths were introduced;
- configurable operational/business values are centralized and typed;
- TOML/profile changes include validation/test coverage when applicable.

## 5. Foundation Implementation Backlog — Recommended Order

### FND-001 Python project skeleton
Deliver:
- `src/` layout;
- package boundaries;
- pyproject tooling;
- test directories;
- bootstrap/composition root;
- baseline `config/` directory and TOML profiles;
- PathManager/RuntimePaths contract.

Acceptance:
- empty engines/application/ports/adapters import correctly;
- architecture dependency test exists;
- temp-root path test exists;
- source execution does not depend on current working directory.

### FND-002 Shared result/error/identity primitives
Deliver:
- typed IDs;
- Result/error model;
- Clock port;
- ID generator port;
- correlation context.

Acceptance:
- deterministic unit tests.

### FND-003 Configuration and Path System
Deliver:
- Pydantic typed settings;
- TOML loader;
- default/portable/farm/test profiles;
- deterministic precedence;
- PathManager/RuntimePaths implementation;
- secret references separated from ordinary config;
- effective configuration reporting with secret redaction;
- packaged/source-run path tests.

### FND-004 Persistence abstraction
Deliver:
- SQLAlchemy base/infrastructure;
- UnitOfWork/Repository contracts;
- SQLite adapter using PathManager-resolved DB location;
- PostgreSQL adapter test harness;
- Alembic baseline.

### FND-005 Shared Job Engine
Deliver:
- job model/state machine;
- lease/idempotency/version rules;
- in-memory repository;
- SQL repositories;
- tests including crash/ACK/retry scenarios;
- timing/retry policy injected via typed configuration rather than scattered constants.

### FND-006 API foundation
Deliver:
- FastAPI app factory;
- `/api/v1` routing;
- common envelope/errors;
- dependency injection from composition root;
- health/readiness endpoints.

### FND-007 Worker reference protocol
Deliver:
- registration;
- capability advertisement;
- heartbeat;
- lease/renew/result/ACK;
- local outbox reference behavior;
- outbox path/limits from PathManager + typed settings.

### FND-008 Step 1 thin slice
Input observation -> normalize -> persist -> score -> shortlist.

Use fake product source first, concrete browser adapter second.

### FND-009 Step 2 thin slice
Approved product -> candidate offers -> eligibility/ranking -> selection.

Use fake affiliate browser first.

### FND-010 Content Identity thin slice
Register video -> exact identity -> duplicate decision -> persistence.

### FND-011 Publishing plan thin slice
Product/offer/video/account constraints -> validated plan -> queued job.

No Android execution required yet.

### FND-012 Scene Engine laboratory slice
Scripted fake UI snapshots -> recognize -> transition -> recovery -> checkpoint.

No Shopee app dependency required initially.

### FND-013 Android adapter laboratory
Real device discovery/control/selector experiment behind ports.

### FND-014 Publishing laboratory flow
Validated publish plan -> fake/controlled Android workflow -> submit guard -> result/reconciliation.

### FND-015 Operator UI shell
Only after stable application commands/queries exist.

## 6. Feature Slice Template

Every Kanban implementation card should include:

```text
ID:
Objective:
Governing docs:
Engine/use case:
Inputs:
Outputs:
State/invariants:
Ports/adapters:
Persistence/transaction:
Paths/filesystem:
Configuration/TOML:
Idempotency/concurrency:
Errors/recovery:
Observability:
Security/compliance:
Tests:
Acceptance criteria:
Out of scope:
Dependencies:
Open risks:
```

## 7. Prohibited Shortcuts

The following block readiness unless explicitly approved:
- business logic implemented only in UI event handlers;
- direct ORM writes from workers/UI;
- concrete vendor SDK imported into domain engines;
- long DB transaction spanning external work;
- retry without idempotency/reconciliation semantics;
- one mutable status field representing multiple independent lifecycles;
- physical-device-only tests for logic that can be simulated;
- hidden constants for business policy that should be configuration/rules;
- coding against assumed Shopee UI details not yet observed/validated;
- developer/machine-specific absolute paths in source;
- canonical path behavior dependent on current working directory;
- direct filesystem path construction scattered across domain/application code;
- domain/engine modules loading TOML/environment directly;
- secrets committed in ordinary configuration files.

## 8. Current Platform Readiness Assessment

Ready to begin foundation implementation:
- project skeleton;
- domain/application/port structure;
- PathManager/RuntimePaths foundation;
- TOML typed configuration foundation;
- SQLAlchemy/Alembic foundation;
- Shared Job Engine;
- API/common contracts;
- test framework/fakes;
- Step 1/2 fake-driven vertical slices;
- Content Identity core;
- Scene Engine against scripted fixtures.

Still requires real-world validation before production completion:
- exact Product Scoring Model v1;
- exact Offer Scoring Model v1;
- real Shopee product/offer identity observations;
- final Step1->Step2 and Step2->Step3 schemas;
- real Android Scene catalog/signatures/selectors;
- actual product-basket capacity/version behavior;
- screen-stream/device-host benchmark;
- video perceptual fingerprint algorithm/threshold;
- post-submit reconciliation evidence rules.

These items do not block correctly isolated foundation development, but they block production readiness of their affected features.
