from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from mtaffiliate.adapters.persistence.sqlalchemy import (
    SQLAlchemyWorkerRegistryRepository,
    build_engine,
    build_session_factory,
)
from mtaffiliate.application.worker_registry import (
    DEFAULT_STALE_HEARTBEAT_MULTIPLIER,
    WorkerRegistryService,
)
from mtaffiliate.bootstrap.config import Settings


def build_durable_worker_registry(
    settings: Settings,
    *,
    project_root: Path,
) -> WorkerRegistryService:
    engine = build_engine(settings.database.url, project_root=project_root)
    sessions = build_session_factory(engine)
    return WorkerRegistryService(
        SQLAlchemyWorkerRegistryRepository(sessions),
        stale_after=timedelta(
            seconds=settings.worker.heartbeat_seconds * DEFAULT_STALE_HEARTBEAT_MULTIPLIER
        ),
    )
