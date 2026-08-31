from __future__ import annotations

from dataclasses import dataclass
import math

from mtaffiliate.domain.product.models import ProductObservation, ProductScore, ShortlistEntry


@dataclass(frozen=True)
class ScoringPolicy:
    model_version: str = "program1-scoring-framework-v0"
    demand_weight: float = 1.0
    rating_weight: float = 1.0
    review_weight: float = 1.0
    price_fit_weight: float = 1.0

    def __post_init__(self) -> None:
        weights = (
            self.demand_weight,
            self.rating_weight,
            self.review_weight,
            self.price_fit_weight,
        )
        if any(not math.isfinite(weight) or weight < 0 for weight in weights):
            raise ValueError("scoring weights must be finite and non-negative")
        if sum(weights) <= 0:
            raise ValueError("at least one scoring weight must be positive")
        if not self.model_version.strip():
            raise ValueError("model_version must be non-empty")


class ProductIntelligenceEngine:
    """Deterministic scoring framework.

    The exact production scoring formula is intentionally not frozen. This
    implementation provides a testable framework using transparent normalized
    components so validated v1 weights/formulas can replace policy without
    changing acquisition/application boundaries.
    """

    def __init__(self, policy: ScoringPolicy) -> None:
        self.policy = policy

    def score(self, observation: ProductObservation) -> ProductScore:
        demand = min((observation.sold_signal or 0) / 1000.0, 1.0) * 100.0
        rating = ((observation.rating or 0.0) / 5.0) * 100.0
        review = min((observation.review_count or 0) / 500.0, 1.0) * 100.0
        price_fit = 50.0 if observation.price_current is not None else 0.0

        components = {
            "demand": demand,
            "rating": rating,
            "review": review,
            "price_fit_placeholder": price_fit,
        }
        weighted = (
            demand * self.policy.demand_weight
            + rating * self.policy.rating_weight
            + review * self.policy.review_weight
            + price_fit * self.policy.price_fit_weight
        )
        weight_sum = sum(
            (
                self.policy.demand_weight,
                self.policy.rating_weight,
                self.policy.review_weight,
                self.policy.price_fit_weight,
            )
        )
        total = weighted / weight_sum
        reasons = [name for name, value in components.items() if value >= 70.0]
        return ProductScore(
            product_key=observation.canonical_key,
            total_score=round(total, 4),
            component_scores=components,
            reasons=reasons,
            model_version=self.policy.model_version,
        )

    def shortlist(
        self,
        observations: list[ProductObservation],
        *,
        limit: int,
        minimum_score: float = 0.0,
    ) -> list[ShortlistEntry]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if not math.isfinite(minimum_score) or not 0.0 <= minimum_score <= 100.0:
            raise ValueError("minimum_score must be finite and within [0, 100]")

        scores = [self.score(observation) for observation in observations]
        eligible = [score for score in scores if score.total_score >= minimum_score]
        eligible.sort(key=lambda item: (-item.total_score, item.product_key))
        return [
            ShortlistEntry(
                product_key=item.product_key,
                score=item.total_score,
                rank=index,
                reasons=item.reasons,
                model_version=item.model_version,
            )
            for index, item in enumerate(eligible[:limit], start=1)
        ]
