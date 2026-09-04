from __future__ import annotations

from pathlib import Path

from mtaffiliate.adapters.persistence.sqlalchemy import (
    SQLAlchemyProgram2ArtifactRepository,
    SQLAlchemyProgram2DecisionRepository,
    build_engine,
    build_session_factory,
)
from mtaffiliate.application.program2_artifacts import Program2ArtifactService
from mtaffiliate.bootstrap.config import Settings


def build_durable_program2_artifact_service(
    settings: Settings,
    *,
    project_root: Path,
) -> Program2ArtifactService:
    engine = build_engine(settings.database.url, project_root=project_root)
    sessions = build_session_factory(engine)
    return Program2ArtifactService(
        decisions=SQLAlchemyProgram2DecisionRepository(sessions),
        artifacts=SQLAlchemyProgram2ArtifactRepository(sessions),
    )
