from __future__ import annotations

from pathlib import Path

from mtaffiliate.adapters.persistence.sqlalchemy import (
    SQLAlchemyIngestionBatchStore,
    SQLAlchemyProductRepository,
    build_engine,
    build_session_factory,
)
from mtaffiliate.application.program1 import Program1Service
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)


def build_durable_program1(settings: Settings, *, project_root: Path) -> Program1Service:
    engine = build_engine(settings.database.url, project_root=project_root)
    sessions = build_session_factory(engine)
    scoring = settings.program1.scoring
    intelligence = ProductIntelligenceEngine(
        ScoringPolicy(
            demand_weight=scoring.demand_weight,
            rating_weight=scoring.rating_weight,
            review_weight=scoring.review_weight,
            price_fit_weight=scoring.price_fit_weight,
        )
    )
    return Program1Service(
        SQLAlchemyProductRepository(sessions),
        intelligence,
        shortlist_limit=settings.program1.shortlist_limit,
        minimum_score=settings.program1.minimum_score,
        batch_store=SQLAlchemyIngestionBatchStore(sessions),
    )
