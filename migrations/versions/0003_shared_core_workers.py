"""shared core worker registry baseline

Revision ID: 0003_shared_core_workers
Revises: 0002_program2_program3
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_shared_core_workers"
down_revision: str | None = "0002_program2_program3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workers",
        sa.Column("worker_id", sa.String(length=128), primary_key=True),
        sa.Column("worker_type", sa.String(length=64), nullable=False),
        sa.Column("installation_id", sa.String(length=128), nullable=False),
        sa.Column("host_id", sa.String(length=128), nullable=True),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("capabilities", sa.String(length=4096), nullable=False),
        sa.Column("health_state", sa.String(length=32), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
    )
    op.create_index("ix_workers_worker_type", "workers", ["worker_type"])
    op.create_index("ix_workers_installation_id", "workers", ["installation_id"])


def downgrade() -> None:
    op.drop_index("ix_workers_installation_id", table_name="workers")
    op.drop_index("ix_workers_worker_type", table_name="workers")
    op.drop_table("workers")
