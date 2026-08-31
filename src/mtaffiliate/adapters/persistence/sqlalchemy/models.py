from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ProductObservationRow(Base):
    __tablename__ = "product_observations"
    __table_args__ = (UniqueConstraint("observation_id", name="uq_product_observation_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    shop_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(1024), nullable=False)
    product_url: Mapped[str | None] = mapped_column(String(4096))
    price_current: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    sold_signal: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[float | None]
    review_count: Mapped[int | None] = mapped_column(Integer)
    source_worker_id: Mapped[str | None] = mapped_column(String(128))
    source_query: Mapped[str | None] = mapped_column(String(1024))
    extractor_version: Mapped[str | None] = mapped_column(String(128))
