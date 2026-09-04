# Program 2 — UX and Operator Experience

Status: DESIGN BASELINE
Date: 2026-09-04

## UX principle

A novice operator should understand:
- what product opportunity is being processed;
- which affiliate account/session is active;
- what stage the worker is in;
- whether evidence is fresh;
- preferred offer and backups;
- why that selection was made;
- whether intervention is required.

## UI is not authority

UI may:
- start/stop/request commands;
- display jobs/health/outbox;
- show offer comparison/explanations;
- request human takeover;
- show freshness/risk.

UI may not:
- calculate final ranking;
- mutate canonical selection directly;
- invent missing evidence;
- hide failed/ambiguous export as success.

## Progressive disclosure

Default view:
- status;
- current product;
- account;
- preferred offer;
- freshness;
- actionable warning.

Advanced view:
- all candidates;
- evidence refs;
- component facts;
- worker/job/lease;
- policy versions;
- raw safe diagnostics.

## Error language

Prefer actionable states:
- Session required
- Page changed — collection stopped safely
- Offer evidence stale — refresh required
- Export result unknown — review required
- Back Office unreachable — data retained locally

Do not expose stack traces as the primary operator message.
