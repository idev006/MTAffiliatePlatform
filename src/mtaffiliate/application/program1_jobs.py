from __future__ import annotations

from datetime import datetime

from mtaffiliate.application.program1_strategy import Program1StrategyPlanner
from mtaffiliate.domain.job.models import JobRecord, JobState
from mtaffiliate.domain.program1.models import (
    AffiliateSuccessHypothesis,
    DiscoveryPlan,
    SignalRequirement,
)
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine
from mtaffiliate.ports.repositories.program1_strategy import Program1StrategyRepository


class Program1DiscoveryJobService:
    """Bind approved Program 1 strategy work to the shared job lifecycle."""

    JOB_TYPE = "DISCOVER_PRODUCTS"
    DOMAIN = "program1"

    def __init__(
        self,
        strategy_planner: Program1StrategyPlanner,
        strategy_repository: Program1StrategyRepository,
        jobs: SharedJobEngine,
    ) -> None:
        self.strategy_planner = strategy_planner
        self.strategy_repository = strategy_repository
        self.jobs = jobs

    def list_discovery_jobs(
        self, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[JobRecord], int]:
        if not 1 <= limit <= 100 or offset < 0:
            raise ValueError("limit must be 1..100 and offset non-negative")
        matching = sorted(
            (
                job
                for job in self.jobs.repository.list_jobs()
                if job.domain == self.DOMAIN and job.job_type == self.JOB_TYPE
            ),
            key=lambda job: (job.created_at, job.job_id),
            reverse=True,
        )
        return matching[offset : offset + limit], len(matching)

    def create_discovery_job(
        self,
        *,
        hypothesis: AffiliateSuccessHypothesis,
        signals: list[SignalRequirement],
        discovery_plan: DiscoveryPlan,
        discovery_plan_ref: str,
        job_id: str,
        idempotency_key: str,
        created_at: datetime,
        priority: int = 0,
    ) -> JobRecord:
        if not discovery_plan_ref.strip():
            raise ValueError("discovery_plan_ref must be a durable non-empty reference")

        approved = self.strategy_planner.build(
            hypothesis=hypothesis,
            signals=signals,
            discovery_plan=discovery_plan,
        )
        self.strategy_repository.put(discovery_plan_ref, approved)
        created = self.jobs.create_job(
            job_id=job_id,
            job_type=self.JOB_TYPE,
            domain=self.DOMAIN,
            payload_ref=discovery_plan_ref,
            idempotency_key=idempotency_key,
            capability_requirements=approved.discovery_plan.capability_requirements,
            priority=priority,
            created_at=created_at,
        )
        if created.state is JobState.CREATED:
            return self.jobs.queue_job(created.job_id, at=created_at)
        return created
