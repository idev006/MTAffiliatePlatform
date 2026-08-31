# Shared Core Specification

Status: IMPLEMENTATION HANDOFF BASELINE
Owner Domain: Shared Core / Control Plane
Migrated to authoritative repo: 2026-08-31

> This specification is governed by the newer engine-first/testability policies in `../PROJECT_STRUCTURE_AND_ENGINE_ARCHITECTURE.md`, `../APPLICATION_AND_ENGINE_CONTRACTS.md`, `../DATA_MODEL.md` and `../TEST_STRATEGY_AND_QUALITY_GATES.md`. Where wording conflicts, those newer governing documents take precedence.

## 1. Purpose

Provide the common infrastructure used by Product Intelligence, Affiliate Offer Automation, and Content Publishing without duplicating worker frameworks or state-management logic.

## 2. Core Responsibilities

- Central database / SSOT
- Job queue
- Worker registry
- Heartbeat and health status
- Rules engine
- Scheduler / dispatcher
- State machines
- Audit log
- Idempotency
- API contracts
- Monitoring
- Authentication/authorization for internal components
- Configuration/versioning
- Analytics data joins

## 3. Control Plane Principle

Python Back Office is the decision/control plane.

Workers are execution/data-plane components.

Control plane decides:
- what job should run
- priority
- ruleset
- product/offer/video/account selection
- retry policy
- duplicate policy

Worker reports:
- heartbeat
- capabilities
- current state
- observations
- execution progress
- facts/results/errors

## 4. Worker Types

Initial types:
- DISCOVERY_BROWSER_WORKER
- AFFILIATE_BROWSER_WORKER
- ANDROID_PUBLISH_WORKER

Future adapters may include API workers without changing business-domain contracts.

## 5. Worker Registry

Minimum fields:
- worker_id
- worker_type
- version
- host/device identity
- capabilities
- status
- last_heartbeat
- current_job_id
- session metadata
- last_error

Recommended status values:
- ONLINE_IDLE
- ONLINE_BUSY
- DEGRADED
- OFFLINE
- DISABLED

## 6. Job Envelope

All domains use a common envelope:
- job_id
- job_type
- idempotency_key
- priority
- payload_version
- payload
- created_at
- not_before
- retry_count
- max_retries
- assigned_worker
- current_state
- ruleset_version
- correlation_id

Domain payloads are independently versioned.

## 7. State & Durability

Database state is authoritative.

Browser extension local storage, device memory, and UI state are caches only.

All state-changing operations must be transactionally recorded before being considered durable.

## 8. Idempotency

Every externally meaningful job must have a stable idempotency key.

Examples:
- discovery: source + keyword/context + collection window
- affiliate offer job: canonical product + refresh cycle
- publishing: platform + video identity + intended publish policy

Retries must reuse the original key.

## 9. Audit Log

Record:
- actor/worker
- action
- entity
- before/after state where applicable
- timestamp
- correlation/job ID
- rule/model version
- outcome/error

Audit records are append-oriented.

## 10. Rules & Configuration

All business-important rules are versioned, including:
- product filters
- score weights
- target offer count
- freshness policy
- duplicate policy
- account/device eligibility
- retry/timeouts

Jobs record the ruleset version used.

## 11. Failure Model

Principles:
- fail closed on ambiguity for destructive/publishing actions
- recover from durable checkpoint
- do not infer success from worker disappearance
- route ambiguous results to NEEDS_HUMAN
- never silently retry a potentially completed publish

## 12. API Design Principles

- Business-level commands
- Versioned payloads
- Explicit success/error schemas
- Correlation IDs
- No dependence on DOM selectors or screen coordinates in central business contracts

## 13. Scalability Baseline

The architecture should support:
- >=1,000,000 product observations
- tens of thousands of videos
- multiple browser workers
- at least 10 Android publishing devices initially
- future horizontal worker growth without redesigning central domain models

These are design-scale targets, not performance guarantees; benchmark gates apply.

## 14. Security & Secrets

- No credentials committed to git
- Secrets remain outside worker source code
- Least-privilege internal APIs
- Worker identity is authenticated where feasible
- Sensitive logs are redacted

## 15. Testability Addendum

Shared Core must be runnable with in-memory/fake ports for component tests.

The Job Engine state machine, lease policy, idempotency policy and error/recovery decisions must not depend on FastAPI, SQLAlchemy, PySide6 or concrete worker transports.

Concrete API, DB and worker transports are adapter/integration concerns.

## 16. Acceptance Criteria

1. All three domains can create jobs through one common queue model.
2. Workers register and heartbeat through one registry.
3. A worker can be replaced without losing durable job state.
4. Job retries preserve idempotency.
5. Every major state change is auditable.
6. Domain business logic can change without changing the worker transport contract.
7. A new worker type can be introduced without redesigning existing domain tables.
8. Job Engine behavior is component-testable without network or production DB.