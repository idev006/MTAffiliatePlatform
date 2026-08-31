from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mtaffiliate.adapters.persistence.inmemory.publishing import InMemoryPublishingLedgerRepository
from mtaffiliate.application.program3 import Program3Service
from mtaffiliate.domain.device.models import DeviceRecord
from mtaffiliate.domain.publishing.models import ApprovedOfferRef, PublishPlan
from mtaffiliate.domain.scene.models import SceneEvidence, SceneSignature
from mtaffiliate.engines.device_host_engine.service import DeviceHostEngine
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine
from mtaffiliate.engines.scene_engine.service import SceneEngine

NOW = datetime(2026, 8, 31, tzinfo=UTC)


def plan() -> PublishPlan:
    return PublishPlan(
        publish_job_id="job-1",
        platform="shopee",
        target_account_id="target-1",
        video_id="video-1",
        video_sha256="a" * 64,
        offers=[
            ApprovedOfferRef(
                selection_id="sel-1",
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
        created_at=NOW,
    )


def test_program3_ledger_blocks_confirmed_and_unknown_republish() -> None:
    app = Program3Service(
        InMemoryPublishingLedgerRepository(),
        PublishingGuardEngine(),
    )
    item = plan()
    assert app.evaluate_plan(item).allowed
    app.record_status(item, "published", now=NOW)
    assert not app.evaluate_plan(item).allowed

    other = item.model_copy(update={"video_id": "video-2", "video_sha256": "b" * 64})
    assert app.evaluate_plan(other).allowed
    app.record_status(other, "post_outcome_unknown", now=NOW)
    decision = app.evaluate_plan(other)
    assert not decision.allowed
    assert decision.reason == "PUBLISH_OUTCOME_REQUIRES_RECONCILIATION"


def test_scene_engine_confirms_unknown_and_ambiguous_without_real_device() -> None:
    engine = SceneEngine()
    source = SceneSignature(
        scene_id="VIDEO_SOURCE",
        expected_package="com.shopee.app",
        required_resource_ids={"video_picker"},
        negative_texts={"Publishing"},
    )
    details = SceneSignature(
        scene_id="POST_DETAILS",
        expected_package="com.shopee.app",
        required_texts={"Caption"},
    )
    confirmed = engine.recognize(
        SceneEvidence(
            package_name="com.shopee.app",
            resource_ids={"video_picker"},
        ),
        [source, details],
    )
    assert confirmed.status == "CONFIRMED"
    assert confirmed.scene_id == "VIDEO_SOURCE"

    unknown = engine.recognize(SceneEvidence(package_name="other"), [source])
    assert unknown.status == "UNKNOWN"

    ambiguous = engine.recognize(
        SceneEvidence(package_name="com.shopee.app", texts={"Caption"}),
        [
            details,
            SceneSignature(
                scene_id="READY_TO_PUBLISH",
                expected_package="com.shopee.app",
                required_texts={"Caption"},
            ),
        ],
    )
    assert ambiguous.status == "AMBIGUOUS"


def test_device_host_engine_enforces_one_active_worker_and_human_gate() -> None:
    engine = DeviceHostEngine()
    free = DeviceRecord(
        device_id="device-1",
        adb_serial="serial-1",
        host_id="host-1",
        status="ONLINE",
    )
    assert engine.can_assign(free, worker_id="worker-a", now=NOW).allowed

    owned = free.model_copy(
        update={
            "worker_id": "worker-a",
            "lease_expires_at": NOW + timedelta(minutes=5),
        }
    )
    assert not engine.can_assign(owned, worker_id="worker-b", now=NOW).allowed
    assert engine.can_assign(owned, worker_id="worker-a", now=NOW).allowed

    expired = owned.model_copy(update={"lease_expires_at": NOW - timedelta(seconds=1)})
    assert engine.can_assign(expired, worker_id="worker-b", now=NOW).allowed

    unauthorized = free.model_copy(update={"status": "UNAUTHORIZED"})
    decision = engine.can_assign(unauthorized, worker_id="worker-a", now=NOW)
    assert not decision.allowed
    assert decision.reason == "ADB_UNAUTHORIZED_NEEDS_HUMAN"
