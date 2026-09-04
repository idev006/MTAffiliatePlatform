from datetime import UTC, datetime

import pytest

from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.factory import (
    build_engine,
    build_session_factory,
)
from mtaffiliate.adapters.persistence.sqlalchemy.program1_strategy import (
    SQLAlchemyProgram1StrategyRepository,
)
from mtaffiliate.application.program1_strategy import StrategyToWorkResult
from mtaffiliate.domain.program1.models import (
    AffiliateSuccessHypothesis,
    DiscoveryPlan,
    SignalRequirement,
)
from mtaffiliate.ports.repositories.program1_strategy import StrategyWorkConflictError

pytestmark = pytest.mark.integration

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


def package(*, objective: str = "Find products worth testing") -> StrategyToWorkResult:
    hypothesis = AffiliateSuccessHypothesis(
        hypothesis_id="hyp-1",
        campaign_id="campaign-1",
        objective=objective,
        decision_question="Which products deserve affiliate effort now?",
        rationale="Concentrate content effort",
        target_outcome="candidate_hit_rate",
        policy_version="affiliate-strategy-v1",
        created_at=NOW,
    )
    signal = SignalRequirement(
        signal_id="demand",
        hypothesis_id="hyp-1",
        decision_supported=hypothesis.decision_question,
        expected_interpretation="demand supports priority",
        evidence_source="approved product observations",
    )
    plan = DiscoveryPlan(
        plan_id="plan-1",
        campaign_id="campaign-1",
        hypothesis_id="hyp-1",
        required_signal_ids=("demand",),
        source_scope="shopee",
        surface_scope=("search",),
        capability_requirements=("collector:search-lab",),
        evidence_policy_version="evidence-v1",
        collection_policy_version="collection-v1",
        created_at=NOW,
    )
    return StrategyToWorkResult(
        hypothesis=hypothesis,
        signals=(signal,),
        discovery_plan=plan,
    )


def test_strategy_work_survives_repository_recomposition(tmp_path) -> None:
    url = "sqlite:///data/program1-strategy.db"
    engine = build_engine(url, project_root=tmp_path)
    Base.metadata.create_all(engine)
    repo = SQLAlchemyProgram1StrategyRepository(build_session_factory(engine))
    repo.put("program1-plan:plan-1:v1", package())
    engine.dispose()

    restarted_engine = build_engine(url, project_root=tmp_path)
    restarted = SQLAlchemyProgram1StrategyRepository(
        build_session_factory(restarted_engine)
    )
    restored = restarted.get("program1-plan:plan-1:v1")
    assert restored == package()
    restarted_engine.dispose()


def test_strategy_work_put_is_idempotent_for_same_semantics(tmp_path) -> None:
    engine = build_engine("sqlite:///data/program1-strategy.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    repo = SQLAlchemyProgram1StrategyRepository(build_session_factory(engine))
    item = package()

    repo.put("program1-plan:plan-1:v1", item)
    repo.put("program1-plan:plan-1:v1", item)

    assert repo.get("program1-plan:plan-1:v1") == item
    engine.dispose()


def test_strategy_work_reference_conflict_is_rejected(tmp_path) -> None:
    engine = build_engine("sqlite:///data/program1-strategy.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    repo = SQLAlchemyProgram1StrategyRepository(build_session_factory(engine))
    repo.put("program1-plan:plan-1:v1", package())

    with pytest.raises(StrategyWorkConflictError):
        repo.put(
            "program1-plan:plan-1:v1",
            package(objective="Different objective"),
        )
    engine.dispose()


def test_unknown_strategy_work_reference_returns_none(tmp_path) -> None:
    engine = build_engine("sqlite:///data/program1-strategy.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    repo = SQLAlchemyProgram1StrategyRepository(build_session_factory(engine))
    assert repo.get("missing") is None
    engine.dispose()
