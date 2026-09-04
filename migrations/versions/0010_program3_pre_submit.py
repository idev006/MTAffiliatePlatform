"""program3 authoritative pre-submit decisions

Revision ID: 0010_program3_pre_submit
Revises: 0009_program3_authority
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_program3_pre_submit"
down_revision: str | None = "0009_program3_authority"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "program3_pre_submit_decisions",
        sa.Column("decision_id", sa.String(length=128), primary_key=True),
        sa.Column("publish_job_id", sa.String(length=128), nullable=False),
        sa.Column("decision_json", sa.String(length=16384), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_program3_pre_submit_decisions_publish_job_id",
        "program3_pre_submit_decisions",
        ["publish_job_id"],
    )
    op.create_index(
        "ix_program3_pre_submit_decisions_evaluated_at",
        "program3_pre_submit_decisions",
        ["evaluated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_program3_pre_submit_decisions_evaluated_at",
        table_name="program3_pre_submit_decisions",
    )
    op.drop_index(
        "ix_program3_pre_submit_decisions_publish_job_id",
        table_name="program3_pre_submit_decisions",
    )
    op.drop_table("program3_pre_submit_decisions")
