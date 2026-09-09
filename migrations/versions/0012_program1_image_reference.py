"""Program 1 optional observed primary image reference."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_program1_image_reference"
down_revision: str | None = "0011_program3_devices"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("product_observations", sa.Column("primary_image_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("product_observations", "primary_image_url")
