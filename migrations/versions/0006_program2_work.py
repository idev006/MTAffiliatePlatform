"""program2 work package and offer provenance

Revision ID: 0006_program2_work
Revises: 0005_program1_opportunity
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_program2_work"
down_revision: str | None = "0005_program1_opportunity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "program2_work",
        sa.Column("reference", sa.String(length=1024), primary_key=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("package_json", sa.String(length=32768), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.add_column(
        "affiliate_offer_observations",
        sa.Column("session_context_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "affiliate_offer_observations",
        sa.Column("source_worker_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "affiliate_offer_observations",
        sa.Column("source_job_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "affiliate_offer_observations",
        sa.Column("extractor_version", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_affiliate_offer_observations_source_worker_id",
        "affiliate_offer_observations",
        ["source_worker_id"],
    )
    op.create_index(
        "ix_affiliate_offer_observations_source_job_id",
        "affiliate_offer_observations",
        ["source_job_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_affiliate_offer_observations_source_job_id",
        table_name="affiliate_offer_observations",
    )
    op.drop_index(
        "ix_affiliate_offer_observations_source_worker_id",
        table_name="affiliate_offer_observations",
    )
    op.drop_column("affiliate_offer_observations", "extractor_version")
    op.drop_column("affiliate_offer_observations", "source_job_id")
    op.drop_column("affiliate_offer_observations", "source_worker_id")
    op.drop_column("affiliate_offer_observations", "session_context_id")
    op.drop_table("program2_work")
