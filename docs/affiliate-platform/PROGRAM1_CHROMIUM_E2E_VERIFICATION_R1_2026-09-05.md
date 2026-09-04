# Program 1 Chromium E2E Verification — Round 1

Scope: P1-H real Chromium MV3 restart/reconcile gate.

Verify:
- local deterministic fixture + mock Back Office only;
- unpacked extension service worker loads in Playwright Chromium;
- page 1 ACK/checkpoint occurs before browser restart;
- persistent profile recovers active job/run state;
- startup reconcile/renew occurs;
- stale tab is safely recreated;
- page 2 completes same job;
- exactly two observation batches and two checkpoints;
- no UI click and no live Shopee dependency.

Acceptance: new browser E2E job and all existing CI gates PASS.