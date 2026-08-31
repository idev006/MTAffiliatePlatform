from __future__ import annotations

from datetime import datetime

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
