from datetime import UTC, datetime, timedelta

import pytest

from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository
from mtaffiliate.domain.job.models import JobState
from mtaffiliate.engines.shared_job_engine.service import (
    IdempotencyConflictError,
    InvalidJobTransitionError,
    SharedJobEngine,
    StaleLeaseError,
)


NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
LEASE = timedelta(minutes=5)


def engine() -> tuple[SharedJobEngine, InMemoryJobRepository]:
    repo = InMemoryJobRepository()
    tokens = iter(["lease-1", "lease-2", "lease-3"])
    return SharedJobEngine(repo, token_factory=lambda: next(tokens)), repo


def queued_job(
    shared: SharedJobEngine,
    *,
    job_id: str = "job-1",
    idempotency_key: str = "idem-1",
):
    shared.create_job(
        job_id=job_id,
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="discovery-plan:plan-1",
        idempotency_key=idempotency_key,
        capability_requirements=("collector:identity",),
        created_at=NOW,
    )
    return shared.queue_job(job_id, at=NOW)


def lease_started(shared: SharedJobEngine):
    queued_job(shared)
    leased = shared.lease_job(
        "job-1",
        worker_id="worker-1",
        worker_capabilities={"collector:identity", "collector:fixture"},
        at=NOW,
        lease_for=LEASE,
    )
    started = shared.start_job(
        "job-1",
        worker_id="worker-1",
        lease_token=leased.lease_token or "",
        at=NOW + timedelta(seconds=1),
    )
    return started


def test_full_headless_job_lifecycle_records_append_only_events() -> None:
    shared, repo = engine()
    started = lease_started(shared)

    checkpointed = shared.record_checkpoint(
        "job-1",
        worker_id="worker-1",
        lease_token=started.lease_token or "",
        checkpoint_type="PAGE",
        payload={"page": 1},
        at=NOW + timedelta(seconds=2),
    )
    verifying = shared.begin_verification(
        "job-1",
        worker_id="worker-1",
        lease_token=checkpointed.lease_token or "",
        at=NOW + timedelta(seconds=3),
    )
    completed = shared.complete_job(
        "job-1",
        worker_id="worker-1",
        lease_token=verifying.lease_token or "",
        at=NOW + timedelta(seconds=4),
    )

    assert completed.state is JobState.COMPLETED
    assert completed.assigned_worker_id is None
    assert completed.checkpoint is not None
    assert completed.checkpoint.payload == {"page": 1}
    assert [event.event_type for event in repo.list_events("job-1")] == [
        "JOB_CREATED",
        "JOB_QUEUED",
        "JOB_LEASED",
        "JOB_STARTED",
        "CHECKPOINT_RECORDED",
        "JOB_VERIFYING",
        "JOB_COMPLETED",
    ]
    assert [event.job_version for event in repo.list_events("job-1")] == list(
        range(1, 8)
    )


def test_pause_releases_lease_and_resume_requires_reacquisition() -> None:
    shared, _repo = engine()
    started = lease_started(shared)
    paused = shared.pause_job("job-1", at=NOW + timedelta(seconds=2))

    assert paused.state is JobState.PAUSED
    assert paused.lease_token is None
    assert paused.assigned_worker_id is None

    with pytest.raises(StaleLeaseError):
        shared.record_checkpoint(
            "job-1",
            worker_id="worker-1",
            lease_token=started.lease_token or "",
            checkpoint_type="PAGE",
            payload={"page": 2},
            at=NOW + timedelta(seconds=3),
        )

    resumed = shared.resume_job("job-1", at=NOW + timedelta(seconds=4))
    assert resumed.state is JobState.QUEUED

    leased_again = shared.lease_job(
        "job-1",
        worker_id="worker-1",
        worker_capabilities={"collector:identity"},
        at=NOW + timedelta(seconds=5),
        lease_for=LEASE,
    )
    assert leased_again.lease_token == "lease-2"
    assert leased_again.attempt_no == 2


def test_lease_is_expired_at_exact_expiry_boundary() -> None:
    shared, _repo = engine()
    queued_job(shared)
    leased = shared.lease_job(
        "job-1",
        worker_id="worker-1",
        worker_capabilities={"collector:identity"},
        at=NOW,
        lease_for=LEASE,
    )

    with pytest.raises(StaleLeaseError, match="expired"):
        shared.start_job(
            "job-1",
            worker_id="worker-1",
            lease_token=leased.lease_token or "",
            at=NOW + LEASE,
        )

    requeued = shared.requeue_expired(
        "job-1",
        at=NOW + LEASE,
        safe_to_reassign=True,
    )
    assert requeued.state is JobState.QUEUED
    assert requeued.lease_token is None


def test_expired_unsafe_job_escalates_instead_of_reassigning() -> None:
    shared, _repo = engine()
    started = lease_started(shared)

    escalated = shared.requeue_expired(
        "job-1",
        at=(started.lease_until or NOW) + timedelta(seconds=1),
        safe_to_reassign=False,
    )

    assert escalated.state is JobState.NEEDS_HUMAN
    assert escalated.failure_code == "LEASE_EXPIRED_UNSAFE_TO_REASSIGN"


def test_fail_job_clears_lease_and_records_reason() -> None:
    shared, repo = engine()
    started = lease_started(shared)

    failed = shared.fail_job(
        "job-1",
        failure_code="COLLECTION_FAILED",
        detail="fixture parser failed",
        at=NOW + timedelta(seconds=2),
    )

    assert failed.state is JobState.FAILED
    assert failed.lease_token is None
    assert failed.assigned_worker_id is None
    assert failed.failure_code == "COLLECTION_FAILED"
    assert repo.list_events("job-1")[-1].event_type == "JOB_FAILED"


def test_stale_worker_or_token_cannot_mutate_job() -> None:
    shared, _repo = engine()
    started = lease_started(shared)

    with pytest.raises(StaleLeaseError):
        shared.record_checkpoint(
            "job-1",
            worker_id="worker-other",
            lease_token=started.lease_token or "",
            checkpoint_type="PAGE",
            payload={},
            at=NOW + timedelta(seconds=2),
        )

    with pytest.raises(StaleLeaseError):
        shared.record_checkpoint(
            "job-1",
            worker_id="worker-1",
            lease_token="wrong",
            checkpoint_type="PAGE",
            payload={},
            at=NOW + timedelta(seconds=2),
        )


def test_worker_must_satisfy_job_capabilities() -> None:
    shared, _repo = engine()
    queued_job(shared)

    with pytest.raises(InvalidJobTransitionError, match="lacks required capabilities"):
        shared.lease_job(
            "job-1",
            worker_id="worker-1",
            worker_capabilities={"collector:fixture"},
            at=NOW,
            lease_for=LEASE,
        )


def test_create_is_idempotent_only_for_same_job_semantics() -> None:
    shared, repo = engine()
    first = shared.create_job(
        job_id="job-1",
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="discovery-plan:plan-1",
        idempotency_key="idem-1",
        created_at=NOW,
    )
    replay = shared.create_job(
        job_id="job-retry-can-differ",
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="discovery-plan:plan-1",
        idempotency_key="idem-1",
        created_at=NOW + timedelta(seconds=1),
    )
    assert replay == first
    assert len(repo.list_jobs()) == 1
    assert len(repo.list_events("job-1")) == 1

    with pytest.raises(IdempotencyConflictError):
        shared.create_job(
            job_id="job-other",
            job_type="DISCOVER_PRODUCTS",
            domain="program1",
            payload_ref="discovery-plan:plan-other",
            idempotency_key="idem-1",
            created_at=NOW,
        )


def test_invalid_state_transition_is_rejected() -> None:
    shared, _repo = engine()
    shared.create_job(
        job_id="job-1",
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="discovery-plan:plan-1",
        idempotency_key="idem-1",
        created_at=NOW,
    )

    with pytest.raises(InvalidJobTransitionError):
        shared.complete_job(
            "job-1",
            worker_id="worker-1",
            lease_token="none",
            at=NOW,
        )
