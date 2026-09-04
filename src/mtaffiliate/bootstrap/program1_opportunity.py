from __future__ import annotations

from pathlib import Path

from mtaffiliate.adapters.persistence.sqlalchemy import (
    SQLAlchemyProductRepository,
    SQLAlchemyProgram1OpportunityRepository,
    SQLAlchemyProgram1StrategyRepository,
    build_engine,
    build_session_factory,
)
from mtaffiliate.application.program1_opportunity import Program1OpportunityService
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.engines.opportunity_intelligence_engine.service import (
    OpportunityIntelligenceEngine,
)
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine


def build_durable_program1_opportunity_service(
    settings: Settings,
    *,
    project_root: Path,
    jobs: SharedJobEngine,
) -> Program1OpportunityService:
    engine = build_engine(settings.database.url, project_root=project_root)
    sessions = build_session_factory(engine)
    return Program1OpportunityService(
        products=SQLAlchemyProductRepository(sessions),
        jobs=jobs.repository,
        strategies=SQLAlchemyProgram1StrategyRepository(sessions),
        decisions=SQLAlchemyProgram1OpportunityRepository(sessions),
        intelligence=OpportunityIntelligenceEngine(),
    )
