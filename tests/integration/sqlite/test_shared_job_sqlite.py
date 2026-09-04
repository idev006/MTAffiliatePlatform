from datetime import UTC, datetime, timedelta

import pytest

from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.factory import (
    build_engine,
    build_session_factory,
)
from mtaffiliate.adapters.persistence.sqlalchemy.job import SQLAlchemyJobRepository
from mtaffiliate.domain.job.models import JobState
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine
from mtaffiliate.ports.repositories.job import JobRepositoryConflictError

pytestmark = pytest.mark.integration

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
LEASE = timedelta(minutes=5)


def build(tmp_path):
    engine = build_engine("sqlite:///data/shared-jobs.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    repo = SQLAlchemyJobRepository(build_session_factory(engine))
    shared = SharedJobEngine(repo, token_factory=lambda: "lease-1")
    return engine, repo, shared


def test_job_checkpoint_and_events_survive_runtime_recomposition(tmp_path) -> None:
    engine, _repo, shared = build(tmp_path)

    shared.create_job(
        job_id="job-1",
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="program1-plan:plan-1:v1",
        idempotency_key="idem-1",
        capability_requirements=("collector:search-lab",),
        created_at=NOW,
    )
    shared.queue_job("job-1", at=NOW)
    leased = shared.lease_job(
        "job-1",
        worker_id="worker-1",
        worker_capabilities={"collector:search-lab"},
        at=NOW,
        lease_for=LEASE,
    )
    started = shared.start_job(
        "job-1",
        worker_id="worker-1",
        lease_token=leased.lease_token or "",
        at=NOW + timedelta(seconds=1),
    )
    checkpointed = shared.record_checkpoint(
        "job-1",
        worker_id="worker-1",
        lease_token=started.lease_token or "",
        checkpoint_type="PAGE",
        payload={"page": 3, "cursor": "abc"},
        at=NOW + timedelta(seconds=2),
    )
    assert checkpointed.state is JobState.IN_PROGRESS
    engine.dispose()

    restarted_engine = build_engine(
        "sqlite:///data/shared-jobs.db",
        project_root=tmp_path,
    )
    restarted_repo = SQLAlchemyJobRepository(build_session_factory(restarted_engine))
    job = restarted_repo.get("job-1")
    assert job is not None
    assert job.state is JobState.IN_PROGRESS
    assert job.checkpoint is not None
    assert job.checkpoint.payload == {"page": 3, "cursor": "abc"}
    assert job.lease_token == "lease-1"
    assert [event.event_type for event in restarted_repo.list_events("job-1")] == [
        "JOB_CREATED",
        "JOB_QUEUED",
        "JOB_LEASED",
        "JOB_STARTED",
        "CHECKPOINT_RECORDED",
    ]
    restarted_engine.dispose()


def test_state_and_event_are_atomic_on_stale_version_conflict(tmp_path) -> None:
    engine, repo, shared = build(tmp_path)

    created = shared.create_job(
        job_id="job-1",
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="program1-plan:plan-1:v1",
        idempotency_key="idem-1",
        created_at=NOW,
    )
    queued = shared.queue_job("job-1", at=NOW)

    stale_update = queued.model_copy(
        update={
            "state": JobState.CANCELLED,
            "job_version": queued.job_version + 1,
            "updated_at": NOW + timedelta(seconds=1),
        }
    )
    event = repo.list_events("job-1")[-1].model_copy(
        update={
            "event_type": "JOB_CANCELLED",
            "job_version": stale_update.job_version,
            "emitted_at": NOW + timedelta(seconds=1),
        }
    )

    with pytest.raises(JobRepositoryConflictError):
        repo.replace_with_event(
            stale_update,
            event,
            expected_version=created.job_version,
        )

    durable = repo.get("job-1")
    assert durable is not None
    assert durable.state is JobState.QUEUED
    assert [event.event_type for event in repo.list_events("job-1")] == [
        "JOB_CREATED",
        "JOB_QUEUED",
    ]
    engine.dispose()


def test_sql_repository_preserves_idempotent_create_across_restart(tmp_path) -> None:
    engine, _repo, shared = build(tmp_path)
    first = shared.create_job(
        job_id="job-1",
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="program1-plan:plan-1:v1",
        idempotency_key="idem-1",
        created_at=NOW,
    )
    engine.dispose()

    restarted_engine = build_engine(
        "sqlite:///data/shared-jobs.db",
        project_root=tmp_path,
    )
    restarted_repo = SQLAlchemyJobRepository(build_session_factory(restarted_engine))
    restarted = SharedJobEngine(restarted_repo, token_factory=lambda: "lease-2")

    replay = restarted.create_job(
        job_id="job-retry",
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="program1-plan:plan-1:v1",
        idempotency_key="idem-1",
        created_at=NOW + timedelta(minutes=1),
    )
    assert replay == first
    assert len(restarted_repo.list_jobs()) == 1
    assert len(restarted_repo.list_events("job-1")) == 1
    restarted_engine.dispose()
