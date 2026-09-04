from __future__ import annotations

from datetime import timedelta

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mtaffiliate.adapters.persistence.inmemory.affiliate_offer import (
    InMemoryAffiliateOfferRepository,
)
from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository
from mtaffiliate.adapters.persistence.inmemory.product import InMemoryProductRepository
from mtaffiliate.adapters.persistence.inmemory.publishing import (
    InMemoryPublishingLedgerRepository,
)
from mtaffiliate.adapters.persistence.inmemory.worker_registry import (
    InMemoryWorkerRegistryRepository,
)
from mtaffiliate.application.program1 import IngestionBatchConflictError, Program1Service
from mtaffiliate.application.program1_jobs import Program1DiscoveryJobService
from mtaffiliate.application.program1_strategy import Program1StrategyPlanner
from mtaffiliate.application.program2 import Program2Service
from mtaffiliate.application.program3 import Program3Service
from mtaffiliate.application.worker_registry import (
    DEFAULT_STALE_HEARTBEAT_MULTIPLIER,
    WorkerRegistryService,
    utc_now,
)
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateOfferObservation,
    OfferScore,
    OfferSelection,
)
from mtaffiliate.domain.product.models import ProductObservation, ShortlistEntry
from mtaffiliate.domain.publishing.models import (
    DuplicateDecision,
    PublishingLedgerEntry,
    PublishPlan,
)
from mtaffiliate.domain.worker_registry.models import (
    WorkerHealthState,
    WorkerRecord,
    WorkerRegistration,
    WorkerSummary,
)
from mtaffiliate.engines.affiliate_offer_engine.service import (
    AffiliateOfferEngine,
    OfferScoringPolicy,
)
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine
from mtaffiliate.interfaces.api.shared_jobs import build_shared_job_router
from mtaffiliate.ports.repositories.product import ObservationConflictError
from mtaffiliate.ports.repositories.worker_registry import (
    UnknownWorkerError,
    WorkerRegistrationConflictError,
)


class ObservationBatch(BaseModel):
    batch_id: str = Field(min_length=1)
    observations: list[ProductObservation]


class OfferObservationBatch(BaseModel):
    observations: list[AffiliateOfferObservation]


class OfferSelectionRequest(BaseModel):
    affiliate_account_id: str = Field(min_length=1)
    backup_count: int | None = Field(default=None, ge=0, le=20)


class PublishStatusRequest(BaseModel):
    plan: PublishPlan
    status: str = Field(min_length=1)


class WorkerHeartbeatRequest(BaseModel):
    schema_version: str = Field(default="worker-heartbeat-v1", min_length=1)
    health_state: WorkerHealthState


def build_inmemory_program1(settings: Settings) -> Program1Service:
    scoring = settings.program1.scoring
    engine = ProductIntelligenceEngine(
        ScoringPolicy(
            demand_weight=scoring.demand_weight,
            rating_weight=scoring.rating_weight,
            review_weight=scoring.review_weight,
            price_fit_weight=scoring.price_fit_weight,
        )
    )
    return Program1Service(
        InMemoryProductRepository(),
        engine,
        shortlist_limit=settings.program1.shortlist_limit,
        minimum_score=settings.program1.minimum_score,
    )


def build_inmemory_program2(settings: Settings) -> Program2Service:
    scoring = settings.program2.scoring
    return Program2Service(
        InMemoryAffiliateOfferRepository(),
        AffiliateOfferEngine(
            OfferScoringPolicy(
                commission_weight=scoring.commission_weight,
                rating_weight=scoring.rating_weight,
                review_weight=scoring.review_weight,
                demand_weight=scoring.demand_weight,
            )
        ),
    )


def build_inmemory_program3() -> Program3Service:
    return Program3Service(
        InMemoryPublishingLedgerRepository(),
        PublishingGuardEngine(),
    )


def build_inmemory_worker_registry(settings: Settings) -> WorkerRegistryService:
    return WorkerRegistryService(
        InMemoryWorkerRegistryRepository(),
        stale_after=timedelta(
            seconds=settings.worker.heartbeat_seconds * DEFAULT_STALE_HEARTBEAT_MULTIPLIER
        ),
    )


def create_app(
    settings: Settings | None = None,
    *,
    program1: Program1Service | None = None,
    program2: Program2Service | None = None,
    program3: Program3Service | None = None,
    registry: WorkerRegistryService | None = None,
    shared_jobs: SharedJobEngine | None = None,
    program1_jobs: Program1DiscoveryJobService | None = None,
    enabled_programs: set[str] | None = None,
) -> FastAPI:
    enabled = enabled_programs or {"program1", "program2", "program3"}
    unknown = enabled - {"program1", "program2", "program3"}
    if unknown:
        raise ValueError(f"unknown enabled programs: {sorted(unknown)}")
    cfg = settings or Settings()
    service1 = program1 or build_inmemory_program1(cfg) if "program1" in enabled else None
    service2 = program2 or build_inmemory_program2(cfg) if "program2" in enabled else None
    service3 = program3 or build_inmemory_program3() if "program3" in enabled else None
    registry_service = registry or build_inmemory_worker_registry(cfg)
    shared_job_engine = shared_jobs or SharedJobEngine(InMemoryJobRepository())
    program1_job_service = program1_jobs or Program1DiscoveryJobService(
        Program1StrategyPlanner(),
        shared_job_engine,
    )
    app = FastAPI(title="MTAffiliatePlatform", version="0.2.0")

    @app.get("/")
    def root() -> dict[str, str | list[str]]:
        return {
            "service": "MTAffiliatePlatform API",
            "status": "ok",
            "enabled_programs": sorted(enabled),
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/workers/register", response_model=WorkerRecord)
    def register_worker(registration: WorkerRegistration) -> WorkerRecord:
        try:
            return registry_service.register(registration, seen_at=utc_now())
        except WorkerRegistrationConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post(
        "/api/v1/workers/{worker_id}/heartbeat",
        response_model=WorkerRecord,
    )
    def heartbeat(worker_id: str, request: WorkerHeartbeatRequest) -> WorkerRecord:
        try:
            return registry_service.record_heartbeat(
                worker_id,
                health_state=request.health_state,
                seen_at=utc_now(),
            )
        except UnknownWorkerError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/v1/workers", response_model=list[WorkerSummary])
    def list_workers() -> list[WorkerSummary]:
        return registry_service.summaries(now=utc_now())

    @app.get("/api/v1/workers/{worker_id}", response_model=WorkerSummary)
    def get_worker(worker_id: str) -> WorkerSummary:
        summary = registry_service.summary(worker_id, now=utc_now())
        if summary is None:
            raise HTTPException(status_code=404, detail=f"unknown worker: {worker_id}")
        return summary

    if "program1" in enabled:
        app.include_router(
            build_shared_job_router(
                program1_jobs=program1_job_service,
                jobs=shared_job_engine,
                registry=registry_service,
                lease_seconds=cfg.worker.lease_seconds,
                clock=utc_now,
            )
        )

        @app.post("/api/v1/program1/observations")
        def ingest(batch: ObservationBatch) -> dict[str, int | str]:
            assert service1 is not None
            try:
                result = service1.ingest_batch(batch.batch_id, batch.observations)
            except (IngestionBatchConflictError, ObservationConflictError) as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            return {
                "batch_id": batch.batch_id,
                "received_count": result.received_count,
                "accepted_count": result.accepted_count,
            }

        @app.get("/api/v1/program1/shortlist", response_model=list[ShortlistEntry])
        def shortlist() -> list[ShortlistEntry]:
            assert service1 is not None
            return service1.build_shortlist()

    if "program2" in enabled:

        @app.post("/api/v1/program2/observations")
        def ingest_offers(batch: OfferObservationBatch) -> dict[str, int]:
            assert service2 is not None
            try:
                accepted = service2.ingest_observations(batch.observations)
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            return {"received_count": len(batch.observations), "accepted_count": accepted}

        @app.get(
            "/api/v1/program2/products/{product_id}/offers",
            response_model=list[OfferScore],
        )
        def rank_offers(
            product_id: str,
            affiliate_account_id: str | None = None,
        ) -> list[OfferScore]:
            assert service2 is not None
            return service2.rank_offers(
                product_id,
                affiliate_account_id=affiliate_account_id,
            )

        @app.post(
            "/api/v1/program2/products/{product_id}/selection",
            response_model=OfferSelection,
        )
        def select_offers(product_id: str, request: OfferSelectionRequest) -> OfferSelection:
            assert service2 is not None
            try:
                return service2.select_offers(
                    product_id,
                    affiliate_account_id=request.affiliate_account_id,
                    backup_count=(
                        cfg.program2.backup_offer_count
                        if request.backup_count is None
                        else request.backup_count
                    ),
                )
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

    if "program3" in enabled:

        @app.post("/api/v1/program3/publish/evaluate", response_model=DuplicateDecision)
        def evaluate_publish(plan: PublishPlan) -> DuplicateDecision:
            assert service3 is not None
            return service3.evaluate_plan(plan)

        @app.post("/api/v1/program3/publish/status", response_model=PublishingLedgerEntry)
        def record_publish_status(request: PublishStatusRequest) -> PublishingLedgerEntry:
            assert service3 is not None
            try:
                return service3.record_status(request.plan, request.status)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

    return app
