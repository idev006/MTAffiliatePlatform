from __future__ import annotations

from pathlib import Path

from mtaffiliate.adapters.persistence.sqlalchemy.factory import (
    build_engine,
    build_session_factory,
)
from mtaffiliate.adapters.persistence.sqlalchemy.publishing import (
    SQLAlchemyPublishingLedgerRepository,
)
from mtaffiliate.application.program3 import Program3Service
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine


def build_durable_program3(settings: Settings, *, project_root: Path) -> Program3Service:
    engine = build_engine(settings.database.url, project_root=project_root)
    sessions = build_session_factory(engine)
    return Program3Service(
        SQLAlchemyPublishingLedgerRepository(sessions),
        PublishingGuardEngine(),
    )
