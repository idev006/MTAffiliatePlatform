from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ApprovedOfferRef(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    selection_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    offer_id: str = Field(min_length=1)
    shop_id: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    affiliate_account_id: str = Field(min_length=1)
    affiliate_link_id: str = Field(min_length=1)


class PublishPlan(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    publish_job_id: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    target_account_id: str = Field(min_length=1)
    video_id: str = Field(min_length=1)
    video_sha256: str = Field(min_length=64, max_length=64)
    offers: list[ApprovedOfferRef] = Field(min_length=1)
    caption: str = ""
    tags: list[str] = Field(default_factory=list)
    duplicate_policy_version: str = Field(min_length=1)
    plan_version: str = Field(min_length=1)
    created_at: datetime


class PublishingLedgerEntry(BaseModel):
    publish_job_id: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    target_account_id: str = Field(min_length=1)
    video_id: str = Field(min_length=1)
    video_sha256: str = Field(min_length=64, max_length=64)
    status: str = Field(min_length=1)
    updated_at: datetime


class DuplicateDecision(BaseModel):
    allowed: bool
    reason: str = Field(min_length=1)



class PreSubmitDecisionState(StrEnum):
    ALLOW_SUBMIT = "ALLOW_SUBMIT"
    REJECT = "REJECT"
    NEEDS_HUMAN = "NEEDS_HUMAN"


class ReconciliationOutcome(StrEnum):
    CONFIRMED_SUCCESS = "CONFIRMED_SUCCESS"
    CONFIRMED_FAILURE_SAFE_TO_RETRY = "CONFIRMED_FAILURE_SAFE_TO_RETRY"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    NEEDS_HUMAN = "NEEDS_HUMAN"


class Program3PlanPackage(BaseModel):
    model_config = ConfigDict(frozen=True)

    plan_ref: str = Field(min_length=1)
    source_program2_handoff_id: str = Field(min_length=1)
    source_selection_decision_id: str = Field(min_length=1)
    source_link_artifact_id: str = Field(min_length=1)
    program2_handoff_valid_at: datetime
    publish_plan: PublishPlan
    evidence_refs: tuple[str, ...] = ()


class PreSubmitDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision_id: str = Field(min_length=1)
    publish_job_id: str = Field(min_length=1)
    plan_ref: str = Field(min_length=1)
    worker_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    target_account_id: str = Field(min_length=1)
    evaluated_at: datetime
    state: PreSubmitDecisionState
    reasons: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    policy_version: str = Field(min_length=1)


class SubmissionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    submission_id: str = Field(min_length=1)
    publish_job_id: str = Field(min_length=1)
    plan_ref: str = Field(min_length=1)
    worker_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    submitted_at: datetime
    evidence_refs: tuple[str, ...] = ()
    idempotency_key: str = Field(min_length=1)


class ReconciliationDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    reconciliation_id: str = Field(min_length=1)
    submission_id: str = Field(min_length=1)
    publish_job_id: str = Field(min_length=1)
    evaluated_at: datetime
    outcome: ReconciliationOutcome
    retry_allowed: bool
    reasons: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    policy_version: str = Field(min_length=1)
