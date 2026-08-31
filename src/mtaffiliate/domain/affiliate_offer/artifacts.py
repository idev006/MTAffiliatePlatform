from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class AffiliateLink(BaseModel):
    affiliate_link_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    offer_id: str = Field(min_length=1)
    affiliate_account_id: str = Field(min_length=1)
    url: HttpUrl
    acquired_at: datetime
    source_artifact_id: str | None = None
    contract_version: str = Field(default="affiliate-link-v1", min_length=1)


class OfferExportArtifact(BaseModel):
    artifact_id: str = Field(min_length=1)
    affiliate_account_id: str = Field(min_length=1)
    generated_at: datetime
    format: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    source_job_id: str = Field(min_length=1)
    parser_profile_version: str = Field(min_length=1)


class LinkValidationResult(BaseModel):
    valid: bool
    reason: str = Field(min_length=1)
