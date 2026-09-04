# Program 1 World-Class Simulation Verification

Date: 2026-09-04
Status: CI VERIFICATION REQUESTED

Verification objective:
Prove Program 1 behavior through deterministic, headless, restart-safe simulation rather than UI-only observation.

Simulation covers:
- affiliate strategy hypothesis and explicit signals;
- approved DiscoveryPlan;
- durable strategy-work package;
- durable Shared Job creation and idempotency;
- authoritative Worker Registry capabilities;
- deterministic compatible lease selection;
- job start and active lease ownership;
- synthetic product collection;
- atomic ingestion batch identity/ACK behavior;
- durable checkpoint;
- deterministic Product Intelligence shortlist;
- VERIFYING -> COMPLETED transition;
- full process/database recomposition after restart;
- persisted job state/event history/checkpoint;
- persisted strategy package;
- persisted observations and identical shortlist after restart;
- duplicate batch replay;
- batch-id collision with changed payload;
- expired unsafe execution -> NEEDS_HUMAN;
- stale worker mutation rejection;
- duplicate job request without duplicate work.

Synthetic marketplace facts are deliberately used. This verification does not claim real Shopee DOM/selector or marketplace-policy evidence.

Release rule:
Program 1 is not considered production-ready unless CI passes and remaining browser-background-worker / real-evidence gates are closed.
