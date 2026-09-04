"""program2 durable selection decisions

Revision ID: 0007_program2_decision
Revises: 0006_program2_work
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_program2_decision"
down_revision: str | None = "0006_program2_work"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "program2_selection_decisions",
        sa.Column("decision_id", sa.String(length=128), primary_key=True),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("affiliate_account_id", sa.String(length=128), nullable=False),
        sa.Column("source_job_id", sa.String(length=128), nullable=False),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("preferred_offer_id", sa.String(length=128), nullable=False),
        sa.Column("backup_offer_ids", sa.String(length=4096), nullable=False),
        sa.Column("preferred_commercial_key", sa.String(length=4096), nullable=False),
        sa.Column("evidence_refs", sa.String(length=8192), nullable=False),
        sa.Column("feature_policy_version", sa.String(length=128), nullable=False),
        sa.Column("qualification_policy_version", sa.String(length=128), nullable=False),
        sa.Column("decision_policy_version", sa.String(length=128), nullable=False),
        sa.Column("reasons", sa.String(length=8192), nullable=False),
        sa.Column("risks", sa.String(length=8192), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
    )
    for name, column in (
        ("ix_program2_selection_decisions_product_id", "product_id"),
        ("ix_program2_selection_decisions_affiliate_account_id", "affiliate_account_id"),
        ("ix_program2_selection_decisions_source_job_id", "source_job_id"),
        ("ix_program2_selection_decisions_selected_at", "selected_at"),
    ):
        op.create_index(name, "program2_selection_decisions", [column])


def downgrade() -> None:
    for name in (
        "ix_program2_selection_decisions_selected_at",
        "ix_program2_selection_decisions_source_job_id",
        "ix_program2_selection_decisions_affiliate_account_id",
        "ix_program2_selection_decisions_product_id",
    ):
        op.drop_index(name, table_name="program2_selection_decisions")
    op.drop_table("program2_selection_decisions")
