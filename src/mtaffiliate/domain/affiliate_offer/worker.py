from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from mtaffiliate.domain.affiliate_offer.models import AffiliateOfferObservation


class OfferDiscoveryCommand(BaseModel):
    command_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    affiliate_account_id: str = Field(min_length=1)
    session_context_id: str | None = None
    issued_at: datetime
    contract_version: str = Field(default="program2-worker-v1", min_length=1)


class OfferObservationBatch(BaseModel):
    batch_id: str = Field(min_length=1)
    command_id: str = Field(min_length=1)
    worker_id: str = Field(min_length=1)
    affiliate_account_id: str = Field(min_length=1)
    observations: list[AffiliateOfferObservation]
    captured_at: datetime
    extractor_version: str = Field(min_length=1)


class WorkerDeliveryReceipt(BaseModel):
    batch_id: str = Field(min_length=1)
    status: Literal["ACK", "CONFLICT", "REJECTED"]
    received_count: int = Field(ge=0)
    accepted_count: int = Field(ge=0)
    detail: str | None = None


class OutboxEnvelope(BaseModel):
    envelope_id: str = Field(min_length=1)
    kind: Literal["OFFER_OBSERVATION_BATCH", "WORKER_EVENT", "EXPORT_ARTIFACT"]
    payload_json: str = Field(min_length=2)
    created_at: datetime
    attempt_count: int = Field(default=0, ge=0)
