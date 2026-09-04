from __future__ import annotations

from pathlib import Path

from mtaffiliate.adapters.persistence.sqlalchemy import (
    SQLAlchemyProgram1StrategyRepository,
    build_engine,
    build_session_factory,
)
from mtaffiliate.application.program1_jobs import Program1DiscoveryJobService
from mtaffiliate.application.program1_strategy import Program1StrategyPlanner
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine


def build_durable_program1_job_service(
    settings: Settings,
    *,
    project_root: Path,
    jobs: SharedJobEngine,
) -> Program1DiscoveryJobService:
    engine = build_engine(settings.database.url, project_root=project_root)
    sessions = build_session_factory(engine)
    return Program1DiscoveryJobService(
        Program1StrategyPlanner(),
        SQLAlchemyProgram1StrategyRepository(sessions),
        jobs,
    )
