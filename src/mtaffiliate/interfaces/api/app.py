from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mtaffiliate.adapters.persistence.inmemory.affiliate_offer import (
    InMemoryAffiliateOfferRepository,
)
from mtaffiliate.adapters.persistence.inmemory.product import InMemoryProductRepository
from mtaffiliate.adapters.persistence.inmemory.publishing import (
    InMemoryPublishingLedgerRepository,
)
from mtaffiliate.application.program1 import IngestionBatchConflictError, Program1Service
from mtaffiliate.application.program2 import Program2Service
from mtaffiliate.application.program3 import Program3Service
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
from mtaffiliate.engines.affiliate_offer_engine.service import (
    AffiliateOfferEngine,
    OfferScoringPolicy,
)
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine
from mtaffiliate.ports.repositories.product import ObservationConflictError


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


def create_app(
    settings: Settings | None = None,
    *,
    program1: Program1Service | None = None,
    program2: Program2Service | None = None,
    program3: Program3Service | None = None,
) -> FastAPI:
    cfg = settings or Settings()
    service1 = program1 or build_inmemory_program1(cfg)
    service2 = program2 or build_inmemory_program2(cfg)
    service3 = program3 or build_inmemory_program3()
    app = FastAPI(title="MTAffiliatePlatform", version="0.2.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/program1/observations")
    def ingest(batch: ObservationBatch) -> dict[str, int | str]:
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
        return service1.build_shortlist()

    @app.post("/api/v1/program2/observations")
    def ingest_offers(batch: OfferObservationBatch) -> dict[str, int]:
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
        return service2.rank_offers(
            product_id,
            affiliate_account_id=affiliate_account_id,
        )

    @app.post(
        "/api/v1/program2/products/{product_id}/selection",
        response_model=OfferSelection,
    )
    def select_offers(product_id: str, request: OfferSelectionRequest) -> OfferSelection:
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

    @app.post("/api/v1/program3/publish/evaluate", response_model=DuplicateDecision)
    def evaluate_publish(plan: PublishPlan) -> DuplicateDecision:
        return service3.evaluate_plan(plan)

    @app.post("/api/v1/program3/publish/status", response_model=PublishingLedgerEntry)
    def record_publish_status(request: PublishStatusRequest) -> PublishingLedgerEntry:
        try:
            return service3.record_status(request.plan, request.status)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return app
