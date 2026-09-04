from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SignalValidationState(StrEnum):
    EXPERIMENTAL = "EXPERIMENTAL"
    LAB_VALIDATED = "LAB_VALIDATED"
    EVIDENCE_VALIDATED = "EVIDENCE_VALIDATED"
    PRODUCTION_CANDIDATE = "PRODUCTION_CANDIDATE"
    PRODUCTION_APPROVED = "PRODUCTION_APPROVED"
    DEPRECATED = "DEPRECATED"


class AffiliateSuccessHypothesis(BaseModel):
    """Strategy-owned statement describing the affiliate decision to improve."""

    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    hypothesis_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    decision_question: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    target_outcome: str = Field(min_length=1)
    audience_context: str | None = None
    time_context: str | None = None
    policy_version: str = Field(min_length=1)
    created_at: datetime


class SignalRequirement(BaseModel):
    """A signal exists because it supports one explicit affiliate decision."""

    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    signal_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    decision_supported: str = Field(min_length=1)
    expected_interpretation: str = Field(min_length=1)
    evidence_source: str = Field(min_length=1)
    freshness_requirement: str | None = None
    validation_state: SignalValidationState = SignalValidationState.EXPERIMENTAL
    downstream_validation_metric: str | None = None


class DiscoveryPlan(BaseModel):
    """Application-ready strategy-to-work contract.

    This is intentionally free of DOM selectors and browser implementation detail.
    """

    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    plan_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    required_signal_ids: tuple[str, ...] = Field(min_length=1)
    source_scope: str = Field(min_length=1)
    surface_scope: tuple[str, ...] = Field(min_length=1)
    capability_requirements: tuple[str, ...] = ()
    evidence_policy_version: str = Field(min_length=1)
    collection_policy_version: str = Field(min_length=1)
    created_at: datetime

    @model_validator(mode="after")
    def validate_unique_values(self) -> DiscoveryPlan:
        if len(set(self.required_signal_ids)) != len(self.required_signal_ids):
            raise ValueError("required_signal_ids must be unique")
        if len(set(self.surface_scope)) != len(self.surface_scope):
            raise ValueError("surface_scope must be unique")
        if len(set(self.capability_requirements)) != len(self.capability_requirements):
            raise ValueError("capability_requirements must be unique")
        return self
