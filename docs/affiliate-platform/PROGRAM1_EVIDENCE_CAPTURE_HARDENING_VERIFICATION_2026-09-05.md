# Program 1 Evidence Capture Hardening Verification

Scope:
- structural sanitization before HTML evidence is written;
- sensitive runtime values are excluded from persisted evidence;
- evidence-relevant URL sanitization;
- SHA-256 evidence manifest;
- explicit capture classification and HOLD/BLOCK promotion decision;
- verification pages fail closed by default;
- optional human verification wait is explicit.

Acceptance: all repository CI gates PASS.