"""program1 product observations

Revision ID: 0001_program1
Revises:
Create Date: 2026-08-31
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_program1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_observations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("observation_id", sa.String(length=128), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("shop_id", sa.String(length=128), nullable=False),
        sa.Column("item_id", sa.String(length=128), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("product_name", sa.String(length=1024), nullable=False),
        sa.Column("product_url", sa.String(length=4096), nullable=True),
        sa.Column("price_current", sa.Numeric(20, 4), nullable=True),
        sa.Column("sold_signal", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("source_worker_id", sa.String(length=128), nullable=True),
        sa.Column("source_query", sa.String(length=1024), nullable=True),
        sa.Column("extractor_version", sa.String(length=128), nullable=True),
        sa.UniqueConstraint("observation_id", name="uq_product_observation_id"),
    )
    op.create_index("ix_product_observations_platform", "product_observations", ["platform"])
    op.create_index("ix_product_observations_shop_id", "product_observations", ["shop_id"])
    op.create_index("ix_product_observations_item_id", "product_observations", ["item_id"])
    op.create_index("ix_product_observations_collected_at", "product_observations", ["collected_at"])


def downgrade() -> None:
    op.drop_index("ix_product_observations_collected_at", table_name="product_observations")
    op.drop_index("ix_product_observations_item_id", table_name="product_observations")
    op.drop_index("ix_product_observations_shop_id", table_name="product_observations")
    op.drop_index("ix_product_observations_platform", table_name="product_observations")
    op.drop_table("product_observations")
