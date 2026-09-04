from __future__ import annotations

from datetime import datetime

from mtaffiliate.domain.affiliate_offer.models import (
    OfferDiscoveryPlan,
    OfferDiscoveryWorkPackage,
)
from mtaffiliate.domain.job.models import JobRecord, JobState
from mtaffiliate.domain.program1.opportunity import OpportunityAction, QualifiedOpportunityHandoff
from mtaffiliate.engines.shared_job_engine.service import SharedJobEngine
from mtaffiliate.ports.repositories.program2_work import Program2WorkRepository


class Program2OfferDiscoveryJobService:
    JOB_TYPE = "DISCOVER_AFFILIATE_OFFERS"
    DOMAIN = "program2"

    def __init__(
        self,
        work_repository: Program2WorkRepository,
        jobs: SharedJobEngine,
    ) -> None:
        self.work_repository = work_repository
        self.jobs = jobs

    def create_offer_discovery_job(
        self,
        *,
        handoff: QualifiedOpportunityHandoff,
        discovery_plan: OfferDiscoveryPlan,
        work_ref: str,
        job_id: str,
        idempotency_key: str,
        created_at: datetime,
        priority: int = 0,
    ) -> JobRecord:
        if not work_ref.strip():
            raise ValueError("Program 2 work_ref must be a durable non-empty reference")
        if handoff.recommended_action is not OpportunityAction.TEST_NOW:
            raise ValueError("Program 2 admits only TEST_NOW qualified opportunities")
        if discovery_plan.campaign_id != handoff.campaign_id:
            raise ValueError("OfferDiscoveryPlan campaign must match Program 1 handoff")
        if discovery_plan.hypothesis_id != handoff.hypothesis_id:
            raise ValueError("OfferDiscoveryPlan hypothesis must match Program 1 handoff")
        if discovery_plan.source_program1_decision_id != handoff.decision_id:
            raise ValueError("OfferDiscoveryPlan must reference the Program 1 decision")
        if discovery_plan.product_key != handoff.product_key:
            raise ValueError("OfferDiscoveryPlan product identity must match Program 1 handoff")
        if discovery_plan.product_name != handoff.product_name:
            raise ValueError("OfferDiscoveryPlan product name must match Program 1 handoff")

        package = OfferDiscoveryWorkPackage(
            upstream_handoff_id=handoff.handoff_id,
            upstream_decision_id=handoff.decision_id,
            upstream_source_job_id=handoff.source_job_id,
            campaign_id=handoff.campaign_id,
            hypothesis_id=handoff.hypothesis_id,
            product_key=handoff.product_key,
            product_name=handoff.product_name,
            affiliate_account_id=discovery_plan.affiliate_account_id,
            discovery_plan=discovery_plan,
        )
        self.work_repository.put(work_ref, package)
        created = self.jobs.create_job(
            job_id=job_id,
            job_type=self.JOB_TYPE,
            domain=self.DOMAIN,
            payload_ref=work_ref,
            idempotency_key=idempotency_key,
            capability_requirements=discovery_plan.capability_requirements,
            priority=priority,
            created_at=created_at,
        )
        if created.state is JobState.CREATED:
            return self.jobs.queue_job(created.job_id, at=created_at)
        return created

    def get_work_package(self, job_id: str) -> OfferDiscoveryWorkPackage:
        job = self.jobs.repository.get(job_id)
        if job is None:
            raise KeyError(job_id)
        if job.domain != self.DOMAIN or job.job_type != self.JOB_TYPE:
            raise ValueError(f"job is not a Program 2 offer discovery job: {job_id}")
        package = self.work_repository.get(job.payload_ref)
        if package is None:
            raise ValueError(f"Program 2 work package is missing: {job.payload_ref}")
        return package
