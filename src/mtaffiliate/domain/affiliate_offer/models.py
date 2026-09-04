from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

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
    session_context_id: str | None = None
    source_worker_id: str | None = None
    source_job_id: str | None = None
    extractor_version: str | None = None
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


class OfferEvidenceState(StrEnum):
    SUFFICIENT_FOR_LAB = "SUFFICIENT_FOR_LAB"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
    STALE = "STALE"


class OfferQualificationState(StrEnum):
    QUALIFIED = "QUALIFIED"
    WATCH = "WATCH"
    HOLD = "HOLD"
    REJECTED = "REJECTED"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"


class OfferRecommendedAction(StrEnum):
    SELECT_NOW = "SELECT_NOW"
    WATCH = "WATCH"
    HOLD = "HOLD"
    REJECT = "REJECT"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"


class OfferFeatureSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    commercial_key: tuple[str, str, str, str, str]
    as_of: datetime
    feature_policy_version: str = Field(min_length=1)
    latest_observed_at: datetime
    observation_age_seconds: float = Field(ge=0)
    commission_total_rate: float | None = Field(default=None, ge=0, le=200)
    rating: float | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    sold_signal: int | None = Field(default=None, ge=0)
    price_current: Decimal | None = Field(default=None, ge=0)
    available: bool
    evidence_state: OfferEvidenceState
    unknown_features: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()


class OfferQualificationDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    commercial_key: tuple[str, str, str, str, str]
    state: OfferQualificationState
    recommended_action: OfferRecommendedAction
    policy_version: str = Field(min_length=1)
    reasons: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    evaluated_at: datetime


class OfferSelectionDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    affiliate_account_id: str = Field(min_length=1)
    source_job_id: str = Field(min_length=1)
    selected_at: datetime
    preferred_offer_id: str = Field(min_length=1)
    backup_offer_ids: tuple[str, ...] = ()
    preferred_commercial_key: tuple[str, str, str, str, str]
    evidence_refs: tuple[str, ...] = ()
    feature_policy_version: str = Field(min_length=1)
    qualification_policy_version: str = Field(min_length=1)
    decision_policy_version: str = Field(min_length=1)
    reasons: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()


class AffiliateLinkArtifact(BaseModel):
    model_config = ConfigDict(frozen=True)

    artifact_id: str = Field(min_length=1)
    selection_decision_id: str = Field(min_length=1)
    source_job_id: str = Field(min_length=1)
    affiliate_account_id: str = Field(min_length=1)
    offer_id: str = Field(min_length=1)
    link_url: str = Field(min_length=1)
    created_at: datetime
    validated_at: datetime | None = None
    validation_state: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()


class Program3OfferHandoff(BaseModel):
    model_config = ConfigDict(frozen=True)

    handoff_id: str = Field(min_length=1)
    selection_decision_id: str = Field(min_length=1)
    affiliate_account_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    preferred_offer_id: str = Field(min_length=1)
    backup_offer_ids: tuple[str, ...] = ()
    link_artifact_id: str = Field(min_length=1)
    valid_at: datetime
    evidence_refs: tuple[str, ...] = ()
