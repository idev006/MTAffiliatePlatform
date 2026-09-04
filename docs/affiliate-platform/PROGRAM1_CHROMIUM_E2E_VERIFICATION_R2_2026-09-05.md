# Program 1 Chromium E2E Verification — Round 2

R1 finding: persistent state and startup reconcile/renew succeeded, but relying on Chromium alarm delivery timing for post-restart completion made the CI test nondeterministic.

CAPA:
- continue requiring real browser restart and `onStartup` reconcile/renew;
- verify recovered active job and desired run state before continuing;
- drive the same bounded background-cycle command used by alarm wakeups deterministically after recovery;
- emit full status/backend lineage on failure.

No lease, ACK, durability, duplicate, completion or safety assertion is removed.