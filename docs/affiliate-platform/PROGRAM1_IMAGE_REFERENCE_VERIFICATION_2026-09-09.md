# P1-IMG-1 verification — 2026-09-09

Implemented optional primary_image_url validation, nullable migration 0012, both SQLite persistence mappings, compatible legacy batch hashes, and bounded newest-first observation history API. No download or Shopee image selector was added; existing rows remain null. Running Back Office process has not been restarted onto this change yet.

Local full pipeline runtime/verification/20260909T051813Z-aab248a2/report.json: static PASS, core 296 passed/95.06%, SQLite 60 passed + 1 skipped/96.24%, stress 1 passed, extension 105 passed/build PASS. Browser initially failed because project package was not installed in the approved .venv. Repaired via python -m pip install -e . --no-deps. Browser-only rerun runtime/verification/20260909T052113Z-0901ac57/report.json reaches Playwright startup but fails locally; CI remains the browser execution gate. Full local result is not green.

Migration test upgrades a populated previous schema and verifies original observation/receipt values unchanged. Restart test checks actual image URL readback, duplicate-only ACK, original receipt replay and changed-image conflicts. API tests check newest-first bounded readback, absent product, invalid limits and Program1-only routing. Unit tests verify accepted/missing/rejected URLs and byte-compatible old fingerprint calculation.

Team reviewed the contract and recommended staged progress: trustworthy acquisition/evidence, operator review/recovery, then explainable opportunity decisions. Kanban, data model, application contract and traceability updated. Pending: CI, live image association evidence, fixture-backed extraction, image artifact lifecycle, operator image review UI. No production readiness claim.

CI code commit fde439ecc922730538bfe116ab37f5d07f35b933: PASS, run https://github.com/idev006/MTAffiliatePlatform/actions/runs/34314604811 (including Chromium). Draft PR #44. Storage/API foundation verified; live image extraction is not implemented or claimed.
