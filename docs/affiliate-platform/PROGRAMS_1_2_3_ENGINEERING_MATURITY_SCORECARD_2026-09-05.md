# Programs 1–3 Engineering Maturity Scorecard

Status: ENGINEERING COMPLETION BASELINE
Date: 2026-09-05
Scope: Program 1 Product Discovery/Opportunity Intelligence, Program 2 Affiliate Offer Intelligence, Program 3 Content Publishing/Android Control Plane.

## Important interpretation

These scores are **engineering maturity scores**, not a guarantee of affiliate revenue and not a claim that every live Shopee browser/Android behavior is production-validated.

Real Shopee selectors, anti-bot/network behavior, account-specific surfaces, Android scene signatures, basket capacity, pacing and final external publish-success evidence remain versioned production-evidence gates. The score explicitly reserves 5 points for this category so evidence gaps cannot be hidden by high unit-test coverage.

## Scoring model

| Dimension | Weight |
|---|---:|
| Architecture / authority ownership | 15 |
| Functional completeness / contracts | 15 |
| Persistence / idempotency / restart | 15 |
| Automated tests / coverage | 15 |
| Resilience / recovery | 15 |
| Security / safety | 10 |
| Cross-program integration / traceability | 5 |
| SSOT / documentation / conformance | 5 |
| Production evidence / live readiness | 5 |
| **Total** | **100** |

A program is considered engineering-complete for the current foundation when:
- total score is at least 90;
- unresolved CRITICAL findings = 0;
- unresolved HIGH findings = 0;
- applicable CI/conformance gates pass;
- evidence-gated live-platform assumptions remain explicit and fail closed.

## Final scores

| Program | Score | Result |
|---|---:|---|
| Program 1 — Product Discovery / Opportunity Intelligence | **93.0 / 100** | PASS >=90 |
| Program 2 — Affiliate Offer Intelligence | **95.0 / 100** | PASS >=95 |
| Program 3 — Content Publishing / Android Control Plane | **95.5 / 100** | PASS >=95 |

## Program 1 score

| Dimension | Score |
|---|---:|
| Architecture / authority | 14.5 / 15 |
| Functional completeness / contracts | 14.0 / 15 |
| Persistence / idempotency / restart | 14.0 / 15 |
| Automated tests / coverage | 15.0 / 15 |
| Resilience / recovery | 13.5 / 15 |
| Security / safety | 9.0 / 10 |
| Cross-program integration / traceability | 5.0 / 5 |
| SSOT / docs / conformance | 5.0 / 5 |
| Production evidence / live readiness | 3.0 / 5 |
| **Total** | **93.0** |

Evidence:
- Program 1 SSOT/runtime/test conformance PASS;
- browser extension 82/82 tests PASS;
- durable Shared Job/lease/checkpoint path;
- durable local outbox and worker registry;
- evidence-first Opportunity Intelligence and QualifiedOpportunityHandoff;
- full deterministic Program 1 -> Program 2 -> Program 3 contract E2E PASS;
- collection router/profile registry and delivery reliability are verified while Shopee surface profiles remain evidence-gated;
- anti-bot state fails closed rather than being treated as an empty page.

Remaining production-evidence limits:
- current Shopee collection profile remains laboratory/evidence-gated;
- second independent selector/field capture and repeated-session evidence remain required for profile promotion;
- anti-bot/network traffic gate must not be bypassed.

## Program 2 score

| Dimension | Score |
|---|---:|
| Architecture / authority | 15.0 / 15 |
| Functional completeness / contracts | 14.5 / 15 |
| Persistence / idempotency / restart | 14.5 / 15 |
| Automated tests / coverage | 15.0 / 15 |
| Resilience / recovery | 13.5 / 15 |
| Security / safety | 9.5 / 10 |
| Cross-program integration / traceability | 5.0 / 5 |
| SSOT / docs / conformance | 5.0 / 5 |
| Production evidence / live readiness | 3.0 / 5 |
| **Total** | **95.0** |

Evidence:
- Program 2 SSOT/runtime/test conformance PASS;
- typed QualifiedOpportunityHandoff -> OfferDiscoveryPlan -> Shared Job -> account/session-bound observations;
- deterministic evidence-first offer qualification and durable OfferSelectionDecision;
- validated AffiliateLinkArtifact and Program3OfferHandoff;
- SQL/Alembic persistence and restart verification;
- forged worker, wrong account, stale lease, missing session and semantic-collision cases covered;
- full deterministic Program 1 -> 2 -> 3 closed-loop contract PASS.

Remaining production-evidence limits:
- live affiliate surface/profile/export behavior remains versioned and evidence-gated;
- actual account/session/platform changes require fresh controlled evidence before promotion.

## Program 3 score

| Dimension | Score |
|---|---:|
| Architecture / authority | 15.0 / 15 |
| Functional completeness / contracts | 14.5 / 15 |
| Persistence / idempotency / restart | 14.5 / 15 |
| Automated tests / coverage | 15.0 / 15 |
| Resilience / recovery | 14.5 / 15 |
| Security / safety | 10.0 / 10 |
| Cross-program integration / traceability | 5.0 / 5 |
| SSOT / docs / conformance | 5.0 / 5 |
| Production evidence / live readiness | 2.0 / 5 |
| **Total** | **95.5** |

Evidence:
- Program 3 SSOT/runtime/test conformance PASS;
- Program2 handoff -> immutable/durable PublishPlan -> Shared PUBLISH_CONTENT job;
- durable pre-submit decision is Back Office authority and cannot be forged by a client object;
- active Shared Job lease **and active durable device ownership lease** required before submit;
- device registry survives SQLite restart and uses optimistic version conflicts;
- POST_SUBMITTED is durably recorded in execution repository, Publishing Ledger and Shared Job checkpoint;
- OUTCOME_UNKNOWN never permits blind retry;
- only CONFIRMED_FAILURE_SAFE_TO_RETRY permits retry;
- deterministic Scene-aware Android fixture E2E reaches READY_TO_PUBLISH and confirmed ledger without a physical phone;
- destructive-transition ambiguity returns NEEDS_HUMAN;
- full deterministic Program 1 -> 2 -> 3 closed-loop contract PASS.

Remaining production-evidence limits:
- real Shopee Android Scene catalog/signatures/selectors;
- safe-anchor paths;
- basket capacity by supported app/account/version;
- real publish-success/reconciliation evidence;
- pacing/recovery budgets and multi-device capacity benchmarks.

## Latest authoritative verification evidence

Verification workflow: GitHub Actions CI run `33926893965` / round 4.

Results:
- Ruff: PASS
- Program 1 conformance: PASS
- Program 2 conformance: PASS
- Program 3 conformance: PASS (16 required control files)
- Core + contract tests: **263 passed**
- Core branch coverage: **95.06%**
- SQLite/Alembic integration: **57 passed**
- SQLite branch coverage: **96.24%**
- Program 1 extension: **82/82 passed**
- Stress suite: PASS
- Deterministic cross-program Program 1 -> 2 -> 3 E2E: PASS

## Completion conclusion

Programs 1–3 satisfy the requested >=90 engineering maturity target.

Program 2 and Program 3 also satisfy the >=95 stretch target.

The next lifecycle phase is **controlled production-evidence validation**, not basic architecture completion. Production evidence must promote individual profiles/policies/adapters without weakening the fail-closed engineering baseline.
