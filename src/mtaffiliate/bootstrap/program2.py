from __future__ import annotations

from pathlib import Path

from mtaffiliate.adapters.persistence.sqlalchemy.affiliate_offer import (
    SQLAlchemyAffiliateOfferRepository,
)
from mtaffiliate.adapters.persistence.sqlalchemy.factory import (
    build_engine,
    build_session_factory,
)
from mtaffiliate.application.program2 import Program2Service
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.engines.affiliate_offer_engine.service import (
    AffiliateOfferEngine,
    OfferScoringPolicy,
)


def build_durable_program2(settings: Settings, *, project_root: Path) -> Program2Service:
    engine = build_engine(settings.database.url, project_root=project_root)
    sessions = build_session_factory(engine)
    scoring = settings.program2.scoring
    return Program2Service(
        SQLAlchemyAffiliateOfferRepository(sessions),
        AffiliateOfferEngine(
            OfferScoringPolicy(
                commission_weight=scoring.commission_weight,
                rating_weight=scoring.rating_weight,
                review_weight=scoring.review_weight,
                demand_weight=scoring.demand_weight,
            )
        ),
    )
