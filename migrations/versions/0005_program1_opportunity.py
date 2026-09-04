"""program1 opportunity provenance and decisions

Revision ID: 0005_program1_opportunity
Revises: 0004_shared_jobs
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_program1_opportunity"
down_revision: str | None = "0004_shared_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "product_observations",
        sa.Column("source_job_id", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_product_observations_source_job_id",
        "product_observations",
        ["source_job_id"],
    )

    op.create_table(
        "program1_opportunity_decisions",
        sa.Column("decision_id", sa.String(length=128), primary_key=True),
        sa.Column("campaign_id", sa.String(length=128), nullable=False),
        sa.Column("hypothesis_id", sa.String(length=128), nullable=False),
        sa.Column("source_job_id", sa.String(length=128), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("shop_id", sa.String(length=128), nullable=False),
        sa.Column("item_id", sa.String(length=128), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recommended_action", sa.String(length=32), nullable=False),
        sa.Column("feature_policy_version", sa.String(length=128), nullable=False),
        sa.Column("qualification_policy_version", sa.String(length=128), nullable=False),
        sa.Column("evidence_state", sa.String(length=32), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("thesis_json", sa.String(length=32768), nullable=False),
    )
    for name, column in (
        ("ix_program1_opportunity_decisions_campaign_id", "campaign_id"),
        ("ix_program1_opportunity_decisions_hypothesis_id", "hypothesis_id"),
        ("ix_program1_opportunity_decisions_source_job_id", "source_job_id"),
        ("ix_program1_opportunity_decisions_platform", "platform"),
        ("ix_program1_opportunity_decisions_shop_id", "shop_id"),
        ("ix_program1_opportunity_decisions_item_id", "item_id"),
        ("ix_program1_opportunity_decisions_evaluated_at", "evaluated_at"),
        ("ix_program1_opportunity_decisions_recommended_action", "recommended_action"),
    ):
        op.create_index(name, "program1_opportunity_decisions", [column])


def downgrade() -> None:
    for name in (
        "ix_program1_opportunity_decisions_recommended_action",
        "ix_program1_opportunity_decisions_evaluated_at",
        "ix_program1_opportunity_decisions_item_id",
        "ix_program1_opportunity_decisions_shop_id",
        "ix_program1_opportunity_decisions_platform",
        "ix_program1_opportunity_decisions_source_job_id",
        "ix_program1_opportunity_decisions_hypothesis_id",
        "ix_program1_opportunity_decisions_campaign_id",
    ):
        op.drop_index(name, table_name="program1_opportunity_decisions")
    op.drop_table("program1_opportunity_decisions")

    op.drop_index("ix_product_observations_source_job_id", table_name="product_observations")
    op.drop_column("product_observations", "source_job_id")
