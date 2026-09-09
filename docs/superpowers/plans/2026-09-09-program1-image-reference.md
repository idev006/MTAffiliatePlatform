# Program 1 Image Reference Implementation Plan

**Goal:** Preserve optional primary image references durably without breaking old observation receipts.
**Architecture:** Domain evidence -> existing application ingestion -> ports -> SQLite; no network during ingestion. Shopee extraction remains evidence-gated.
**Tech Stack:** Python 3.12 virtual environment, Pydantic, SQLAlchemy, Alembic, pytest.

- [ ] Review contract and current CI; identify image provenance and compatibility risks.
- [ ] Add domain validation and nullable migration; update both persistence mappings.
- [ ] Preserve legacy fingerprints and test receipt replay across image changes/restart.
- [ ] Inspect stored image evidence through existing query boundary or bounded read endpoint.
- [ ] Run narrow tests, shared pipeline and CI; update Kanban and verification with remaining gates.

Follow PROGRAM1_IMAGE_REFERENCE_CONTRACT.md. User authorized team implementation in the current checkout; no additional planning approval is needed.
