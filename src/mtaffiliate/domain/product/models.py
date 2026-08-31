from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductObservation(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    observation_id: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    shop_id: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    collected_at: datetime
    product_name: str = Field(min_length=1)
    product_url: str | None = None
    price_current: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    sold_signal: int | None = Field(default=None, ge=0)
    rating: float | None = Field(default=None, ge=0, le=5, allow_inf_nan=False)
    review_count: int | None = Field(default=None, ge=0)
    source_worker_id: str | None = None
    source_query: str | None = None
    extractor_version: str | None = None

    @property
    def canonical_key(self) -> tuple[str, str, str]:
        return (self.platform, self.shop_id, self.item_id)


class ProductScore(BaseModel):
    product_key: tuple[str, str, str]
    total_score: float = Field(ge=0, le=100, allow_inf_nan=False)
    component_scores: dict[str, float]
    reasons: list[str]
    model_version: str


class ShortlistEntry(BaseModel):
    product_key: tuple[str, str, str]
    score: float = Field(ge=0, le=100, allow_inf_nan=False)
    rank: int = Field(ge=1)
    reasons: list[str]
    model_version: str
