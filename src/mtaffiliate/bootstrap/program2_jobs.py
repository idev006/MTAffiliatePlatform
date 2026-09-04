from __future__ import annotations

from pathlib import Path

from mtaffiliate.adapters.persistence.sqlalchemy import (
    SQLAlchemyProgram2WorkRepository,
    build_engine,
    build_session_factory,
)
from mtaffiliate.application.program2_jobs import Program2OfferDiscoveryJobService
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine


def build_durable_program2_job_service(
    settings: Settings,
    *,
    project_root: Path,
    jobs: SharedJobEngine,
) -> Program2OfferDiscoveryJobService:
    engine = build_engine(settings.database.url, project_root=project_root)
    sessions = build_session_factory(engine)
    return Program2OfferDiscoveryJobService(
        SQLAlchemyProgram2WorkRepository(sessions),
        jobs,
    )
