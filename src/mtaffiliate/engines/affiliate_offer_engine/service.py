from __future__ import annotations

import math
from dataclasses import dataclass

from mtaffiliate.domain.affiliate_offer.models import AffiliateOfferObservation, OfferScore


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
