from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WorkersRow(Base):
    """Shared Core worker registry current projection (DATA_MODEL `workers`)."""

    __tablename__ = "workers"

    worker_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    worker_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    installation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    host_id: Mapped[str | None] = mapped_column(String(128))
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    capabilities: Mapped[str] = mapped_column(String(4096), nullable=False)
    health_state: Mapped[str] = mapped_column(String(32), nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)


class JobsRow(Base):
    """Shared Job Engine current projection."""

    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_jobs_idempotency_key"),)

    job_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    job_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload_ref: Mapped[str] = mapped_column(String(1024), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    capability_requirements: Mapped[str] = mapped_column(String(4096), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    job_version: Mapped[int] = mapped_column(Integer, nullable=False)
    assigned_worker_id: Mapped[str | None] = mapped_column(String(128), index=True)
    lease_token: Mapped[str | None] = mapped_column(String(256))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    checkpoint_json: Mapped[str | None] = mapped_column(String(16384))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(128))
    failure_detail: Mapped[str | None] = mapped_column(String(4096))


class JobEventsRow(Base):
    """Append-oriented audit events; one event corresponds to one job version."""

    __tablename__ = "job_events"
    __table_args__ = (
        UniqueConstraint("job_id", "job_version", name="uq_job_events_job_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    job_version: Mapped[int] = mapped_column(Integer, nullable=False)
    emitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    worker_id: Mapped[str | None] = mapped_column(String(128), index=True)
    detail: Mapped[str | None] = mapped_column(String(4096))


class ProductObservationRow(Base):
    __tablename__ = "product_observations"
    __table_args__ = (UniqueConstraint("observation_id", name="uq_product_observation_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    shop_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(1024), nullable=False)
    product_url: Mapped[str | None] = mapped_column(String(4096))
    price_current: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    sold_signal: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[float | None]
    review_count: Mapped[int | None] = mapped_column(Integer)
    source_worker_id: Mapped[str | None] = mapped_column(String(128))
    source_query: Mapped[str | None] = mapped_column(String(1024))
    extractor_version: Mapped[str | None] = mapped_column(String(128))


class IngestionBatchRow(Base):
    __tablename__ = "ingestion_batches"

    batch_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    accepted_count: Mapped[int] = mapped_column(Integer, nullable=False)
    received_count: Mapped[int] = mapped_column(Integer, nullable=False)


class AffiliateOfferObservationRow(Base):
    __tablename__ = "affiliate_offer_observations"

    observation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    offer_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    shop_id: Mapped[str] = mapped_column(String(128), nullable=False)
    item_id: Mapped[str] = mapped_column(String(128), nullable=False)
    affiliate_account_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    seller_name: Mapped[str | None] = mapped_column(String(1024))
    product_name: Mapped[str] = mapped_column(String(1024), nullable=False)
    price_current: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    commission_rate: Mapped[float | None] = mapped_column(Float)
    extra_commission_rate: Mapped[float | None] = mapped_column(Float)
    rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    sold_signal: Mapped[int | None] = mapped_column(Integer)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False)


class AffiliateOfferSelectionRow(Base):
    __tablename__ = "affiliate_offer_selections"

    selection_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    preferred_offer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    backup_offer_ids: Mapped[str] = mapped_column(String(4096), nullable=False)
    affiliate_account_id: Mapped[str] = mapped_column(String(128), nullable=False)
    selected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    model_version: Mapped[str] = mapped_column(String(128), nullable=False)


class PublishingLedgerRow(Base):
    __tablename__ = "publishing_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    publish_job_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    target_account_id: Mapped[str] = mapped_column(String(128), nullable=False)
    video_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    video_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
