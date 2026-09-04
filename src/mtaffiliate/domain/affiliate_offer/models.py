from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AffiliateAccountContext(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    affiliate_account_id: str = Field(min_length=1)
    session_context_id: str | None = None


class AffiliateOfferObservation(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    observation_id: str = Field(min_length=1)
    offer_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    shop_id: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    affiliate_account_id: str = Field(min_length=1)
    observed_at: datetime
    seller_name: str | None = None
    product_name: str = Field(min_length=1)
    price_current: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    commission_rate: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    extra_commission_rate: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    rating: float | None = Field(default=None, ge=0, le=5, allow_inf_nan=False)
    review_count: int | None = Field(default=None, ge=0)
    sold_signal: int | None = Field(default=None, ge=0)
    available: bool = True

    @property
    def commercial_key(self) -> tuple[str, str, str, str, str]:
        return (
            self.platform,
            self.shop_id,
            self.item_id,
            self.offer_id,
            self.affiliate_account_id,
        )


class OfferScore(BaseModel):
    commercial_key: tuple[str, str, str, str, str]
    total_score: float = Field(ge=0, le=100, allow_inf_nan=False)
    component_scores: dict[str, float]
    reasons: list[str]
    model_version: str


class OfferSelection(BaseModel):
    selection_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    preferred_offer_id: str = Field(min_length=1)
    backup_offer_ids: list[str] = Field(default_factory=list)
    affiliate_account_id: str = Field(min_length=1)
    selected_at: datetime
    model_version: str = Field(min_length=1)


class OfferDiscoveryPlan(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    plan_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    source_program1_decision_id: str = Field(min_length=1)
    product_key: tuple[str, str, str]
    product_name: str = Field(min_length=1)
    affiliate_account_id: str = Field(min_length=1)
    collection_targets: tuple[str, ...] = ()
    capability_requirements: tuple[str, ...] = ()
    evidence_policy_version: str = Field(min_length=1)
    collection_policy_version: str = Field(min_length=1)
    created_at: datetime


class OfferDiscoveryWorkPackage(BaseModel):
    model_config = ConfigDict(frozen=True)

    upstream_handoff_id: str = Field(min_length=1)
    upstream_decision_id: str = Field(min_length=1)
    upstream_source_job_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    product_key: tuple[str, str, str]
    product_name: str = Field(min_length=1)
    affiliate_account_id: str = Field(min_length=1)
    discovery_plan: OfferDiscoveryPlan
