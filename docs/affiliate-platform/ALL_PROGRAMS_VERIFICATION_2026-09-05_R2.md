# Programs 1–3 Maturity Verification — Round 2

CAPA since R1:
- deterministic Android-to-ledger Program 3 E2E;
- durable device registry and optimistic ownership leases;
- pre-submit now requires active job lease and active device ownership;
- SQLite device restart/conflict coverage;
- Program 3 device authority added to CI coverage and conformance.

Acceptance: Ruff + Program1/2/3 conformance + core >=95% + SQLite >=95% + stress + extension all PASS.