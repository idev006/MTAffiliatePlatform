"""shared job engine durable state

Revision ID: 0004_shared_jobs
Revises: 0003_shared_core_workers
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_shared_jobs"
down_revision: str | None = "0003_shared_core_workers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "program1_strategy_work",
        sa.Column("reference", sa.String(length=1024), primary_key=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("package_json", sa.String(length=32768), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "jobs",
        sa.Column("job_id", sa.String(length=128), primary_key=True),
        sa.Column("job_type", sa.String(length=128), nullable=False),
        sa.Column("domain", sa.String(length=64), nullable=False),
        sa.Column("payload_ref", sa.String(length=1024), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=256), nullable=False),
        sa.Column("capability_requirements", sa.String(length=4096), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("job_version", sa.Integer(), nullable=False),
        sa.Column("assigned_worker_id", sa.String(length=128), nullable=True),
        sa.Column("lease_token", sa.String(length=256), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("checkpoint_json", sa.String(length=16384), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failure_code", sa.String(length=128), nullable=True),
        sa.Column("failure_detail", sa.String(length=4096), nullable=True),
        sa.UniqueConstraint("idempotency_key", name="uq_jobs_idempotency_key"),
    )
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"])
    op.create_index("ix_jobs_domain", "jobs", ["domain"])
    op.create_index("ix_jobs_state", "jobs", ["state"])
    op.create_index("ix_jobs_assigned_worker_id", "jobs", ["assigned_worker_id"])
    op.create_index("ix_jobs_lease_until", "jobs", ["lease_until"])

    op.create_table(
        "job_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "job_id",
            sa.String(length=128),
            sa.ForeignKey("jobs.job_id"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("job_version", sa.Integer(), nullable=False),
        sa.Column("emitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("worker_id", sa.String(length=128), nullable=True),
        sa.Column("detail", sa.String(length=4096), nullable=True),
        sa.UniqueConstraint(
            "job_id",
            "job_version",
            name="uq_job_events_job_version",
        ),
    )
    op.create_index("ix_job_events_job_id", "job_events", ["job_id"])
    op.create_index("ix_job_events_event_type", "job_events", ["event_type"])
    op.create_index("ix_job_events_worker_id", "job_events", ["worker_id"])


def downgrade() -> None:
    op.drop_index("ix_job_events_worker_id", table_name="job_events")
    op.drop_index("ix_job_events_event_type", table_name="job_events")
    op.drop_index("ix_job_events_job_id", table_name="job_events")
    op.drop_table("job_events")

    op.drop_index("ix_jobs_lease_until", table_name="jobs")
    op.drop_index("ix_jobs_assigned_worker_id", table_name="jobs")
    op.drop_index("ix_jobs_state", table_name="jobs")
    op.drop_index("ix_jobs_domain", table_name="jobs")
    op.drop_index("ix_jobs_job_type", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("program1_strategy_work")
