from __future__ import annotations

from pathlib import Path

from mtaffiliate.adapters.persistence.sqlalchemy import (
    SQLAlchemyAffiliateOfferRepository,
    SQLAlchemyProgram2DecisionRepository,
    build_engine,
    build_session_factory,
)
from mtaffiliate.application.program2_intelligence import Program2OfferDecisionService
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.engines.affiliate_offer_engine.service import EvidenceFirstOfferIntelligence


def build_durable_program2_intelligence(
    settings: Settings,
    *,
    project_root: Path,
) -> Program2OfferDecisionService:
    engine = build_engine(settings.database.url, project_root=project_root)
    sessions = build_session_factory(engine)
    return Program2OfferDecisionService(
        offers=SQLAlchemyAffiliateOfferRepository(sessions),
        decisions=SQLAlchemyProgram2DecisionRepository(sessions),
        intelligence=EvidenceFirstOfferIntelligence(),
    )
