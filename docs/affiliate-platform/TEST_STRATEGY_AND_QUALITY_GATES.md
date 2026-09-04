# Test Strategy and Quality Gates

Status: IMPLEMENTATION HANDOFF POLICY
Date: 2026-08-31

## 1. Purpose

Make the platform testable by design rather than adding tests after implementation.

Testing is part of architecture. A component that cannot be isolated, stimulated deterministically and observed through stable contracts is considered poorly designed even if it currently works.

## 2. Testing Principles

1. Critical business rules are tested without UI or physical infrastructure.
2. Side effects are behind ports and adapters.
3. Time, randomness, IDs and external responses are controllable in tests.
4. Domain state transitions are explicit and assertable.
5. Every bug that reaches development/QA should normally gain a regression test.
6. Integration tests prove adapters; unit/component tests prove business logic.
7. End-to-end tests are selective and valuable, not the primary safety net.
8. SQLite and PostgreSQL behavior differences must be covered by compatibility tests for Tier-1 features.
9. Irreversible publishing behavior requires failure-injection and ambiguity tests before production use.

## 3. Test Layers

### Unit Tests
Scope:
- pure policies;
- value objects;
- scoring functions;
- state-machine guards;
- duplicate classification;
- Scene confidence/scoring;
- retry/recovery decision logic.

Properties:
- milliseconds where practical;
- no DB/network/browser/device/UI;
- deterministic.

### Component Tests
Scope:
- one Engine or application use case with in-memory/fake ports;
- multiple collaborating domain objects;
- event/state verification.

Examples:
- Product Intelligence Engine with fake observation repository;
- Publishing Engine with in-memory ledger;
- Scene Engine with scripted fake UI snapshots.

### Contract Tests
Scope:
- API DTOs;
- worker command/result envelopes;
- repository port behavior;
- adapter capability contracts;
- schema version compatibility.

Every concrete adapter must satisfy the same contract suite as its fake/reference implementation where meaningful.

### Integration Tests
Scope:
- SQLAlchemy repository with real SQLite;
- SQLAlchemy repository with PostgreSQL in CI/test container;
- Alembic migrations;
- FastAPI routes + actual application container;
- browser extension/backend transport integration;
- Android adapter laboratory integration.

### End-to-End Tests
Scope:
- selected vertical slices from command to durable result;
- portable runtime smoke path;
- worker lease/result flow;
- controlled publishing flow using a safe test target/environment when available.

Do not make E2E tests responsible for validating every rule combination.

### Resilience / Failure-Injection Tests
Mandatory scenarios include:
- worker process killed after lease;
- ACK lost after Back Office commit;
- duplicate result submitted twice;
- lease expiration/reassignment;
- stale optimistic version;
- DB deadlock/conflict where applicable;
- outbox resend;
- network disconnect;
- device disconnect;
- Android app unexpected Scene;
- adapter schema/selector change;
- publish submitted but result unknown;
- Back Office restart during active workload.

### Compatibility Tests
Tier-1 DB compatibility:
- SQLite;
- PostgreSQL.

Verify:
- migrations;
- constraints;
- transaction behavior used by the application;
- repository semantics;
- timestamps/null behavior;
- concurrency assumptions;
- upsert/conflict handling where used.

## 4. Test Directory Baseline

```text
tests/
├─ unit/
├─ component/
├─ contract/
├─ integration/
│  ├─ sqlite/
│  ├─ postgres/
│  ├─ api/
│  ├─ browser/
│  └─ android/
├─ e2e/
├─ resilience/
├─ compatibility/
├─ fixtures/
├─ fakes/
├─ factories/
└─ golden/
```

`golden/` may contain sanitized deterministic Scene snapshots, payloads and expected outputs suitable for regression testing. Secrets/session data must never be stored there.

## 5. Required Test Doubles

Foundation implementation should provide reusable test doubles:
- FakeClock;
- DeterministicIdGenerator;
- InMemoryJobRepository;
- InMemoryProductRepository;
- InMemoryOfferRepository;
- InMemoryVideoRepository;
- InMemoryPublishingLedger;
- FakeProductSource;
- FakeAffiliateBrowser;
- FakeDeviceTransport;
- ScriptedUIAutomationAdapter;
- FakeMediaProbe;
- InMemoryEventPublisher;
- FakeNotificationAdapter.

Prefer behavior-rich fakes over excessive mocks for core workflows.

Mocks are appropriate at narrow interaction boundaries when exact calls matter.

## 6. Determinism Requirements

Production code must not directly call uncontrolled global facilities inside domain engines when behavior depends on them.

Avoid direct use of:
- `datetime.now()`;
- random generators;
- environment variables;
- filesystem globals;
- singleton network clients;
- hidden process-wide mutable state.

Inject abstractions/configuration at boundaries so tests can control them.

## 7. State Machine Testing

Every important state machine must have:
- allowed-transition tests;
- forbidden-transition tests;
- idempotent-repeat tests;
- terminal-state tests;
- stale/concurrent update tests;
- restart/resume tests where durable.

Critical state machines:
- Shared Job lifecycle;
- worker/device health lifecycle;
- Product shortlist lifecycle where stateful;
- Offer selection/freshness lifecycle;
- Video duplicate/publish lifecycle;
- Publishing Ledger;
- Scene/Process workflow;
- publish reconciliation.

## 8. Property and Table-Driven Tests

Use parameterized/table-driven tests for rule matrices.

Property-based testing is recommended for invariants with large input spaces, especially:
- scoring bounds/normalization;
- identity normalization;
- idempotency;
- state transition invariants;
- duplicate fingerprint thresholds once frozen;
- pagination/sharding boundary calculations.

Hypothesis is an acceptable candidate for Python property-based tests.

## 9. API Contract Quality Gates

For every public command/result contract:
- valid payload acceptance;
- invalid payload rejection;
- unknown/nullable semantics;
- schema version handling;
- idempotency behavior;
- authentication/authorization where relevant;
- conflict semantics;
- stable error code assertions.

HTTP status code alone is not sufficient; stable application error codes are required.

## 10. Database Quality Gates

Every migration must be tested from:
- empty database to head;
- previous supported release revision to head.

For destructive or data-transforming migrations, define backup/recovery expectations.

Repository tests must verify that database constraints enforce critical invariants rather than relying only on service code.

No test may depend on one giant shared mutable database fixture.

## 11. Android / Scene Testing Pyramid

Most Scene Engine behavior must run with scripted snapshots/hierarchies and a fake automation adapter.

Physical-device tests are reserved for:
- selector validity;
- activity/package behavior;
- timing/latency;
- actual app transitions;
- permissions/dialogs;
- recovery feasibility;
- screen streaming/control compatibility.

This prevents the physical device farm from becoming a prerequisite for every CI run.

## 12. Browser Worker Testing

Separate:
- page parsing/normalization tests using saved sanitized fixtures;
- extension message-routing tests;
- outbox/ACK tests;
- live-browser laboratory tests.

DOM fixture tests must make schema changes visible as failures instead of silently returning empty observations.

## 13. Performance and Capacity Testing

Performance budgets must be measured at component boundaries.

Initial benchmark families:
- job lease throughput;
- observation batch ingestion;
- scoring throughput;
- outbox replay;
- SQLite single-writer behavior;
- PostgreSQL concurrent workers;
- API/WebSocket load;
- Device Host CPU/RAM/USB/network usage at 10/20/50/100 devices;
- screen-stream Overview vs Focus mode.

Performance optimization must not weaken correctness invariants.

## 14. Coverage Policy

Do not use total line coverage as the sole quality target.

Required:
- all CRITICAL business invariants have explicit named tests;
- all state transitions have tests;
- all error/recovery branches of irreversible actions have tests;
- every production incident/confirmed defect gains a regression test when reproducible.

A numeric coverage threshold may be added in CI, but it is subordinate to risk-based coverage.

## 15. CI Gate Baseline

Before merge to main, foundation CI should eventually run:
1. formatting/lint;
2. static typing;
3. architectural dependency checks;
4. unit tests;
5. component tests;
6. contract tests;
7. SQLite integration/migrations;
8. PostgreSQL integration/migrations;
9. selected resilience tests.

Physical Android/browser farm suites may run separately as scheduled/laboratory gates where infrastructure is required.

## 15.1 Full-Automation Preference

For every new capability, reviewers should first ask whether the acceptance path can be proven without UI.

Preferred path:
`domain/unit -> application/component -> contract -> integration -> resilience -> deterministic E2E`.

Manual UI interaction is reserved for presentation acceptance and controlled external evidence that cannot be simulated.

Where a core behavior cannot be automated, the reason and alternative control/monitoring must be documented.

## 16. Definition of Done — Testing

A feature is not Done unless:
- acceptance criteria are represented by tests;
- normal path is tested;
- important negative paths are tested;
- retry/idempotency/concurrency behavior is tested where applicable;
- logs/events are assertable where operationally important;
- adapter behavior is covered at the correct layer;
- documentation/contracts are updated;
- no unresolved CRITICAL/HIGH testability issue remains.