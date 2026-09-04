# Program 1 Evidence Capture Hardening Verification — Round 2

R1 finding: tests imported a helper from `tools/`, which is not an installed package boundary.

CAPA:
- pure evidence policy moved to `mtaffiliate.common.evidence`;
- capture script and tests use the installed package helper;
- duplicate helper removed.

Acceptance: all repository CI gates PASS.