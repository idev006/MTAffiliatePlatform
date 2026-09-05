# Production Evidence Promotion Matrix

Status: ACTIVE SSOT
Date: 2026-09-05

| ID | Program | Evidence target | Current stage | Required next evidence | Promotion blocker |
|---|---|---|---|---|---|
| P1-E01 | Program 1 | `shopee-search-lab-v1` Search profile | LAB_VALIDATED | fresh authorized evidence campaign: >=2 independent captures, negative evidence, field boundaries, fixtures/tests | `NEEDS_REAL_DATA`; prior cached/public retrieval is non-promotional |
| P1-E02 | Program 1 | Category result profile | LAB_VALIDATED | second independent category capture + hydration behavior | insufficient repeat evidence |
| P1-E03 | Program 1 | Shop result profile | LAB_VALIDATED | second independent shop capture + identity/name/price boundaries | insufficient repeat evidence |
| P1-E04 | Program 1 | Product detail profile | LAB_VALIDATED | second independent PDP capture + identity/price/sold/rating field semantics | insufficient repeat evidence |
| P1-E05 | Program 1 | Product identity `(platform, shop_id, item_id)` | PRODUCTION_CANDIDATE | independent repeated live identity evidence across surfaces/sessions | pending broader repeated evidence |
| P2-E01 | Program 2 | Real affiliate offer identity | LAB_VALIDATED | repeated account-bound offer captures | account/session evidence incomplete |
| P2-E02 | Program 2 | Commission field semantics | LAB_VALIDATED | repeated same-offer field evidence + ambiguity cases | live field semantics not fully frozen |
| P2-E03 | Program 2 | Affiliate account/session provenance | LAB_VALIDATED | controlled session restart/login evidence | repeatability incomplete |
| P2-E04 | Program 2 | Export/link artifact semantics | LAB_VALIDATED | controlled export + lost/ambiguous outcome evidence | real export reconciliation incomplete |
| P3-E01 | Program 3 | Shopee Android Scene catalog | EXPERIMENTAL | sanitized real-device Scene evidence per supported app/version | real device/app evidence required |
| P3-E02 | Program 3 | Semantic selector profiles | EXPERIMENTAL | repeated Scene element evidence | real device/app evidence required |
| P3-E03 | Program 3 | Safe Anchor | EXPERIMENTAL | controlled recovery evidence from known failure states | not yet validated |
| P3-E04 | Program 3 | Basket capacity | EXPERIMENTAL | controlled account/app/version observation | must not be guessed |
| P3-E05 | Program 3 | Publish success/reconciliation evidence | EXPERIMENTAL | real controlled submit evidence + ambiguous outcome case | irreversible live action evidence required |
| P3-E06 | Program 3 | Recovery/pacing budgets | EXPERIMENTAL | endurance data | no numeric defaults without measurements |
| P3-E07 | Program 3 | Multi-device capacity | EXPERIMENTAL | controlled host/device benchmark | no scale claim without benchmark |

## Rules

- This matrix is the canonical promotion backlog for live-platform evidence.
- Promotion requires `CONTROLLED_PRODUCTION_EVIDENCE_VALIDATION_STANDARD.md`.
- Engineering maturity scores are not silently increased because a profile merely has one successful live capture.
- Any evidence target may be moved backward to STALE/BLOCKED if drift or ambiguity is observed.