# Program Engineering Maturity Score

Status: GOVERNING QUALITY MODEL
Date: 2026-09-04

Purpose: make the requested “90%+” maturity target evidence-based rather than subjective.

## Score dimensions

Each program is scored 0–10 on ten dimensions, total 100.

1. Strategy / Objective Fit
2. Architecture Conformance
3. Use-case Coverage
4. Automated Test / CI Quality
5. Reliability / Recovery
6. Data Integrity / Idempotency / Concurrency
7. Observability / Process Control
8. Security / Compliance / Fail-closed Behavior
9. Documentation / Traceability / Developer Handoff
10. Operability / UX / Deployment Readiness

## Evidence rule

A point may be awarded only when supported by repo evidence such as:
- governing document;
- implemented contract/source;
- automated test;
- CI/conformance result;
- migration/integration evidence;
- deterministic E2E/laboratory evidence.

A known production-specific external evidence gate may remain open while engineering maturity exceeds 90 only when:
- the uncertain behavior is isolated behind a versioned adapter/policy;
- the system fails closed;
- production readiness is not claimed for that feature.

Therefore two statuses are tracked separately:
- Engineering Maturity Score (0–100)
- Production Evidence Readiness (NOT_READY / LAB_VALIDATED / EVIDENCE_VALIDATED / PRODUCTION_APPROVED)

## Minimum 90% rule

A program cannot be rated >=90 if any of these is true:
- unresolved CRITICAL architecture/security defect;
- unresolved HIGH defect affecting core workflow;
- critical business workflow depends on UI;
- job lifecycle has a second authority outside Shared Job Engine;
- acknowledged durable data can be lost on restart;
- irreversible/ambiguous side effect blindly retries;
- CI/conformance gate is red;
- key program handoff is untyped/untraceable;
- critical negative/recovery paths lack automated tests.

## Iteration policy

Each Agile/Kanban round must:
1. start from current score/findings;
2. choose highest-risk score gaps;
3. update docs/DoR;
4. implement smallest coherent vertical slice;
5. test + failure inject;
6. run CI/conformance;
7. perform audit/CAPA;
8. record new score with evidence;
9. continue until target or explicit external evidence gate.
