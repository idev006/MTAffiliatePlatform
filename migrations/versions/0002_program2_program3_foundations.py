"""program2 and program3 foundations

Revision ID: 0002_program2_program3
Revises: 0001_program1
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_program2_program3"
down_revision: str | None = "0001_program1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "affiliate_offer_observations",
        sa.Column("observation_id", sa.String(length=128), primary_key=True),
        sa.Column("offer_id", sa.String(length=128), nullable=False),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("shop_id", sa.String(length=128), nullable=False),
        sa.Column("item_id", sa.String(length=128), nullable=False),
        sa.Column("affiliate_account_id", sa.String(length=128), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("seller_name", sa.String(length=1024)),
        sa.Column("product_name", sa.String(length=1024), nullable=False),
        sa.Column("price_current", sa.Numeric(20, 4)),
        sa.Column("commission_rate", sa.Float()),
        sa.Column("extra_commission_rate", sa.Float()),
        sa.Column("rating", sa.Float()),
        sa.Column("review_count", sa.Integer()),
        sa.Column("sold_signal", sa.Integer()),
        sa.Column("available", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_offer_obs_offer", "affiliate_offer_observations", ["offer_id"])
    op.create_index("ix_offer_obs_product", "affiliate_offer_observations", ["product_id"])
    op.create_index(
        "ix_offer_obs_account",
        "affiliate_offer_observations",
        ["affiliate_account_id"],
    )

    op.create_table(
        "affiliate_offer_selections",
        sa.Column("selection_id", sa.String(length=128), primary_key=True),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("preferred_offer_id", sa.String(length=128), nullable=False),
        sa.Column("backup_offer_ids", sa.String(length=4096), nullable=False),
        sa.Column("affiliate_account_id", sa.String(length=128), nullable=False),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_version", sa.String(length=128), nullable=False),
    )
    op.create_index("ix_offer_selection_product", "affiliate_offer_selections", ["product_id"])

    op.create_table(
        "publishing_ledger",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("publish_job_id", sa.String(length=128), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("target_account_id", sa.String(length=128), nullable=False),
        sa.Column("video_id", sa.String(length=128), nullable=False),
        sa.Column("video_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_publish_job", "publishing_ledger", ["publish_job_id"])
    op.create_index("ix_publish_platform", "publishing_ledger", ["platform"])
    op.create_index("ix_publish_video", "publishing_ledger", ["video_id"])
    op.create_index("ix_publish_hash", "publishing_ledger", ["video_sha256"])


def downgrade() -> None:
    op.drop_index("ix_publish_hash", table_name="publishing_ledger")
    op.drop_index("ix_publish_video", table_name="publishing_ledger")
    op.drop_index("ix_publish_platform", table_name="publishing_ledger")
    op.drop_index("ix_publish_job", table_name="publishing_ledger")
    op.drop_table("publishing_ledger")
    op.drop_index("ix_offer_selection_product", table_name="affiliate_offer_selections")
    op.drop_table("affiliate_offer_selections")
    op.drop_index("ix_offer_obs_account", table_name="affiliate_offer_observations")
    op.drop_index("ix_offer_obs_product", table_name="affiliate_offer_observations")
    op.drop_index("ix_offer_obs_offer", table_name="affiliate_offer_observations")
    op.drop_table("affiliate_offer_observations")
