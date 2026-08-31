from __future__ import annotations

from mtaffiliate.domain.publishing.models import DuplicateDecision, PublishPlan, PublishingLedgerEntry


class PublishingGuardEngine:
    """Pure Program 3 guard logic independent of Android/UI/persistence tools."""

    terminal_duplicate_statuses = {"PUBLISHED", "CONFIRMED"}
    ambiguous_statuses = {"POST_OUTCOME_UNKNOWN", "NEEDS_HUMAN"}

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
        if any(entry.status in self.terminal_duplicate_statuses for entry in same_platform_video):
            return DuplicateDecision(allowed=False, reason="VIDEO_ALREADY_PUBLISHED_TO_PLATFORM")
        if any(entry.status in self.ambiguous_statuses for entry in same_platform_video):
            return DuplicateDecision(allowed=False, reason="PUBLISH_OUTCOME_REQUIRES_RECONCILIATION")
        return DuplicateDecision(allowed=True, reason="NO_BLOCKING_PUBLISH_HISTORY")
