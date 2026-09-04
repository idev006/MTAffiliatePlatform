from __future__ import annotations

from dataclasses import dataclass

from mtaffiliate.domain.program1.models import (
    AffiliateSuccessHypothesis,
    DiscoveryPlan,
    SignalRequirement,
)


@dataclass(frozen=True)
class StrategyToWorkResult:
    hypothesis: AffiliateSuccessHypothesis
    signals: tuple[SignalRequirement, ...]
    discovery_plan: DiscoveryPlan


class Program1StrategyPlanner:
    """Translate approved strategy artifacts into a bounded discovery plan.

    The planner validates traceability only. It does not decide Shopee selectors,
    pacing numbers, opportunity scores or collection mechanics.
    """

    def build(
        self,
        *,
        hypothesis: AffiliateSuccessHypothesis,
        signals: list[SignalRequirement],
        discovery_plan: DiscoveryPlan,
    ) -> StrategyToWorkResult:
        if discovery_plan.hypothesis_id != hypothesis.hypothesis_id:
            raise ValueError("discovery plan must reference the supplied hypothesis")
        if discovery_plan.campaign_id != hypothesis.campaign_id:
            raise ValueError("discovery plan campaign must match hypothesis campaign")

        by_id: dict[str, SignalRequirement] = {}
        for signal in signals:
            if signal.hypothesis_id != hypothesis.hypothesis_id:
                raise ValueError(
                    f"signal {signal.signal_id} must reference the supplied hypothesis"
                )
            if signal.signal_id in by_id:
                raise ValueError(f"duplicate signal_id: {signal.signal_id}")
            by_id[signal.signal_id] = signal

        missing = [
            signal_id
            for signal_id in discovery_plan.required_signal_ids
            if signal_id not in by_id
        ]
        if missing:
            raise ValueError(
                f"discovery plan references unknown required signals: {missing}"
            )

        unused = [
            signal.signal_id
            for signal in signals
            if signal.signal_id not in discovery_plan.required_signal_ids
        ]
        if unused:
            raise ValueError(
                f"signals supplied but not required by discovery plan: {unused}"
            )

        return StrategyToWorkResult(
            hypothesis=hypothesis,
            signals=tuple(by_id[signal_id] for signal_id in discovery_plan.required_signal_ids),
            discovery_plan=discovery_plan,
        )
