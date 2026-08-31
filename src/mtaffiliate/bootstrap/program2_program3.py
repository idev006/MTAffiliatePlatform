from __future__ import annotations

from pathlib import Path

from mtaffiliate.adapters.persistence.sqlalchemy.affiliate_offer import (
    SQLAlchemyAffiliateOfferRepository,
)
from mtaffiliate.adapters.persistence.sqlalchemy.factory import (
    build_engine,
    build_session_factory,
)
from mtaffiliate.adapters.persistence.sqlalchemy.publishing import (
    SQLAlchemyPublishingLedgerRepository,
)
from mtaffiliate.application.program2 import Program2Service
from mtaffiliate.application.program3 import Program3Service
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.engines.affiliate_offer_engine.service import (
    AffiliateOfferEngine,
    OfferScoringPolicy,
)
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine


def build_durable_program2_program3(
    settings: Settings,
    *,
    project_root: Path,
) -> tuple[Program2Service, Program3Service]:
    engine = build_engine(settings.database.url, project_root=project_root)
    sessions = build_session_factory(engine)
    scoring = settings.program2.scoring
    program2 = Program2Service(
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
    program3 = Program3Service(
        SQLAlchemyPublishingLedgerRepository(sessions),
        PublishingGuardEngine(),
    )
    return program2, program3
