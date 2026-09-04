# Program 1 P0-A Background Execution Verification

Scope:
- DiscoveryPlan durable collection_targets;
- MV3 alarm-driven background execution controller;
- Side Panel command-only Start/Stop;
- page-load/retry/next-cycle alarm wakeups;
- durable run state and active job;
- ACK checkpoint and last-page completion;
- background execution conformance checks;
- extension version 0.1.24.

Acceptance: all CI jobs green; no quality gate weakened.