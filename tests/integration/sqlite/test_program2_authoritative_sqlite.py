from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mtaffiliate.adapters.persistence.sqlalchemy.affiliate_offer import (
    SQLAlchemyAffiliateOfferRepository,
)
from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.factory import (
    build_engine,
    build_session_factory,
)
from mtaffiliate.adapters.persistence.sqlalchemy.program2_artifact import (
    SQLAlchemyProgram2ArtifactRepository,
)
from mtaffiliate.adapters.persistence.sqlalchemy.program2_decision import (
    SQLAlchemyProgram2DecisionRepository,
)
from mtaffiliate.adapters.persistence.sqlalchemy.program2_work import (
    SQLAlchemyProgram2WorkRepository,
)
from mtaffiliate.domain.affiliate_offer.models import (
    AffiliateLinkArtifact,
    AffiliateOfferObservation,
    LinkArtifactValidationState,
    OfferDiscoveryPlan,
    OfferDiscoveryWorkPackage,
    OfferSelectionDecision,
)
from mtaffiliate.ports.repositories.program2_artifact import Program2ArtifactConflictError
from mtaffiliate.ports.repositories.program2_decision import Program2DecisionConflictError
from mtaffiliate.ports.repositories.program2_work import Program2WorkConflictError

pytestmark = pytest.mark.integration
NOW = datetime(2026, 9, 4, 18, 30, tzinfo=UTC)
URL = "sqlite:///data/program2-authoritative.db"


def compose(tmp_path):
    engine = build_engine(URL, project_root=tmp_path)
    Base.metadata.create_all(engine)
    sessions = build_session_factory(engine)
    return (
        engine,
        SQLAlchemyAffiliateOfferRepository(sessions),
        SQLAlchemyProgram2WorkRepository(sessions),
        SQLAlchemyProgram2DecisionRepository(sessions),
        SQLAlchemyProgram2ArtifactRepository(sessions),
    )


def work_package() -> OfferDiscoveryWorkPackage:
    plan = OfferDiscoveryPlan(
        plan_id="plan-1",
        campaign_id="campaign-1",
        hypothesis_id="hyp-1",
        source_program1_decision_id="p1d-1",
        product_key=("shopee", "shop-1", "item-1"),
        product_name="Synthetic SSD",
        affiliate_account_id="account-1",
        collection_targets=("https://example.invalid/affiliate/search",),
        capability_requirements=("offer:candidate-read",),
        evidence_policy_version="p2-evidence-v1",
        collection_policy_version="p2-collection-v1",
        created_at=NOW,
    )
    return OfferDiscoveryWorkPackage(
        upstream_handoff_id="p1h-1",
        upstream_decision_id="p1d-1",
        upstream_source_job_id="program1-job-1",
        campaign_id="campaign-1",
        hypothesis_id="hyp-1",
        product_key=("shopee", "shop-1", "item-1"),
        product_id="shopee:shop-1:item-1",
        product_name="Synthetic SSD",
        affiliate_account_id="account-1",
        discovery_plan=plan,
    )


def decision() -> OfferSelectionDecision:
    return OfferSelectionDecision(
        decision_id="p2d-1",
        product_id="shopee:shop-1:item-1",
        affiliate_account_id="account-1",
        source_job_id="program2-job-1",
        selected_at=NOW,
        preferred_offer_id="offer-1",
        backup_offer_ids=("offer-2",),
        preferred_commercial_key=(
            "shopee",
            "shop-offer-1",
            "item-1",
            "offer-1",
            "account-1",
        ),
        evidence_refs=("offer-obs-1", "offer-obs-2"),
        feature_policy_version="features-v1",
        qualification_policy_version="qualification-v1",
        decision_policy_version="selection-v1",
        reasons=("fixture decision",),
        risks=(),
    )


def artifact() -> AffiliateLinkArtifact:
    return AffiliateLinkArtifact(
        artifact_id="artifact-1",
        selection_decision_id="p2d-1",
        source_job_id="program2-job-1",
        affiliate_account_id="account-1",
        offer_id="offer-1",
        link_url="https://example.invalid/affiliate/link-1",
        created_at=NOW + timedelta(minutes=1),
        validated_at=NOW + timedelta(minutes=2),
        validation_state=LinkArtifactValidationState.LAB_VALIDATED,
        evidence_refs=("export-fixture-1",),
    )


def observation() -> AffiliateOfferObservation:
    return AffiliateOfferObservation(
        observation_id="offer-obs-1",
        offer_id="offer-1",
        product_id="shopee:shop-1:item-1",
        platform="shopee",
        shop_id="shop-offer-1",
        item_id="item-1",
        affiliate_account_id="account-1",
        session_context_id="session-1",
        source_worker_id="worker-1",
        source_job_id="program2-job-1",
        extractor_version="fixture-v1",
        observed_at=NOW,
        seller_name="Seller",
        product_name="Synthetic SSD",
        price_current=Decimal(1590),
        commission_rate=12,
        extra_commission_rate=0,
        rating=4.8,
        review_count=120,
        sold_signal=300,
        available=True,
    )


def test_program2_work_decision_artifact_and_provenance_survive_restart(tmp_path) -> None:
    engine, offers, work, decisions, artifacts = compose(tmp_path)

    work.put("program2-work:1", work_package())
    offers.add_observations([observation()])
    decisions.put(decision())
    artifacts.put(artifact())
    engine.dispose()

    restarted_engine, restarted_offers, restarted_work, restarted_decisions, restarted_artifacts = (
        compose(tmp_path)
    )

    assert restarted_work.get("program2-work:1") == work_package()
    stored_offer = restarted_offers.latest_for_product(
        "shopee:shop-1:item-1",
        "account-1",
    )[0]
    assert stored_offer.source_job_id == "program2-job-1"
    assert stored_offer.source_worker_id == "worker-1"
    assert stored_offer.session_context_id == "session-1"
    assert stored_offer.extractor_version == "fixture-v1"
    assert restarted_decisions.get("p2d-1") == decision()
    assert (
        restarted_decisions.latest_for_product_account(
            "shopee:shop-1:item-1",
            "account-1",
        )
        == decision()
    )
    assert restarted_artifacts.get("artifact-1") == artifact()
    assert restarted_artifacts.latest_for_selection("p2d-1") == artifact()
    restarted_engine.dispose()


def test_program2_sql_repositories_are_idempotent_and_conflict_safe(tmp_path) -> None:
    engine, _offers, work, decisions, artifacts = compose(tmp_path)

    package = work_package()
    work.put("program2-work:1", package)
    work.put("program2-work:1", package)
    with pytest.raises(Program2WorkConflictError):
        work.put(
            "program2-work:1",
            package.model_copy(update={"campaign_id": "other"}),
        )

    selected = decision()
    decisions.put(selected)
    decisions.put(selected)
    with pytest.raises(Program2DecisionConflictError):
        decisions.put(
            selected.model_copy(update={"affiliate_account_id": "other"})
        )

    link = artifact()
    artifacts.put(link)
    artifacts.put(link)
    with pytest.raises(Program2ArtifactConflictError):
        artifacts.put(
            link.model_copy(update={"offer_id": "other"})
        )

    assert work.get("missing") is None
    assert decisions.get("missing") is None
    assert decisions.latest_for_product_account("missing", "missing") is None
    assert artifacts.get("missing") is None
    assert artifacts.latest_for_selection("missing") is None
    engine.dispose()
