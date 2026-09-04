# Program 1 World-Class Simulation CI

Date: 2026-09-04
Status: VERIFICATION ROUND 2

Round 1:
- Program 1 extension: PASS
- Back Office stress: PASS
- SQLite/Alembic integration: PASS
- Back Office core: FAIL at Ruff only

CAPA:
- canonicalized Ruff import ordering;
- removed unused simulation unpack;
- no test/coverage/lint thresholds weakened.

Round 2 release rule:
All CI jobs must pass. A green simulation baseline still does not waive real-browser/MV3-restart and real-Shopee evidence gates.
