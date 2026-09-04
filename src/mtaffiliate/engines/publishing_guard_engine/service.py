from __future__ import annotations

from typing import ClassVar

from mtaffiliate.domain.publishing.models import (
    DuplicateDecision,
    PublishingLedgerEntry,
    PublishPlan,
)


class PublishingGuardEngine:
    """Pure Program 3 guard logic independent of Android/UI/persistence tools."""

    terminal_duplicate_statuses: ClassVar[frozenset[str]] = frozenset({"PUBLISHED", "CONFIRMED"})
    ambiguous_statuses: ClassVar[frozenset[str]] = frozenset(
        {"POST_SUBMITTED", "POST_OUTCOME_UNKNOWN", "OUTCOME_UNKNOWN", "NEEDS_HUMAN"}
    )

    def evaluate_duplicate(
        self,
        plan: PublishPlan,
        history: list[PublishingLedgerEntry],
    ) -> DuplicateDecision:
        same_platform_video = [
            entry
            for entry in history
            if entry.platform == plan.platform
            and (entry.video_id == plan.video_id or entry.video_sha256 == plan.video_sha256)
        ]
        latest_by_job: dict[str, PublishingLedgerEntry] = {}
        for entry in same_platform_video:
            current = latest_by_job.get(entry.publish_job_id)
            if current is None or entry.updated_at >= current.updated_at:
                latest_by_job[entry.publish_job_id] = entry
        current_states = list(latest_by_job.values())
        if any(entry.status in self.terminal_duplicate_statuses for entry in current_states):
            return DuplicateDecision(allowed=False, reason="VIDEO_ALREADY_PUBLISHED_TO_PLATFORM")
        if any(entry.status in self.ambiguous_statuses for entry in current_states):
            return DuplicateDecision(
                allowed=False,
                reason="PUBLISH_OUTCOME_REQUIRES_RECONCILIATION",
            )
        return DuplicateDecision(allowed=True, reason="NO_BLOCKING_PUBLISH_HISTORY")
