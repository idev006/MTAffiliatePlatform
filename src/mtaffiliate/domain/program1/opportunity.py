from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class OpportunityEvidenceState(StrEnum):
    SUFFICIENT_FOR_LAB = "SUFFICIENT_FOR_LAB"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"


class QualificationState(StrEnum):
    QUALIFIED_FOR_TEST = "QUALIFIED_FOR_TEST"
    WATCH = "WATCH"
    HOLD = "HOLD"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"


class OpportunityAction(StrEnum):
    TEST_NOW = "TEST_NOW"
    WATCH = "WATCH"
    HOLD = "HOLD"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"


class OpportunityFeatureSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    product_key: tuple[str, str, str]
    as_of: datetime
    feature_policy_version: str = Field(min_length=1)
    history_count: int = Field(ge=1)

    latest_sold_signal: int | None = Field(default=None, ge=0)
    sold_signal_delta: int | None = None
    latest_rating: float | None = Field(default=None, ge=0, le=5)
    latest_review_count: int | None = Field(default=None, ge=0)
    latest_price: Decimal | None = Field(default=None, ge=0)
    observation_age_seconds: float = Field(ge=0)

    evidence_state: OpportunityEvidenceState
    unknown_features: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()


class QualificationDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    product_key: tuple[str, str, str]
    state: QualificationState
    recommended_action: OpportunityAction
    policy_version: str = Field(min_length=1)
    reasons: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    evaluated_at: datetime


class OpportunityThesis(BaseModel):
    model_config = ConfigDict(frozen=True)

    product_key: tuple[str, str, str]
    product_name: str = Field(min_length=1)
    as_of: datetime
    feature_policy_version: str = Field(min_length=1)
    qualification_policy_version: str = Field(min_length=1)
    recommended_action: OpportunityAction

    why_now: tuple[str, ...] = ()
    observed_evidence: tuple[str, ...] = ()
    strengths: tuple[str, ...] = ()
    risks_and_uncertainties: tuple[str, ...] = ()
    target_buyer_context: str | None = None
    evidence_state: OpportunityEvidenceState
    evidence_refs: tuple[str, ...] = ()


class OpportunityDecisionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    source_job_id: str = Field(min_length=1)
    evaluated_at: datetime
    thesis: OpportunityThesis


class QualifiedOpportunityHandoff(BaseModel):
    model_config = ConfigDict(frozen=True)

    handoff_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    source_job_id: str = Field(min_length=1)
    product_key: tuple[str, str, str]
    product_name: str = Field(min_length=1)
    recommended_action: OpportunityAction
    evidence_refs: tuple[str, ...]
    feature_policy_version: str = Field(min_length=1)
    qualification_policy_version: str = Field(min_length=1)
