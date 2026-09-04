"""program2 affiliate link artifacts

Revision ID: 0008_program2_artifact
Revises: 0007_program2_decision
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_program2_artifact"
down_revision: str | None = "0007_program2_decision"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "program2_link_artifacts",
        sa.Column("artifact_id", sa.String(length=128), primary_key=True),
        sa.Column("selection_decision_id", sa.String(length=128), nullable=False),
        sa.Column("source_job_id", sa.String(length=128), nullable=False),
        sa.Column("affiliate_account_id", sa.String(length=128), nullable=False),
        sa.Column("offer_id", sa.String(length=128), nullable=False),
        sa.Column("link_url", sa.String(length=4096), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validation_state", sa.String(length=32), nullable=False),
        sa.Column("evidence_refs", sa.String(length=8192), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
    )
    for name, column in (
        ("ix_program2_link_artifacts_selection_decision_id", "selection_decision_id"),
        ("ix_program2_link_artifacts_source_job_id", "source_job_id"),
        ("ix_program2_link_artifacts_affiliate_account_id", "affiliate_account_id"),
        ("ix_program2_link_artifacts_offer_id", "offer_id"),
        ("ix_program2_link_artifacts_validation_state", "validation_state"),
    ):
        op.create_index(name, "program2_link_artifacts", [column])


def downgrade() -> None:
    for name in (
        "ix_program2_link_artifacts_validation_state",
        "ix_program2_link_artifacts_offer_id",
        "ix_program2_link_artifacts_affiliate_account_id",
        "ix_program2_link_artifacts_source_job_id",
        "ix_program2_link_artifacts_selection_decision_id",
    ):
        op.drop_index(name, table_name="program2_link_artifacts")
    op.drop_table("program2_link_artifacts")
