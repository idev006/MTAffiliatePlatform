from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.factory import (
    build_engine,
    build_session_factory,
)
from mtaffiliate.adapters.persistence.sqlalchemy.ingestion import (
    SQLAlchemyProgram1BatchIngestor,
)
from mtaffiliate.adapters.persistence.sqlalchemy.job import SQLAlchemyJobRepository
from mtaffiliate.adapters.persistence.sqlalchemy.product import SQLAlchemyProductRepository
from mtaffiliate.adapters.persistence.sqlalchemy.program1_strategy import (
    SQLAlchemyProgram1StrategyRepository,
)
from mtaffiliate.adapters.persistence.sqlalchemy.worker_registry import (
    SQLAlchemyWorkerRegistryRepository,
)
from mtaffiliate.application.program1 import Program1Service
from mtaffiliate.application.program1_jobs import Program1DiscoveryJobService
from mtaffiliate.application.program1_strategy import Program1StrategyPlanner
from mtaffiliate.application.worker_registry import WorkerRegistryService
from mtaffiliate.domain.job.models import JobState
from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.domain.program1.models import (
    AffiliateSuccessHypothesis,
    DiscoveryPlan,
    SignalRequirement,
)
from mtaffiliate.domain.worker_registry.models import WorkerRegistration, WorkerType
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)
from mtaffiliate.engines.shared_job_engine.service import (
    InvalidJobTransitionError,
    SharedJobEngine,
)
from mtaffiliate.ports.repositories.ingestion import IngestionBatchConflictError

pytestmark = pytest.mark.integration

T0 = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
LEASE = timedelta(minutes=2)
DB_URL = "sqlite:///data/program1-world-class-simulation.db"


def hypothesis() -> AffiliateSuccessHypothesis:
    return AffiliateSuccessHypothesis(
        hypothesis_id="hyp-world-1",
        campaign_id="campaign-world-1",
        objective="Find evidence-backed products worth affiliate effort",
        decision_question="Which observed products deserve content effort now?",
        rationale="Allocate scarce content effort using reproducible evidence",
        target_outcome="candidate_hit_rate",
        audience_context="synthetic Thai marketplace lab",
        policy_version="affiliate-strategy-v1",
        created_at=T0,
    )


def signals() -> list[SignalRequirement]:
    return [
        SignalRequirement(
            signal_id="demand",
            hypothesis_id="hyp-world-1",
            decision_supported="Which observed products deserve content effort now?",
            expected_interpretation="higher observed demand increases test priority",
            evidence_source="synthetic product observations",
        ),
        SignalRequirement(
            signal_id="quality",
            hypothesis_id="hyp-world-1",
            decision_supported="Which observed products deserve content effort now?",
            expected_interpretation="rating/reviews support confidence",
            evidence_source="synthetic product observations",
        ),
    ]


def discovery_plan() -> DiscoveryPlan:
    return DiscoveryPlan(
        plan_id="plan-world-1",
        campaign_id="campaign-world-1",
        hypothesis_id="hyp-world-1",
        required_signal_ids=("demand", "quality"),
        source_scope="synthetic-shopee-lab",
        surface_scope=("search",),
        capability_requirements=("collector:search-lab",),
        evidence_policy_version="evidence-v1",
        collection_policy_version="collection-v1",
        created_at=T0,
    )


def observations() -> list[ProductObservation]:
    return [
        ProductObservation(
            observation_id="obs-world-1",
            platform="shopee",
            shop_id="shop-a",
            item_id="item-a",
            collected_at=T0 + timedelta(seconds=30),
            product_name="Synthetic SSD A",
            product_url="https://example.invalid/item-a",
            price_current=Decimal("1590.00"),
            sold_signal=920,
            rating=4.9,
            review_count=490,
            source_worker_id="worker-world-1",
            source_query="ssd",
            extractor_version="synthetic-v1",
        ),
        ProductObservation(
            observation_id="obs-world-2",
            platform="shopee",
            shop_id="shop-b",
            item_id="item-b",
            collected_at=T0 + timedelta(seconds=31),
            product_name="Synthetic SSD B",
            product_url="https://example.invalid/item-b",
            price_current=Decimal("1290.00"),
            sold_signal=300,
            rating=4.6,
            review_count=160,
            source_worker_id="worker-world-1",
            source_query="ssd",
            extractor_version="synthetic-v1",
        ),
        ProductObservation(
            observation_id="obs-world-3",
            platform="shopee",
            shop_id="shop-c",
            item_id="item-c",
            collected_at=T0 + timedelta(seconds=32),
            product_name="Synthetic SSD C",
            product_url="https://example.invalid/item-c",
            price_current=None,
            sold_signal=50,
            rating=4.0,
            review_count=30,
            source_worker_id="worker-world-1",
            source_query="ssd",
            extractor_version="synthetic-v1",
        ),
    ]


def compose(tmp_path):
    engine = build_engine(DB_URL, project_root=tmp_path)
    Base.metadata.create_all(engine)
    sessions = build_session_factory(engine)

    job_repo = SQLAlchemyJobRepository(sessions)
    strategy_repo = SQLAlchemyProgram1StrategyRepository(sessions)
    product_repo = SQLAlchemyProductRepository(sessions)
    registry_repo = SQLAlchemyWorkerRegistryRepository(sessions)

    jobs = SharedJobEngine(job_repo, token_factory=lambda: "lease-world-1")
    discovery_jobs = Program1DiscoveryJobService(
        Program1StrategyPlanner(),
        strategy_repo,
        jobs,
    )
    registry = WorkerRegistryService(
        registry_repo,
        stale_after=timedelta(minutes=5),
    )
    program1 = Program1Service(
        product_repo,
        ProductIntelligenceEngine(ScoringPolicy()),
        shortlist_limit=10,
        minimum_score=0.0,
        batch_ingestor=SQLAlchemyProgram1BatchIngestor(sessions),
    )
    return engine, jobs, discovery_jobs, registry, program1, strategy_repo


def register_worker(registry: WorkerRegistryService) -> None:
    registry.register(
        WorkerRegistration(
            worker_id="worker-world-1",
            worker_type=WorkerType.DISCOVERY_BROWSER_WORKER,
            installation_id="install-world-1",
            version="simulation-v1",
            capabilities=["collector:search-lab"],
        ),
        seen_at=T0,
    )


def test_program1_complete_headless_business_flow_survives_restart(tmp_path) -> None:
    engine, jobs, discovery_jobs, registry, program1, _strategy_repo = compose(tmp_path)
    register_worker(registry)

    queued = discovery_jobs.create_discovery_job(
        hypothesis=hypothesis(),
        signals=signals(),
        discovery_plan=discovery_plan(),
        discovery_plan_ref="program1-plan:plan-world-1:v1",
        job_id="job-world-1",
        idempotency_key="campaign-world-1:plan-world-1",
        created_at=T0,
        priority=10,
    )
    assert queued.state is JobState.QUEUED

    worker = registry.execution_record("worker-world-1", now=T0 + timedelta(seconds=1))
    leased = jobs.lease_next(
        worker_id=worker.worker_id,
        worker_capabilities=set(worker.capabilities),
        at=T0 + timedelta(seconds=1),
        lease_for=LEASE,
    )
    assert leased is not None
    assert leased.job_id == "job-world-1"

    started = jobs.start_job(
        leased.job_id,
        worker_id=worker.worker_id,
        lease_token=leased.lease_token or "",
        at=T0 + timedelta(seconds=2),
    )
    assert started.state is JobState.IN_PROGRESS

    first_ingest = program1.ingest_batch("batch-world-1", observations())
    assert first_ingest.received_count == 3
    assert first_ingest.accepted_count == 3

    checkpointed = jobs.record_checkpoint(
        started.job_id,
        worker_id=worker.worker_id,
        lease_token=started.lease_token or "",
        checkpoint_type="COLLECTION_BATCH_ACK",
        payload={
            "batch_id": "batch-world-1",
            "received_count": first_ingest.received_count,
            "accepted_count": first_ingest.accepted_count,
        },
        at=T0 + timedelta(seconds=40),
    )
    assert checkpointed.checkpoint is not None

    shortlist_before_restart = program1.build_shortlist()
    assert [entry.product_key[-1] for entry in shortlist_before_restart] == [
        "item-a",
        "item-b",
        "item-c",
    ]
    assert shortlist_before_restart[0].score > shortlist_before_restart[1].score

    verifying = jobs.begin_verification(
        started.job_id,
        worker_id=worker.worker_id,
        lease_token=started.lease_token or "",
        at=T0 + timedelta(seconds=41),
    )
    completed = jobs.complete_job(
        started.job_id,
        worker_id=worker.worker_id,
        lease_token=verifying.lease_token or "",
        at=T0 + timedelta(seconds=42),
    )
    assert completed.state is JobState.COMPLETED
    engine.dispose()

    restarted_engine, restarted_jobs, _discovery, _registry, restarted_program1, restarted_strategy = compose(
        tmp_path
    )
    durable_job = restarted_jobs.repository.get("job-world-1")
    assert durable_job is not None
    assert durable_job.state is JobState.COMPLETED
    assert durable_job.checkpoint is not None
    assert durable_job.checkpoint.payload["batch_id"] == "batch-world-1"

    restored_package = restarted_strategy.get("program1-plan:plan-world-1:v1")
    assert restored_package is not None
    assert restored_package.discovery_plan == discovery_plan()

    replay = restarted_program1.ingest_batch("batch-world-1", observations())
    assert replay.received_count == 3
    assert replay.accepted_count == 3

    shortlist_after_restart = restarted_program1.build_shortlist()
    assert shortlist_after_restart == shortlist_before_restart

    assert [
        event.event_type
        for event in restarted_jobs.repository.list_events("job-world-1")
    ] == [
        "JOB_CREATED",
        "JOB_QUEUED",
        "JOB_LEASED",
        "JOB_STARTED",
        "CHECKPOINT_RECORDED",
        "JOB_VERIFYING",
        "JOB_COMPLETED",
    ]
    restarted_engine.dispose()


def test_program1_rejects_batch_id_reuse_with_different_payload(tmp_path) -> None:
    engine, _jobs, _discovery, _registry, program1, _strategy = compose(tmp_path)
    program1.ingest_batch("batch-world-1", observations())

    conflicting = observations()
    conflicting[0] = conflicting[0].model_copy(
        update={"product_name": "Tampered Product Name"}
    )
    with pytest.raises(IngestionBatchConflictError):
        program1.ingest_batch("batch-world-1", conflicting)
    engine.dispose()


def test_program1_expired_unsafe_execution_escalates_instead_of_replaying(tmp_path) -> None:
    engine, jobs, discovery_jobs, registry, _program1, _strategy = compose(tmp_path)
    register_worker(registry)
    discovery_jobs.create_discovery_job(
        hypothesis=hypothesis(),
        signals=signals(),
        discovery_plan=discovery_plan(),
        discovery_plan_ref="program1-plan:plan-world-1:v1",
        job_id="job-world-unsafe",
        idempotency_key="campaign-world-1:unsafe",
        created_at=T0,
    )
    worker = registry.execution_record("worker-world-1", now=T0)
    leased = jobs.lease_next(
        worker_id=worker.worker_id,
        worker_capabilities=set(worker.capabilities),
        at=T0,
        lease_for=timedelta(seconds=10),
    )
    assert leased is not None
    jobs.start_job(
        leased.job_id,
        worker_id=worker.worker_id,
        lease_token=leased.lease_token or "",
        at=T0 + timedelta(seconds=1),
    )

    escalated = jobs.requeue_expired(
        leased.job_id,
        at=T0 + timedelta(seconds=10),
        safe_to_reassign=False,
    )
    assert escalated.state is JobState.NEEDS_HUMAN
    assert escalated.failure_code == "LEASE_EXPIRED_UNSAFE_TO_REASSIGN"

    with pytest.raises(InvalidJobTransitionError, match="NEEDS_HUMAN"):
        jobs.record_checkpoint(
            leased.job_id,
            worker_id=worker.worker_id,
            lease_token=leased.lease_token or "",
            checkpoint_type="SHOULD_NOT_WRITE",
            payload={},
            at=T0 + timedelta(seconds=11),
        )
    engine.dispose()


def test_program1_duplicate_job_request_is_idempotent_and_does_not_duplicate_work(tmp_path) -> None:
    engine, jobs, discovery_jobs, _registry, _program1, _strategy = compose(tmp_path)

    kwargs = {
        "hypothesis": hypothesis(),
        "signals": signals(),
        "discovery_plan": discovery_plan(),
        "discovery_plan_ref": "program1-plan:plan-world-1:v1",
        "job_id": "job-world-1",
        "idempotency_key": "campaign-world-1:plan-world-1",
        "created_at": T0,
    }
    first = discovery_jobs.create_discovery_job(**kwargs)
    replay = discovery_jobs.create_discovery_job(
        **{**kwargs, "job_id": "job-world-retry"}
    )

    assert first == replay
    assert len(jobs.repository.list_jobs()) == 1
    assert [
        event.event_type
        for event in jobs.repository.list_events("job-world-1")
    ] == ["JOB_CREATED", "JOB_QUEUED"]
    engine.dispose()
