from pathlib import Path

import pytest

from mtaffiliate.bootstrap.config import DatabaseConfig, Settings
from mtaffiliate.bootstrap.program2_artifacts import build_durable_program2_artifact_service
from mtaffiliate.bootstrap.program2_intelligence import build_durable_program2_intelligence
from mtaffiliate.bootstrap.program2_jobs import build_durable_program2_job_service
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine
from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository

pytestmark = pytest.mark.integration


def test_program2_authoritative_bootstrap_composes_sql_adapters(tmp_path: Path) -> None:
    settings = Settings(database=DatabaseConfig(url="sqlite:///data/program2-bootstrap.db"))
    jobs = SharedJobEngine(InMemoryJobRepository())

    job_service = build_durable_program2_job_service(
        settings,
        project_root=tmp_path,
        jobs=jobs,
    )
    intelligence = build_durable_program2_intelligence(
        settings,
        project_root=tmp_path,
    )
    artifacts = build_durable_program2_artifact_service(
        settings,
        project_root=tmp_path,
    )

    assert job_service.jobs is jobs
    assert job_service.work_repository.__class__.__name__ == "SQLAlchemyProgram2WorkRepository"
    assert intelligence.offers.__class__.__name__ == "SQLAlchemyAffiliateOfferRepository"
    assert intelligence.decisions.__class__.__name__ == "SQLAlchemyProgram2DecisionRepository"
    assert artifacts.decisions.__class__.__name__ == "SQLAlchemyProgram2DecisionRepository"
    assert artifacts.artifacts.__class__.__name__ == "SQLAlchemyProgram2ArtifactRepository"
