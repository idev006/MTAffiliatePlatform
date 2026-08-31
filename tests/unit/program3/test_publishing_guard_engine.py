from datetime import UTC, datetime

from mtaffiliate.domain.publishing.models import ApprovedOfferRef, PublishPlan, PublishingLedgerEntry
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine


def plan() -> PublishPlan:
    return PublishPlan(
        publish_job_id="job-1",
        platform="shopee",
        target_account_id="account-1",
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


def ledger(status: str, *, platform: str = "shopee", video_id: str = "video-1") -> PublishingLedgerEntry:
    return PublishingLedgerEntry(
        publish_job_id="old-job",
        platform=platform,
        target_account_id="old-account",
        video_id=video_id,
        video_sha256="a" * 64,
        status=status,
        updated_at=datetime(2026, 8, 31, tzinfo=UTC),
    )


def test_allows_when_no_blocking_history_exists() -> None:
    result = PublishingGuardEngine().evaluate_duplicate(plan(), [])
    assert result.allowed


def test_blocks_confirmed_publish_across_managed_accounts_on_same_platform() -> None:
    result = PublishingGuardEngine().evaluate_duplicate(plan(), [ledger("PUBLISHED")])
    assert not result.allowed
    assert result.reason == "VIDEO_ALREADY_PUBLISHED_TO_PLATFORM"


def test_blocks_unknown_outcome_until_reconciled() -> None:
    result = PublishingGuardEngine().evaluate_duplicate(plan(), [ledger("POST_OUTCOME_UNKNOWN")])
    assert not result.allowed
    assert result.reason == "PUBLISH_OUTCOME_REQUIRES_RECONCILIATION"


def test_different_platform_does_not_block_platform_scoped_policy() -> None:
    result = PublishingGuardEngine().evaluate_duplicate(plan(), [ledger("PUBLISHED", platform="other")])
    assert result.allowed
