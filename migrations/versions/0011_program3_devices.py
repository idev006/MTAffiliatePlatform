"""program3 durable device ownership

Revision ID: 0011_program3_devices
Revises: 0010_program3_pre_submit
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_program3_devices"
down_revision: str | None = "0010_program3_pre_submit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "program3_devices",
        sa.Column("device_id", sa.String(length=128), primary_key=True),
        sa.Column("adb_serial", sa.String(length=256), nullable=False, unique=True),
        sa.Column("host_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("worker_id", sa.String(length=128), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False),
    )
    op.create_index("ix_program3_devices_host_id", "program3_devices", ["host_id"])
    op.create_index("ix_program3_devices_status", "program3_devices", ["status"])
    op.create_index("ix_program3_devices_worker_id", "program3_devices", ["worker_id"])
    op.create_index(
        "ix_program3_devices_lease_expires_at",
        "program3_devices",
        ["lease_expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_program3_devices_lease_expires_at", table_name="program3_devices")
    op.drop_index("ix_program3_devices_worker_id", table_name="program3_devices")
    op.drop_index("ix_program3_devices_status", table_name="program3_devices")
    op.drop_index("ix_program3_devices_host_id", table_name="program3_devices")
    op.drop_table("program3_devices")
