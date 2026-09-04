from pathlib import Path

import pytest

from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository
from mtaffiliate.bootstrap.config import DatabaseConfig, Settings
from mtaffiliate.bootstrap.program3_authority import build_durable_program3_authority
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine

pytestmark = pytest.mark.integration


def test_program3_authority_bootstrap_composes_sql_adapters(tmp_path: Path) -> None:
    settings = Settings(database=DatabaseConfig(url="sqlite:///data/program3-bootstrap.db"))
    jobs = SharedJobEngine(InMemoryJobRepository())

    service = build_durable_program3_authority(
        settings,
        project_root=tmp_path,
        jobs=jobs,
    )

    assert service.jobs is jobs
    assert service.decisions.__class__.__name__ == "SQLAlchemyProgram2DecisionRepository"
    assert service.artifacts.__class__.__name__ == "SQLAlchemyProgram2ArtifactRepository"
    assert service.execution.__class__.__name__ == "SQLAlchemyProgram3ExecutionRepository"
    assert service.ledger.__class__.__name__ == "SQLAlchemyPublishingLedgerRepository"
    assert service.devices.repository.__class__.__name__ == "SQLAlchemyDeviceRepository"
