"""program3 durable plans submissions reconciliation

Revision ID: 0009_program3_authority
Revises: 0008_program2_artifact
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_program3_authority"
down_revision: str | None = "0008_program2_artifact"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "program3_plans",
        sa.Column("plan_ref", sa.String(length=1024), primary_key=True),
        sa.Column("publish_job_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("package_json", sa.String(length=32768), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_program3_plans_publish_job_id", "program3_plans", ["publish_job_id"])

    op.create_table(
        "program3_submissions",
        sa.Column("submission_id", sa.String(length=128), primary_key=True),
        sa.Column("publish_job_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("record_json", sa.String(length=16384), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_program3_submissions_publish_job_id",
        "program3_submissions",
        ["publish_job_id"],
    )

    op.create_table(
        "program3_reconciliations",
        sa.Column("reconciliation_id", sa.String(length=128), primary_key=True),
        sa.Column("submission_id", sa.String(length=128), nullable=False),
        sa.Column("decision_json", sa.String(length=16384), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_program3_reconciliations_submission_id",
        "program3_reconciliations",
        ["submission_id"],
    )
    op.create_index(
        "ix_program3_reconciliations_evaluated_at",
        "program3_reconciliations",
        ["evaluated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_program3_reconciliations_evaluated_at",
        table_name="program3_reconciliations",
    )
    op.drop_index(
        "ix_program3_reconciliations_submission_id",
        table_name="program3_reconciliations",
    )
    op.drop_table("program3_reconciliations")
    op.drop_index(
        "ix_program3_submissions_publish_job_id",
        table_name="program3_submissions",
    )
    op.drop_table("program3_submissions")
    op.drop_index("ix_program3_plans_publish_job_id", table_name="program3_plans")
    op.drop_table("program3_plans")
