# Controlled Production Evidence Validation Standard

Status: ACCEPTED PROCESS STANDARD
Date: 2026-09-05
Scope: Programs 1–3 live Shopee/browser/affiliate/Android evidence promotion.

## Purpose

This standard governs how a laboratory profile, selector set, field interpretation, Android Scene signature, reconciliation rule, timing/pacing policy or other live-platform assumption may be promoted.

It exists to prevent:
- one successful capture becoming a production assumption;
- silent platform drift;
- selection bias toward only successful observations;
- anti-bot/access-control bypass;
- test fixtures being mistaken for live evidence;
- architecture safeguards being weakened to accommodate unstable external behavior.

## Lifecycle

```text
EXPERIMENTAL
  -> LAB_VALIDATED
  -> EVIDENCE_VALIDATED
  -> PRODUCTION_CANDIDATE
  -> PRODUCTION_APPROVED

Any stage
  -> STALE
  -> DEPRECATED
  -> BLOCKED / NEEDS_REAL_DATA
```

## Promotion rules

### EXPERIMENTAL -> LAB_VALIDATED
Requires:
- deterministic fixture or controlled synthetic evidence;
- explicit owner/component/profile version;
- typed inputs/outputs;
- failure semantics;
- automated tests;
- no unresolved CRITICAL/HIGH design finding.

### LAB_VALIDATED -> EVIDENCE_VALIDATED
Requires all of:
1. at least two independent live captures;
2. captures differ by at least one meaningful dimension such as query/page/product/account/session/restart/time;
3. identity fields remain stable where expected;
4. candidate selectors/fields are supported by direct evidence, not inference;
5. negative/failure evidence is recorded;
6. blocked/anti-bot state is classified separately from empty/no-result state;
7. no CAPTCHA/access-control/anti-abuse bypass was used;
8. sanitized fixture derived from evidence exists when legally/operationally appropriate;
9. parser/recognizer contract tests cover the promoted behavior;
10. evidence provenance records date, surface, environment/profile version and limitations.

### EVIDENCE_VALIDATED -> PRODUCTION_CANDIDATE
Requires:
- repeatability across at least three independent sessions/runs or equivalent evidence set;
- restart/re-login or state-reset behavior where relevant;
- known failure classes and fail-closed behavior;
- drift detector or explicit profile mismatch behavior;
- bounded recovery/pacing policy;
- compatibility scope explicitly stated;
- integration/resilience test for the promoted profile;
- no CRITICAL/HIGH unresolved finding.

### PRODUCTION_CANDIDATE -> PRODUCTION_APPROVED
Requires:
- controlled endurance/operational run;
- observable error/health metrics;
- rollback/deprecation path;
- runbook/operator action for blocked/unknown states;
- evidence freshness reviewed;
- senior engineering/process/QA review;
- no silent fallback to heuristics outside approved profile.

## Evidence independence

Two captures are not independent if they are merely:
- repeated parsing of the same saved HTML/screenshot;
- the same page state without meaningful re-navigation/reload/session change;
- copied evidence derived from one original capture.

Independence should preferably vary:
- keyword/page/category/shop/PDP;
- login/session/browser restart;
- time;
- account where authorized and relevant;
- app version/device where Android behavior is relevant.

## Failure evidence requirement

Promotion requires recording not only what worked but also what happened when:
- target content was absent;
- page/scene was partially hydrated;
- session was logged out/expired;
- anti-bot/verification appeared;
- selector/signature matched more than one candidate;
- network/device state changed;
- post-submit outcome could not be proven.

Failure evidence must drive explicit states such as `BLOCKED`, `UNKNOWN`, `AMBIGUOUS`, `NEEDS_HUMAN`, or `NEEDS_REAL_DATA`.

## Safety / compliance

Forbidden:
- CAPTCHA solving automation or bypass;
- access-control circumvention;
- anti-bot evasion techniques;
- aggressive retry intended to defeat traffic gates;
- hiding automation identity through fingerprint manipulation;
- increasing concurrency before pacing/capacity evidence exists.

Human completion of an ordinary platform verification step may be recorded as evidence, but the system must not automate or bypass that boundary.

## Evidence artifact minimum fields

Every live evidence artifact records:
- evidence_id;
- date/time and timezone;
- program/surface/profile;
- platform/app/browser/device version when known;
- login/session context category (not secrets);
- collection method;
- observed identity;
- observed fields/signals;
- selectors/signatures tested;
- success/failure classification;
- blocked/verification state;
- sanitization notes;
- limitations;
- resulting promotion decision;
- linked tests/fixtures/code version.

## Promotion decision

A promotion decision is one of:
- PROMOTE;
- HOLD;
- BLOCK;
- STALE;
- DEPRECATE;
- NEEDS_REAL_DATA.

Absence of evidence means `NEEDS_REAL_DATA`, never implicit approval.

## Drift

Any of the following marks the affected profile/policy STALE until reviewed:
- parser mismatch rate exceeds expected controlled baseline;
- known identity selector no longer resolves;
- field meaning changes;
- page/scene structure becomes ambiguous;
- platform/app version changes in a way that affects signatures;
- anti-bot behavior invalidates normal observation assumptions;
- reconciliation evidence no longer proves outcome.

## Quality priority

Correctness > Recoverability > Traceability > Testability > Maintainability > Stable Throughput > Raw Speed.