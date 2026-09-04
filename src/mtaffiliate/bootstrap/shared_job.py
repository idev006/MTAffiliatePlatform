from __future__ import annotations

from pathlib import Path

from mtaffiliate.adapters.persistence.sqlalchemy import (
    SQLAlchemyJobRepository,
    build_engine,
    build_session_factory,
)
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine


def build_durable_shared_job_engine(
    settings: Settings,
    *,
    project_root: Path,
) -> SharedJobEngine:
    engine = build_engine(settings.database.url, project_root=project_root)
    sessions = build_session_factory(engine)
    return SharedJobEngine(SQLAlchemyJobRepository(sessions))
