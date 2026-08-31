from __future__ import annotations

from datetime import UTC, datetime

from mtaffiliate.domain.publishing.models import (
    DuplicateDecision,
    PublishingLedgerEntry,
    PublishPlan,
)
from mtaffiliate.engines.publishing_guard_engine.service import PublishingGuardEngine
from mtaffiliate.ports.repositories.publishing import PublishingLedgerRepository


class Program3Service:
    def __init__(
        self,
        ledger: PublishingLedgerRepository,
        guard: PublishingGuardEngine,
    ) -> None:
        self.ledger = ledger
        self.guard = guard

    def evaluate_plan(self, plan: PublishPlan) -> DuplicateDecision:
        history = self.ledger.history_for_video(plan.video_id)
        return self.guard.evaluate_duplicate(plan, history)

    def record_status(
        self,
        plan: PublishPlan,
        status: str,
        *,
        now: datetime | None = None,
    ) -> PublishingLedgerEntry:
        normalized = status.strip().upper()
        if not normalized:
            raise ValueError("status must be non-empty")
        entry = PublishingLedgerEntry(
            publish_job_id=plan.publish_job_id,
            platform=plan.platform,
            target_account_id=plan.target_account_id,
            video_id=plan.video_id,
            video_sha256=plan.video_sha256,
            status=normalized,
            updated_at=now or datetime.now(UTC),
        )
        self.ledger.append(entry)
        return entry
