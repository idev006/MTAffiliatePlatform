from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.domain.program1.opportunity import (
    OpportunityAction,
    OpportunityEvidenceState,
    OpportunityFeatureSnapshot,
    OpportunityThesis,
    QualificationDecision,
    QualificationState,
)


@dataclass(frozen=True)
class OpportunityFeaturePolicy:
    version: str = "program1-opportunity-features-lab-v1"
    max_observation_age: timedelta = timedelta(days=7)

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("feature policy version must be non-empty")
        if self.max_observation_age <= timedelta(0):
            raise ValueError("max_observation_age must be positive")


@dataclass(frozen=True)
class QualificationPolicy:
    """Conservative laboratory gate, not a production success model."""

    version: str = "program1-qualification-lab-v1"
    min_rating_for_test: float = 4.0
    min_reviews_for_test: int = 20
    min_sold_signal_for_test: int = 50

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("qualification policy version must be non-empty")
        if not 0 <= self.min_rating_for_test <= 5:
            raise ValueError("min_rating_for_test must be within [0, 5]")
        if self.min_reviews_for_test < 0:
            raise ValueError("min_reviews_for_test must be >= 0")
        if self.min_sold_signal_for_test < 0:
            raise ValueError("min_sold_signal_for_test must be >= 0")


class OpportunityIntelligenceEngine:
    """Evidence-first opportunity qualification.

    This engine deliberately avoids a synthetic production total score. It
    derives transparent facts from history, tracks unknown strategic features,
    and decides only whether a product is ready for a controlled affiliate test.
    """

    _STRATEGIC_FEATURES_NOT_YET_OBSERVED = (
        "buyer_intent",
        "competition_saturation",
        "contentability",
        "audience_account_fit",
    )

    def __init__(
        self,
        feature_policy: OpportunityFeaturePolicy | None = None,
        qualification_policy: QualificationPolicy | None = None,
    ) -> None:
        self.feature_policy = feature_policy or OpportunityFeaturePolicy()
        self.qualification_policy = qualification_policy or QualificationPolicy()

    def derive_features(
        self,
        history: list[ProductObservation],
        *,
        as_of: datetime,
    ) -> OpportunityFeatureSnapshot:
        if not history:
            raise ValueError("observation history must be non-empty")
        ordered = sorted(
            history,
            key=lambda item: (item.collected_at, item.observation_id),
        )
        product_key = ordered[0].canonical_key
        if any(item.canonical_key != product_key for item in ordered):
            raise ValueError("history must contain exactly one product identity")

        latest = ordered[-1]
        previous_with_sold = next(
            (
                item
                for item in reversed(ordered[:-1])
                if item.sold_signal is not None
            ),
            None,
        )
        sold_delta = None
        if latest.sold_signal is not None and previous_with_sold is not None:
            sold_delta = latest.sold_signal - previous_with_sold.sold_signal

        age_seconds = max(0.0, (as_of - latest.collected_at).total_seconds())
        unknown: list[str] = list(self._STRATEGIC_FEATURES_NOT_YET_OBSERVED)
        for name, value in (
            ("demand", latest.sold_signal),
            ("rating", latest.rating),
            ("review_count", latest.review_count),
            ("price", latest.price_current),
        ):
            if value is None:
                unknown.append(name)
        if previous_with_sold is None:
            unknown.append("momentum")

        core_evidence_present = (
            latest.sold_signal is not None
            and latest.rating is not None
            and latest.review_count is not None
            and age_seconds <= self.feature_policy.max_observation_age.total_seconds()
        )
        evidence_state = (
            OpportunityEvidenceState.SUFFICIENT_FOR_LAB
            if core_evidence_present
            else OpportunityEvidenceState.NEEDS_EVIDENCE
        )

        return OpportunityFeatureSnapshot(
            product_key=product_key,
            as_of=as_of,
            feature_policy_version=self.feature_policy.version,
            history_count=len(ordered),
            latest_sold_signal=latest.sold_signal,
            sold_signal_delta=sold_delta,
            latest_rating=latest.rating,
            latest_review_count=latest.review_count,
            latest_price=latest.price_current,
            observation_age_seconds=age_seconds,
            evidence_state=evidence_state,
            unknown_features=tuple(sorted(set(unknown))),
            evidence_refs=tuple(item.observation_id for item in ordered),
        )

    def qualify(
        self,
        features: OpportunityFeatureSnapshot,
        *,
        evaluated_at: datetime,
    ) -> QualificationDecision:
        reasons: list[str] = []
        risks: list[str] = []

        if features.evidence_state is OpportunityEvidenceState.NEEDS_EVIDENCE:
            risks.extend(f"unknown:{name}" for name in features.unknown_features)
            return QualificationDecision(
                product_key=features.product_key,
                state=QualificationState.NEEDS_EVIDENCE,
                recommended_action=OpportunityAction.NEEDS_EVIDENCE,
                policy_version=self.qualification_policy.version,
                reasons=("Core observation evidence is incomplete or stale",),
                risks=tuple(risks),
                evaluated_at=evaluated_at,
            )

        assert features.latest_rating is not None
        assert features.latest_review_count is not None
        assert features.latest_sold_signal is not None

        if features.latest_rating < self.qualification_policy.min_rating_for_test:
            return QualificationDecision(
                product_key=features.product_key,
                state=QualificationState.HOLD,
                recommended_action=OpportunityAction.HOLD,
                policy_version=self.qualification_policy.version,
                reasons=(
                    "Observed rating is below the laboratory controlled-test gate",
                ),
                risks=("buyer_confidence_risk",),
                evaluated_at=evaluated_at,
            )

        if (
            features.latest_review_count < self.qualification_policy.min_reviews_for_test
            or features.latest_sold_signal
            < self.qualification_policy.min_sold_signal_for_test
        ):
            reasons.append(
                "Core evidence exists but demand/social-proof depth is not yet strong "
                "enough for the laboratory controlled-test gate"
            )
            return QualificationDecision(
                product_key=features.product_key,
                state=QualificationState.WATCH,
                recommended_action=OpportunityAction.WATCH,
                policy_version=self.qualification_policy.version,
                reasons=tuple(reasons),
                risks=("limited_evidence_depth",),
                evaluated_at=evaluated_at,
            )

        reasons.append("Core demand and buyer-confidence evidence passes the laboratory gate")
        if features.sold_signal_delta is not None:
            if features.sold_signal_delta > 0:
                reasons.append("Observed sold signal increased versus prior observation")
            elif features.sold_signal_delta < 0:
                risks.append("observed_sold_signal_declined")

        risks.extend(
            f"not_yet_observed:{name}"
            for name in features.unknown_features
            if name in self._STRATEGIC_FEATURES_NOT_YET_OBSERVED
        )
        return QualificationDecision(
            product_key=features.product_key,
            state=QualificationState.QUALIFIED_FOR_TEST,
            recommended_action=OpportunityAction.TEST_NOW,
            policy_version=self.qualification_policy.version,
            reasons=tuple(reasons),
            risks=tuple(risks),
            evaluated_at=evaluated_at,
        )

    def build_thesis(
        self,
        history: list[ProductObservation],
        *,
        as_of: datetime,
        target_buyer_context: str | None = None,
    ) -> OpportunityThesis:
        features = self.derive_features(history, as_of=as_of)
        decision = self.qualify(features, evaluated_at=as_of)
        latest = sorted(
            history,
            key=lambda item: (item.collected_at, item.observation_id),
        )[-1]

        evidence: list[str] = []
        if features.latest_sold_signal is not None:
            evidence.append(f"sold_signal={features.latest_sold_signal}")
        if features.sold_signal_delta is not None:
            evidence.append(f"sold_signal_delta={features.sold_signal_delta}")
        if features.latest_rating is not None:
            evidence.append(f"rating={features.latest_rating:.2f}")
        if features.latest_review_count is not None:
            evidence.append(f"review_count={features.latest_review_count}")
        if features.latest_price is not None:
            evidence.append(f"price={features.latest_price}")

        why_now = tuple(
            reason
            for reason in decision.reasons
            if "increased" in reason.lower() or "passes" in reason.lower()
        )
        strengths = tuple(
            reason
            for reason in decision.reasons
            if "passes" in reason.lower()
        )
        return OpportunityThesis(
            product_key=features.product_key,
            product_name=latest.product_name,
            as_of=as_of,
            feature_policy_version=features.feature_policy_version,
            qualification_policy_version=decision.policy_version,
            recommended_action=decision.recommended_action,
            why_now=why_now,
            observed_evidence=tuple(evidence),
            strengths=strengths,
            risks_and_uncertainties=decision.risks,
            target_buyer_context=target_buyer_context,
            evidence_state=features.evidence_state,
            evidence_refs=features.evidence_refs,
        )
