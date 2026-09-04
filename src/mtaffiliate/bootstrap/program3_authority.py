from __future__ import annotations

from pathlib import Path

from mtaffiliate.adapters.persistence.sqlalchemy import (
    SQLAlchemyDeviceRepository,
    SQLAlchemyProgram2ArtifactRepository,
    SQLAlchemyProgram2DecisionRepository,
    SQLAlchemyProgram3ExecutionRepository,
    build_engine,
    build_session_factory,
)
from mtaffiliate.adapters.persistence.sqlalchemy.publishing import (
    SQLAlchemyPublishingLedgerRepository,
)
from mtaffiliate.application.program3_authority import Program3AuthoritativeService
from mtaffiliate.application.program3_device import Program3DeviceService
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.engines.device_host_engine.service import DeviceHostEngine
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine


def build_durable_program3_authority(
    settings: Settings,
    *,
    project_root: Path,
    jobs: SharedJobEngine,
) -> Program3AuthoritativeService:
    engine = build_engine(settings.database.url, project_root=project_root)
    sessions = build_session_factory(engine)
    return Program3AuthoritativeService(
        decisions=SQLAlchemyProgram2DecisionRepository(sessions),
        artifacts=SQLAlchemyProgram2ArtifactRepository(sessions),
        execution=SQLAlchemyProgram3ExecutionRepository(sessions),
        ledger=SQLAlchemyPublishingLedgerRepository(sessions),
        jobs=jobs,
        guard=PublishingGuardEngine(),
        devices=Program3DeviceService(
            SQLAlchemyDeviceRepository(sessions),
            DeviceHostEngine(),
        ),
    )
