from datetime import UTC, datetime, timedelta

import pytest

from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository
from mtaffiliate.adapters.persistence.inmemory.program1_strategy import (
    InMemoryProgram1StrategyRepository,
)
from mtaffiliate.application.program1_strategy import StrategyToWorkResult
from mtaffiliate.domain.job.models import JobEvent, JobRecord, JobState
from mtaffiliate.domain.program1.models import (
    AffiliateSuccessHypothesis,
    DiscoveryPlan,
    SignalRequirement,
)
from mtaffiliate.engines.shared_job_engine.service import (
    IdempotencyConflictError,
    InvalidJobTransitionError,
    SharedJobEngine,
)
from mtaffiliate.ports.repositories.job import JobRepositoryConflictError
from mtaffiliate.ports.repositories.program1_strategy import StrategyWorkConflictError

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


def job(
    *,
    job_id: str = "job-1",
    idempotency_key: str = "idem-1",
    version: int = 1,
    state: JobState = JobState.CREATED,
) -> JobRecord:
    return JobRecord(
        job_id=job_id,
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="plan:1",
        idempotency_key=idempotency_key,
        state=state,
        job_version=version,
        created_at=NOW,
        updated_at=NOW,
    )


def event(item: JobRecord, *, event_type: str = "JOB_CREATED") -> JobEvent:
    return JobEvent(
        event_type=event_type,
        job_id=item.job_id,
        job_version=item.job_version,
        emitted_at=NOW,
    )


def strategy_package(*, objective: str = "Find products") -> StrategyToWorkResult:
    hypothesis = AffiliateSuccessHypothesis(
        hypothesis_id="hyp-1",
        campaign_id="campaign-1",
        objective=objective,
        decision_question="Which products deserve effort?",
        rationale="Synthetic verification",
        target_outcome="candidate_hit_rate",
        policy_version="v1",
        created_at=NOW,
    )
    signal = SignalRequirement(
        signal_id="demand",
        hypothesis_id="hyp-1",
        decision_supported=hypothesis.decision_question,
        expected_interpretation="higher demand raises priority",
        evidence_source="synthetic",
    )
    plan = DiscoveryPlan(
        plan_id="plan-1",
        campaign_id="campaign-1",
        hypothesis_id="hyp-1",
        required_signal_ids=("demand",),
        source_scope="synthetic",
        surface_scope=("search",),
        evidence_policy_version="evidence-v1",
        collection_policy_version="collection-v1",
        created_at=NOW,
    )
    return StrategyToWorkResult(
        hypothesis=hypothesis,
        signals=(signal,),
        discovery_plan=plan,
    )


def test_inmemory_job_repository_conflict_and_validation_branches() -> None:
    repo = InMemoryJobRepository()
    first = job()
    repo.add_with_event(first, event(first))

    assert repo.get_by_idempotency_key("missing") is None
    assert repo.list_events("missing") == []

    with pytest.raises(JobRepositoryConflictError, match="job already exists"):
        repo.add_with_event(first, event(first))

    duplicate_key = job(job_id="job-2")
    with pytest.raises(JobRepositoryConflictError, match="idempotency key already exists"):
        repo.add_with_event(duplicate_key, event(duplicate_key))

    mismatch = job(job_id="job-3", idempotency_key="idem-3")
    wrong_event = JobEvent(
        event_type="JOB_CREATED",
        job_id="wrong",
        job_version=1,
        emitted_at=NOW,
    )
    with pytest.raises(ValueError, match="must match added job"):
        repo.add_with_event(mismatch, wrong_event)

    missing = job(job_id="missing", idempotency_key="missing")
    with pytest.raises(KeyError):
        repo.replace_with_event(missing, event(missing), expected_version=1)

    updated = first.model_copy(update={"job_version": 2, "updated_at": NOW})
    with pytest.raises(JobRepositoryConflictError, match="stale job version"):
        repo.replace_with_event(updated, event(updated), expected_version=0)

    wrong_version_event = JobEvent(
        event_type="JOB_QUEUED",
        job_id=updated.job_id,
        job_version=99,
        emitted_at=NOW,
    )
    with pytest.raises(ValueError, match="must match replacement job"):
        repo.replace_with_event(
            updated,
            wrong_version_event,
            expected_version=first.job_version,
        )


def test_inmemory_strategy_repository_is_idempotent_and_conflict_safe() -> None:
    repo = InMemoryProgram1StrategyRepository()
    package = strategy_package()

    with pytest.raises(ValueError, match="non-empty"):
        repo.put("   ", package)

    repo.put("plan-ref", package)
    repo.put("plan-ref", package)
    assert repo.get("plan-ref") == package
    assert repo.get("missing") is None

    with pytest.raises(StrategyWorkConflictError):
        repo.put("plan-ref", strategy_package(objective="Different objective"))


def test_shared_job_negative_duration_unknown_job_and_cancel_paths() -> None:
    repo = InMemoryJobRepository()
    shared = SharedJobEngine(repo, token_factory=lambda: "lease-1")

    with pytest.raises(ValueError, match="positive"):
        shared.lease_next(
            worker_id="worker-1",
            worker_capabilities=set(),
            at=NOW,
            lease_for=timedelta(0),
        )

    with pytest.raises(KeyError):
        shared.queue_job("missing", at=NOW)

    created = shared.create_job(
        job_id="job-1",
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="plan:1",
        idempotency_key="idem-1",
        created_at=NOW,
    )
    cancelled = shared.cancel_job(created.job_id, at=NOW)
    assert cancelled.state is JobState.CANCELLED

    with pytest.raises(InvalidJobTransitionError):
        shared.queue_job(created.job_id, at=NOW)


def test_shared_job_renew_and_not_yet_expired_requeue_paths() -> None:
    repo = InMemoryJobRepository()
    shared = SharedJobEngine(repo, token_factory=lambda: "lease-1")
    shared.create_job(
        job_id="job-1",
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="plan:1",
        idempotency_key="idem-1",
        created_at=NOW,
    )
    shared.queue_job("job-1", at=NOW)

    with pytest.raises(ValueError, match="positive"):
        shared.lease_job(
            "job-1",
            worker_id="worker-1",
            worker_capabilities=set(),
            at=NOW,
            lease_for=timedelta(0),
        )

    leased = shared.lease_job(
        "job-1",
        worker_id="worker-1",
        worker_capabilities=set(),
        at=NOW,
        lease_for=timedelta(seconds=30),
    )

    with pytest.raises(ValueError, match="positive"):
        shared.renew_lease(
            "job-1",
            worker_id="worker-1",
            lease_token=leased.lease_token or "",
            at=NOW + timedelta(seconds=1),
            lease_for=timedelta(0),
        )

    renewed = shared.renew_lease(
        "job-1",
        worker_id="worker-1",
        lease_token=leased.lease_token or "",
        at=NOW + timedelta(seconds=1),
        lease_for=timedelta(minutes=2),
    )
    assert renewed.lease_until == NOW + timedelta(seconds=121)

    with pytest.raises(InvalidJobTransitionError, match="has not expired"):
        shared.requeue_expired(
            "job-1",
            at=NOW + timedelta(seconds=2),
            safe_to_reassign=True,
        )


def test_lease_next_returns_none_when_no_compatible_job_exists() -> None:
    repo = InMemoryJobRepository()
    shared = SharedJobEngine(repo)
    shared.create_job(
        job_id="job-1",
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="plan:1",
        idempotency_key="idem-1",
        capability_requirements=("collector:required",),
        created_at=NOW,
    )
    shared.queue_job("job-1", at=NOW)

    assert (
        shared.lease_next(
            worker_id="worker-1",
            worker_capabilities={"collector:other"},
            at=NOW,
            lease_for=timedelta(minutes=1),
        )
        is None
    )


class _RaceRepository(InMemoryJobRepository):
    def __init__(self, raced: JobRecord | None) -> None:
        super().__init__()
        self.raced = raced

    def get_by_idempotency_key(self, idempotency_key: str) -> JobRecord | None:
        return self.raced

    def add_with_event(self, item: JobRecord, item_event: JobEvent) -> None:
        raise JobRepositoryConflictError("simulated race")


def test_create_job_recovers_idempotent_race_and_rejects_raced_semantic_conflict() -> None:
    raced = job()
    shared = SharedJobEngine(_RaceRepository(raced))
    replay = shared.create_job(
        job_id="retry",
        job_type="DISCOVER_PRODUCTS",
        domain="program1",
        payload_ref="plan:1",
        idempotency_key="idem-1",
        created_at=NOW,
    )
    assert replay == raced

    conflicting = raced.model_copy(update={"payload_ref": "different"})
    with pytest.raises(IdempotencyConflictError):
        SharedJobEngine(_RaceRepository(conflicting)).create_job(
            job_id="retry",
            job_type="DISCOVER_PRODUCTS",
            domain="program1",
            payload_ref="plan:1",
            idempotency_key="idem-1",
            created_at=NOW,
        )

    with pytest.raises(JobRepositoryConflictError):
        SharedJobEngine(_RaceRepository(None)).create_job(
            job_id="retry",
            job_type="DISCOVER_PRODUCTS",
            domain="program1",
            payload_ref="plan:1",
            idempotency_key="idem-1",
            created_at=NOW,
        )
