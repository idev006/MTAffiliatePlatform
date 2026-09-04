from datetime import UTC, datetime

import pytest

from mtaffiliate.adapters.persistence.inmemory.job import InMemoryJobRepository
from mtaffiliate.adapters.persistence.inmemory.program1_strategy import (
    InMemoryProgram1StrategyRepository,
)
from mtaffiliate.application.program1_jobs import Program1DiscoveryJobService
from mtaffiliate.application.program1_strategy import Program1StrategyPlanner
from mtaffiliate.domain.job.models import JobState
from mtaffiliate.domain.program1.models import (
    AffiliateSuccessHypothesis,
    DiscoveryPlan,
    SignalRequirement,
)
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine

NOW = datetime(2026, 9, 4, tzinfo=UTC)


def hypothesis() -> AffiliateSuccessHypothesis:
    return AffiliateSuccessHypothesis(
        hypothesis_id="hyp-1",
        campaign_id="campaign-1",
        objective="Find products worth testing",
        decision_question="Which products deserve affiliate effort now?",
        rationale="Concentrate content effort on evidence-backed opportunities",
        target_outcome="candidate_hit_rate",
        policy_version="affiliate-strategy-v1",
        created_at=NOW,
    )


def signal(signal_id: str) -> SignalRequirement:
    return SignalRequirement(
        signal_id=signal_id,
        hypothesis_id="hyp-1",
        decision_supported="Which products deserve affiliate effort now?",
        expected_interpretation="signal supports test priority",
        evidence_source="approved product observations",
    )


def plan() -> DiscoveryPlan:
    return DiscoveryPlan(
        plan_id="plan-1",
        campaign_id="campaign-1",
        hypothesis_id="hyp-1",
        required_signal_ids=("demand", "contentability"),
        source_scope="shopee",
        surface_scope=("search",),
        capability_requirements=("collector:search-lab", "feature:pagination"),
        evidence_policy_version="evidence-v1",
        collection_policy_version="collection-v1",
        created_at=NOW,
    )


def service() -> tuple[Program1DiscoveryJobService, InMemoryJobRepository]:
    repo = InMemoryJobRepository()
    jobs = SharedJobEngine(repo, token_factory=lambda: "lease-1")
    return (
        Program1DiscoveryJobService(
            Program1StrategyPlanner(),
            InMemoryProgram1StrategyRepository(),
            jobs,
        ),
        repo,
    )


def test_strategy_approved_plan_creates_queued_shared_job() -> None:
    app, repo = service()

    job = app.create_discovery_job(
        hypothesis=hypothesis(),
        signals=[signal("contentability"), signal("demand")],
        discovery_plan=plan(),
        discovery_plan_ref="program1-plan:plan-1:v1",
        job_id="job-1",
        idempotency_key="campaign-1:plan-1",
        created_at=NOW,
    )

    assert job.state is JobState.QUEUED
    assert job.job_type == "DISCOVER_PRODUCTS"
    assert job.domain == "program1"
    assert job.payload_ref == "program1-plan:plan-1:v1"
    assert job.capability_requirements == (
        "collector:search-lab",
        "feature:pagination",
    )
    assert [event.event_type for event in repo.list_events("job-1")] == [
        "JOB_CREATED",
        "JOB_QUEUED",
    ]


def test_undeclared_signal_fails_before_job_is_created() -> None:
    app, repo = service()

    with pytest.raises(ValueError, match="not required by discovery plan"):
        app.create_discovery_job(
            hypothesis=hypothesis(),
            signals=[signal("demand"), signal("contentability"), signal("rating")],
            discovery_plan=plan(),
            discovery_plan_ref="program1-plan:plan-1:v1",
            job_id="job-1",
            idempotency_key="campaign-1:plan-1",
            created_at=NOW,
        )

    assert repo.list_jobs() == []


def test_blank_plan_reference_is_rejected() -> None:
    app, repo = service()

    with pytest.raises(ValueError, match="durable non-empty"):
        app.create_discovery_job(
            hypothesis=hypothesis(),
            signals=[signal("demand"), signal("contentability")],
            discovery_plan=plan(),
            discovery_plan_ref="   ",
            job_id="job-1",
            idempotency_key="campaign-1:plan-1",
            created_at=NOW,
        )

    assert repo.list_jobs() == []


def test_idempotent_retry_returns_existing_queued_job_without_extra_events() -> None:
    app, repo = service()
    kwargs = {
        "hypothesis": hypothesis(),
        "signals": [signal("demand"), signal("contentability")],
        "discovery_plan": plan(),
        "discovery_plan_ref": "program1-plan:plan-1:v1",
        "job_id": "job-1",
        "idempotency_key": "campaign-1:plan-1",
        "created_at": NOW,
    }

    first = app.create_discovery_job(**kwargs)
    retry = app.create_discovery_job(**{**kwargs, "job_id": "job-retry"})

    assert retry == first
    assert len(repo.list_jobs()) == 1
    assert [event.event_type for event in repo.list_events("job-1")] == [
        "JOB_CREATED",
        "JOB_QUEUED",
    ]
