from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mtaffiliate.adapters.persistence.inmemory.product import (
    InMemoryProductRepository,
    ObservationConflictError,
)
from mtaffiliate.application.program1 import IngestionBatchConflictError, Program1Service
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.domain.product.models import ProductObservation, ShortlistEntry
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)


class ObservationBatch(BaseModel):
    batch_id: str = Field(min_length=1)
    observations: list[ProductObservation]


def build_program1(settings: Settings) -> Program1Service:
    repository = InMemoryProductRepository()
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
        repository,
        engine,
        shortlist_limit=settings.program1.shortlist_limit,
        minimum_score=settings.program1.minimum_score,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or Settings()
    program1 = build_program1(cfg)
    app = FastAPI(title="MTAffiliatePlatform", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/program1/observations")
    def ingest(batch: ObservationBatch) -> dict[str, int | str]:
        try:
            result = program1.ingest_batch(batch.batch_id, batch.observations)
        except (IngestionBatchConflictError, ObservationConflictError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {
            "batch_id": batch.batch_id,
            "received_count": result.received_count,
            "accepted_count": result.accepted_count,
        }

    @app.get("/api/v1/program1/shortlist", response_model=list[ShortlistEntry])
    def shortlist() -> list[ShortlistEntry]:
        return program1.build_shortlist()

    return app
