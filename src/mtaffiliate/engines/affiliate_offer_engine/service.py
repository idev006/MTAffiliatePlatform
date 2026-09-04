from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateOfferObservation,
    OfferEvidenceState,
    OfferFeatureSnapshot,
    OfferQualificationDecision,
    OfferQualificationState,
    OfferRecommendedAction,
    OfferScore,
)


@dataclass(frozen=True)
class OfferScoringPolicy:
    model_version: str = "program2-offer-scoring-framework-v0"
    commission_weight: float = 1.0
    rating_weight: float = 1.0
    review_weight: float = 1.0
    demand_weight: float = 1.0

    def __post_init__(self) -> None:
        weights = (
            self.commission_weight,
            self.rating_weight,
            self.review_weight,
            self.demand_weight,
        )
        if any(not math.isfinite(weight) or weight < 0 for weight in weights):
            raise ValueError("offer scoring weights must be finite and non-negative")
        if sum(weights) <= 0:
            raise ValueError("at least one offer scoring weight must be positive")
        if not self.model_version.strip():
            raise ValueError("model_version must be non-empty")


class AffiliateOfferEngine:
    """Deterministic Program 2 scoring framework.

    Production Offer Scoring Model v1 is intentionally not frozen yet. This
    framework keeps scoring replaceable while preserving stable domain and
    application boundaries.
    """

    def __init__(self, policy: OfferScoringPolicy) -> None:
        self.policy = policy

    def is_eligible(self, observation: AffiliateOfferObservation) -> bool:
        return observation.available and (
            observation.commission_rate is not None or observation.extra_commission_rate is not None
        )

    def score(self, observation: AffiliateOfferObservation) -> OfferScore:
        commission = min(
            (observation.commission_rate or 0.0) + (observation.extra_commission_rate or 0.0),
            100.0,
        )
        rating = ((observation.rating or 0.0) / 5.0) * 100.0
        review = min((observation.review_count or 0) / 500.0, 1.0) * 100.0
        demand = min((observation.sold_signal or 0) / 1000.0, 1.0) * 100.0
        components = {
            "commission_placeholder": commission,
            "rating": rating,
            "review": review,
            "demand": demand,
        }
        weights = (
            self.policy.commission_weight,
            self.policy.rating_weight,
            self.policy.review_weight,
            self.policy.demand_weight,
        )
        weighted = (
            commission * weights[0]
            + rating * weights[1]
            + review * weights[2]
            + demand * weights[3]
        )
        total = weighted / sum(weights)
        reasons = [name for name, value in components.items() if value >= 70.0]
        return OfferScore(
            commercial_key=observation.commercial_key,
            total_score=round(total, 4),
            component_scores=components,
            reasons=reasons,
            model_version=self.policy.model_version,
        )

    def rank(self, observations: list[AffiliateOfferObservation]) -> list[OfferScore]:
        eligible = [item for item in observations if self.is_eligible(item)]
        scores = [self.score(item) for item in eligible]
        scores.sort(key=lambda item: (-item.total_score, item.commercial_key))
        return scores



@dataclass(frozen=True)
class OfferFeaturePolicy:
    version: str = "program2-offer-features-lab-v1"
    max_observation_age: timedelta = timedelta(hours=24)

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("offer feature policy version must be non-empty")
        if self.max_observation_age <= timedelta(0):
            raise ValueError("max_observation_age must be positive")


@dataclass(frozen=True)
class OfferQualificationPolicy:
    version: str = "program2-offer-qualification-lab-v1"
    min_commission_rate: float = 0.01
    min_rating: float = 4.0
    min_review_count: int = 20

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("offer qualification policy version must be non-empty")
        if not math.isfinite(self.min_commission_rate) or self.min_commission_rate < 0:
            raise ValueError("min_commission_rate must be finite and non-negative")
        if not math.isfinite(self.min_rating) or not 0 <= self.min_rating <= 5:
            raise ValueError("min_rating must be within [0, 5]")
        if self.min_review_count < 0:
            raise ValueError("min_review_count must be >= 0")


class EvidenceFirstOfferIntelligence:
    """Conservative Program 2 qualification for controlled affiliate use.

    This does not replace the evidence-gated production Offer Scoring Model v1.
    It preserves explicit unknown/stale state and selects only from observations
    with sufficient account-scoped evidence.
    """

    def __init__(
        self,
        feature_policy: OfferFeaturePolicy | None = None,
        qualification_policy: OfferQualificationPolicy | None = None,
    ) -> None:
        self.feature_policy = feature_policy or OfferFeaturePolicy()
        self.qualification_policy = qualification_policy or OfferQualificationPolicy()

    def derive_features(
        self,
        observation: AffiliateOfferObservation,
        *,
        as_of: datetime,
    ) -> OfferFeatureSnapshot:
        age_seconds = max(0.0, (as_of - observation.observed_at).total_seconds())
        commission_total = None
        if observation.commission_rate is not None or observation.extra_commission_rate is not None:
            commission_total = (observation.commission_rate or 0.0) + (
                observation.extra_commission_rate or 0.0
            )

        unknown: list[str] = []
        if commission_total is None:
            unknown.append("commission")
        if observation.rating is None:
            unknown.append("rating")
        if observation.review_count is None:
            unknown.append("review_count")
        if observation.price_current is None:
            unknown.append("price")
        if observation.sold_signal is None:
            unknown.append("demand")
        if observation.session_context_id is None:
            unknown.append("session_context")

        stale = age_seconds > self.feature_policy.max_observation_age.total_seconds()
        if stale:
            evidence_state = OfferEvidenceState.STALE
        elif commission_total is None or observation.rating is None or observation.review_count is None:
            evidence_state = OfferEvidenceState.NEEDS_EVIDENCE
        else:
            evidence_state = OfferEvidenceState.SUFFICIENT_FOR_LAB

        return OfferFeatureSnapshot(
            commercial_key=observation.commercial_key,
            as_of=as_of,
            feature_policy_version=self.feature_policy.version,
            latest_observed_at=observation.observed_at,
            observation_age_seconds=age_seconds,
            commission_total_rate=commission_total,
            rating=observation.rating,
            review_count=observation.review_count,
            sold_signal=observation.sold_signal,
            price_current=observation.price_current,
            available=observation.available,
            evidence_state=evidence_state,
            unknown_features=tuple(sorted(unknown)),
            evidence_refs=(observation.observation_id,),
        )

    def qualify(
        self,
        features: OfferFeatureSnapshot,
        *,
        evaluated_at: datetime,
    ) -> OfferQualificationDecision:
        if not features.available:
            return OfferQualificationDecision(
                commercial_key=features.commercial_key,
                state=OfferQualificationState.REJECTED,
                recommended_action=OfferRecommendedAction.REJECT,
                policy_version=self.qualification_policy.version,
                reasons=("Offer is not currently available",),
                risks=("availability",),
                evaluated_at=evaluated_at,
            )

        if features.evidence_state is OfferEvidenceState.STALE:
            return OfferQualificationDecision(
                commercial_key=features.commercial_key,
                state=OfferQualificationState.NEEDS_EVIDENCE,
                recommended_action=OfferRecommendedAction.NEEDS_EVIDENCE,
                policy_version=self.qualification_policy.version,
                reasons=("Offer observation is stale",),
                risks=("freshness",),
                evaluated_at=evaluated_at,
            )

        if features.evidence_state is OfferEvidenceState.NEEDS_EVIDENCE:
            return OfferQualificationDecision(
                commercial_key=features.commercial_key,
                state=OfferQualificationState.NEEDS_EVIDENCE,
                recommended_action=OfferRecommendedAction.NEEDS_EVIDENCE,
                policy_version=self.qualification_policy.version,
                reasons=("Offer evidence is incomplete",),
                risks=tuple(f"unknown:{name}" for name in features.unknown_features),
                evaluated_at=evaluated_at,
            )

        assert features.commission_total_rate is not None
        assert features.rating is not None
        assert features.review_count is not None

        if features.commission_total_rate < self.qualification_policy.min_commission_rate:
            return OfferQualificationDecision(
                commercial_key=features.commercial_key,
                state=OfferQualificationState.HOLD,
                recommended_action=OfferRecommendedAction.HOLD,
                policy_version=self.qualification_policy.version,
                reasons=("Observed commission is below the controlled-use gate",),
                risks=("commission_opportunity",),
                evaluated_at=evaluated_at,
            )

        if (
            features.rating < self.qualification_policy.min_rating
            or features.review_count < self.qualification_policy.min_review_count
        ):
            return OfferQualificationDecision(
                commercial_key=features.commercial_key,
                state=OfferQualificationState.WATCH,
                recommended_action=OfferRecommendedAction.WATCH,
                policy_version=self.qualification_policy.version,
                reasons=("Offer has usable economics but limited buyer-confidence evidence",),
                risks=("buyer_confidence",),
                evaluated_at=evaluated_at,
            )

        return OfferQualificationDecision(
            commercial_key=features.commercial_key,
            state=OfferQualificationState.QUALIFIED,
            recommended_action=OfferRecommendedAction.SELECT_NOW,
            policy_version=self.qualification_policy.version,
            reasons=("Offer passes the controlled-use evidence gate",),
            risks=(),
            evaluated_at=evaluated_at,
        )
