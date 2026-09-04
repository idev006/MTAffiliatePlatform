# Program 1 World-Class Final Verification

Date: 2026-09-04

Applied CAPA:
- deterministic Program 1 headless simulation suite added;
- durable strategy-work payload added;
- Shared Job durable SQLite lifecycle verified;
- exact Ruff diagnostic enabled in CI;
- Ruff canonical patch applied exactly;
- no lint/test/coverage thresholds weakened.

Final acceptance gate:
All CI jobs must pass.

Important residual evidence gates remain:
- background extension must consume Shared Job lease/start/checkpoint lifecycle directly;
- MV3 service-worker restart/recovery must be verified end-to-end;
- real Shopee DOM/selectors/signals remain evidence-gated.
