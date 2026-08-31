from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductObservation(BaseModel):
    observation_id: str
    platform: str
    shop_id: str
    item_id: str
    collected_at: datetime
    product_name: str
    product_url: str | None = None
    price_current: Decimal | None = None
    sold_signal: int | None = Field(default=None, ge=0)
    rating: float | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    source_worker_id: str | None = None
    source_query: str | None = None
    extractor_version: str | None = None

    @property
    def canonical_key(self) -> tuple[str, str, str]:
        return (self.platform, self.shop_id, self.item_id)


class ProductScore(BaseModel):
    product_key: tuple[str, str, str]
    total_score: float
    component_scores: dict[str, float]
    reasons: list[str]
    model_version: str


class ShortlistEntry(BaseModel):
    product_key: tuple[str, str, str]
    score: float
    rank: int
    reasons: list[str]
    model_version: str
