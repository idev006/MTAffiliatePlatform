from __future__ import annotations

import hashlib
import json
from datetime import datetime

from mtaffiliate.domain.program1.opportunity import (
    OpportunityAction,
    OpportunityDecisionRecord,
    QualifiedOpportunityHandoff,
)
from mtaffiliate.engines.opportunity_intelligence_engine.service import (
    OpportunityIntelligenceEngine,
)
from mtaffiliate.ports.repositories.job import JobRepository
from mtaffiliate.ports.repositories.product import ProductRepository
from mtaffiliate.ports.repositories.program1_opportunity import Program1OpportunityRepository
from mtaffiliate.ports.repositories.program1_strategy import Program1StrategyRepository


class Program1OpportunityService:
    def __init__(
        self,
        *,
        products: ProductRepository,
        jobs: JobRepository,
        strategies: Program1StrategyRepository,
        decisions: Program1OpportunityRepository,
        intelligence: OpportunityIntelligenceEngine,
    ) -> None:
        self.products = products
        self.jobs = jobs
        self.strategies = strategies
        self.decisions = decisions
        self.intelligence = intelligence

    @staticmethod
    def _decision_id(
        *,
        campaign_id: str,
        hypothesis_id: str,
        source_job_id: str,
        product_key: tuple[str, str, str],
        evaluated_at: datetime,
        evidence_refs: tuple[str, ...],
        feature_policy_version: str,
        qualification_policy_version: str,
    ) -> str:
        payload = {
            "campaign_id": campaign_id,
            "hypothesis_id": hypothesis_id,
            "source_job_id": source_job_id,
            "product_key": product_key,
            "evaluated_at": evaluated_at.isoformat(),
            "evidence_refs": evidence_refs,
            "feature_policy_version": feature_policy_version,
            "qualification_policy_version": qualification_policy_version,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return f"p1od-{digest[:32]}"

    def evaluate_product(
        self,
        product_key: tuple[str, str, str],
        *,
        evaluated_at: datetime,
    ) -> OpportunityDecisionRecord:
        history = self.products.observation_history(product_key)
        if not history:
            raise KeyError(product_key)

        latest = history[-1]
        if not latest.source_job_id:
            raise ValueError(
                "latest observation is not traceable to a Program 1 discovery job"
            )

        job = self.jobs.get(latest.source_job_id)
        if job is None:
            raise ValueError(f"source job does not exist: {latest.source_job_id}")
        if job.domain != "program1" or job.job_type != "DISCOVER_PRODUCTS":
            raise ValueError(f"source job is not a Program 1 discovery job: {job.job_id}")

        package = self.strategies.get(job.payload_ref)
        if package is None:
            raise ValueError(f"strategy work package is missing: {job.payload_ref}")

        thesis = self.intelligence.build_thesis(
            history,
            as_of=evaluated_at,
            target_buyer_context=package.hypothesis.audience_context,
        )
        decision = OpportunityDecisionRecord(
            decision_id=self._decision_id(
                campaign_id=package.hypothesis.campaign_id,
                hypothesis_id=package.hypothesis.hypothesis_id,
                source_job_id=job.job_id,
                product_key=product_key,
                evaluated_at=evaluated_at,
                evidence_refs=thesis.evidence_refs,
                feature_policy_version=thesis.feature_policy_version,
                qualification_policy_version=thesis.qualification_policy_version,
            ),
            campaign_id=package.hypothesis.campaign_id,
            hypothesis_id=package.hypothesis.hypothesis_id,
            source_job_id=job.job_id,
            evaluated_at=evaluated_at,
            thesis=thesis,
        )
        self.decisions.put(decision)
        return decision

    def evaluate_campaign(
        self,
        campaign_id: str,
        *,
        evaluated_at: datetime,
    ) -> list[OpportunityDecisionRecord]:
        if not campaign_id.strip():
            raise ValueError("campaign_id must be non-empty")

        evaluated: list[OpportunityDecisionRecord] = []
        for observation in self.products.latest_observations():
            if not observation.source_job_id:
                continue
            job = self.jobs.get(observation.source_job_id)
            if job is None or job.domain != "program1" or job.job_type != "DISCOVER_PRODUCTS":
                continue
            package = self.strategies.get(job.payload_ref)
            if package is None or package.hypothesis.campaign_id != campaign_id:
                continue
            evaluated.append(
                self.evaluate_product(
                    observation.canonical_key,
                    evaluated_at=evaluated_at,
                )
            )
        evaluated.sort(
            key=lambda item: (
                item.thesis.recommended_action != OpportunityAction.TEST_NOW,
                item.thesis.product_key,
            )
        )
        return evaluated

    def qualified_handoffs(self, campaign_id: str) -> list[QualifiedOpportunityHandoff]:
        latest_by_product: dict[
            tuple[str, str, str],
            OpportunityDecisionRecord,
        ] = {}
        for decision in self.decisions.list_for_campaign(campaign_id):
            latest_by_product.setdefault(decision.thesis.product_key, decision)

        handoffs: list[QualifiedOpportunityHandoff] = []
        for decision in latest_by_product.values():
            thesis = decision.thesis
            if thesis.recommended_action is not OpportunityAction.TEST_NOW:
                continue
            handoffs.append(
                QualifiedOpportunityHandoff(
                    handoff_id=f"p1h-{decision.decision_id}",
                    decision_id=decision.decision_id,
                    campaign_id=decision.campaign_id,
                    hypothesis_id=decision.hypothesis_id,
                    source_job_id=decision.source_job_id,
                    product_key=thesis.product_key,
                    product_name=thesis.product_name,
                    recommended_action=thesis.recommended_action,
                    evidence_refs=thesis.evidence_refs,
                    feature_policy_version=thesis.feature_policy_version,
                    qualification_policy_version=thesis.qualification_policy_version,
                )
            )
        return sorted(handoffs, key=lambda item: item.product_key)
