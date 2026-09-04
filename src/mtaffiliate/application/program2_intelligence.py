from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateOfferObservation,
    OfferRecommendedAction,
    OfferSelectionDecision,
)
from mtaffiliate.engines.affiliate_offer_engine.service import EvidenceFirstOfferIntelligence
from mtaffiliate.ports.repositories.affiliate_offer import AffiliateOfferRepository
from mtaffiliate.ports.repositories.program2_decision import Program2DecisionRepository


@dataclass(frozen=True)
class OfferSelectionPolicy:
    version: str = "program2-selection-lab-v1"
    backup_count: int = 2

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("selection policy version must be non-empty")
        if self.backup_count < 0:
            raise ValueError("backup_count must be >= 0")


class Program2OfferDecisionService:
    """Build durable, explainable, account-scoped offer selection decisions."""

    def __init__(
        self,
        *,
        offers: AffiliateOfferRepository,
        decisions: Program2DecisionRepository,
        intelligence: EvidenceFirstOfferIntelligence,
        selection_policy: OfferSelectionPolicy | None = None,
    ) -> None:
        self.offers = offers
        self.decisions = decisions
        self.intelligence = intelligence
        self.selection_policy = selection_policy or OfferSelectionPolicy()

    @staticmethod
    def _decision_id(
        *,
        product_id: str,
        affiliate_account_id: str,
        source_job_id: str,
        selected_at: datetime,
        preferred_offer_id: str,
        backup_offer_ids: tuple[str, ...],
        evidence_refs: tuple[str, ...],
        feature_policy_version: str,
        qualification_policy_version: str,
        decision_policy_version: str,
    ) -> str:
        payload = {
            "product_id": product_id,
            "affiliate_account_id": affiliate_account_id,
            "source_job_id": source_job_id,
            "selected_at": selected_at.isoformat(),
            "preferred_offer_id": preferred_offer_id,
            "backup_offer_ids": backup_offer_ids,
            "evidence_refs": evidence_refs,
            "feature_policy_version": feature_policy_version,
            "qualification_policy_version": qualification_policy_version,
            "decision_policy_version": decision_policy_version,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return f"p2d-{digest[:32]}"

    @staticmethod
    def _ordering(
        observation: AffiliateOfferObservation,
    ) -> tuple[float, float, int, int, tuple[str, str, str, str, str]]:
        commission = (observation.commission_rate or 0.0) + (
            observation.extra_commission_rate or 0.0
        )
        return (
            -commission,
            -(observation.rating or 0.0),
            -(observation.review_count or 0),
            -(observation.sold_signal or 0),
            observation.commercial_key,
        )

    def evaluate_and_select(
        self,
        *,
        product_id: str,
        affiliate_account_id: str,
        source_job_id: str,
        evaluated_at: datetime,
    ) -> OfferSelectionDecision:
        if not product_id.strip():
            raise ValueError("product_id must be non-empty")
        if not affiliate_account_id.strip():
            raise ValueError("affiliate_account_id must be non-empty")
        if not source_job_id.strip():
            raise ValueError("source_job_id must be non-empty")

        candidates = [
            observation
            for observation in self.offers.latest_for_product(
                product_id,
                affiliate_account_id,
            )
            if observation.source_job_id == source_job_id
        ]
        if not candidates:
            raise ValueError("no offer observations for source job")

        qualified: list[tuple[AffiliateOfferObservation, object, object]] = []
        rejected_reasons: list[str] = []
        for observation in candidates:
            features = self.intelligence.derive_features(
                observation,
                as_of=evaluated_at,
            )
            qualification = self.intelligence.qualify(
                features,
                evaluated_at=evaluated_at,
            )
            if qualification.recommended_action is OfferRecommendedAction.SELECT_NOW:
                qualified.append((observation, features, qualification))
            else:
                rejected_reasons.append(
                    f"{observation.offer_id}:{qualification.recommended_action.value}"
                )

        if not qualified:
            raise ValueError(
                "no qualified affiliate offers; "
                + ", ".join(sorted(rejected_reasons))
            )

        qualified.sort(key=lambda item: self._ordering(item[0]))
        preferred_observation, preferred_features, preferred_qualification = qualified[0]
        backups = qualified[1 : self.selection_policy.backup_count + 1]

        backup_ids = tuple(item[0].offer_id for item in backups)
        evidence_refs = tuple(
            sorted(
                {
                    ref
                    for _observation, features, _qualification in qualified
                    for ref in features.evidence_refs
                }
            )
        )
        reasons = (
            "Eligible offers passed account-scoped freshness/evidence gates",
            "Preferred offer selected by transparent laboratory ordering "
            "(commission, rating, reviews, demand, identity)",
        )
        risks = tuple(
            sorted(
                {
                    risk
                    for _observation, _features, qualification in qualified
                    for risk in qualification.risks
                }
            )
        )

        decision = OfferSelectionDecision(
            decision_id=self._decision_id(
                product_id=product_id,
                affiliate_account_id=affiliate_account_id,
                source_job_id=source_job_id,
                selected_at=evaluated_at,
                preferred_offer_id=preferred_observation.offer_id,
                backup_offer_ids=backup_ids,
                evidence_refs=evidence_refs,
                feature_policy_version=preferred_features.feature_policy_version,
                qualification_policy_version=preferred_qualification.policy_version,
                decision_policy_version=self.selection_policy.version,
            ),
            product_id=product_id,
            affiliate_account_id=affiliate_account_id,
            source_job_id=source_job_id,
            selected_at=evaluated_at,
            preferred_offer_id=preferred_observation.offer_id,
            backup_offer_ids=backup_ids,
            preferred_commercial_key=preferred_observation.commercial_key,
            evidence_refs=evidence_refs,
            feature_policy_version=preferred_features.feature_policy_version,
            qualification_policy_version=preferred_qualification.policy_version,
            decision_policy_version=self.selection_policy.version,
            reasons=reasons,
            risks=risks,
        )
        self.decisions.put(decision)
        return decision
