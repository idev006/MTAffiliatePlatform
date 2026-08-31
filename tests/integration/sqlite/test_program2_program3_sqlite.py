from datetime import UTC, datetime

from mtaffiliate.adapters.persistence.sqlalchemy.affiliate_offer import (
    SQLAlchemyAffiliateOfferRepository,
)
from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.factory import (
    build_engine,
    build_session_factory,
)
from mtaffiliate.adapters.persistence.sqlalchemy.publishing import (
    SQLAlchemyPublishingLedgerRepository,
)
from mtaffiliate.application.program2 import Program2Service
from mtaffiliate.application.program3 import Program3Service
from mtaffiliate.domain.affiliate_offer.models import AffiliateOfferObservation
from mtaffiliate.domain.publishing.models import ApprovedOfferRef, PublishPlan
from mtaffiliate.engines.affiliate_offer_engine.service import (
    AffiliateOfferEngine,
    OfferScoringPolicy,
)
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine


def offer() -> AffiliateOfferObservation:
    return AffiliateOfferObservation(
        observation_id="offer-obs-1",
        offer_id="offer-1",
        product_id="product-1",
        platform="shopee",
        shop_id="shop-1",
        item_id="item-1",
        affiliate_account_id="affiliate-1",
        observed_at=datetime(2026, 8, 31, tzinfo=UTC),
        product_name="Product",
        commission_rate=20,
        rating=4.5,
        review_count=100,
        sold_signal=500,
    )


def plan() -> PublishPlan:
    return PublishPlan(
        publish_job_id="publish-1",
        platform="shopee",
        target_account_id="target-1",
        video_id="video-1",
        video_sha256="a" * 64,
        offers=[
            ApprovedOfferRef(
                selection_id="selection-1",
                product_id="product-1",
                offer_id="offer-1",
                shop_id="shop-1",
                item_id="item-1",
                affiliate_account_id="affiliate-1",
                affiliate_link_id="link-1",
            )
        ],
        duplicate_policy_version="duplicate-v1",
        plan_version="plan-v1",
        created_at=datetime(2026, 8, 31, tzinfo=UTC),
    )


def test_program2_offer_and_selection_survive_repository_restart(tmp_path) -> None:
    engine = build_engine("sqlite:///data/p23.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    sessions = build_session_factory(engine)

    app = Program2Service(
        SQLAlchemyAffiliateOfferRepository(sessions),
        AffiliateOfferEngine(OfferScoringPolicy()),
    )
    assert app.ingest_observations([offer()]) == 1
    selection = app.select_offers(
        "product-1",
        affiliate_account_id="affiliate-1",
        now=datetime(2026, 8, 31, tzinfo=UTC),
    )

    restarted = SQLAlchemyAffiliateOfferRepository(sessions)
    assert restarted.latest_for_product("product-1")[0] == offer()
    assert restarted.get_selection(selection.selection_id) == selection
    assert restarted.add_observations([offer()]) == 0
    engine.dispose()


def test_program3_publishing_ledger_survives_restart_and_blocks_duplicate(tmp_path) -> None:
    engine = build_engine("sqlite:///data/p23-ledger.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    sessions = build_session_factory(engine)
    item = plan()

    app = Program3Service(
        SQLAlchemyPublishingLedgerRepository(sessions),
        PublishingGuardEngine(),
    )
    assert app.evaluate_plan(item).allowed
    app.record_status(item, "PUBLISHED", now=datetime(2026, 8, 31, tzinfo=UTC))

    restarted = Program3Service(
        SQLAlchemyPublishingLedgerRepository(sessions),
        PublishingGuardEngine(),
    )
    decision = restarted.evaluate_plan(item)
    assert not decision.allowed
    assert decision.reason == "VIDEO_ALREADY_PUBLISHED_TO_PLATFORM"
    engine.dispose()
