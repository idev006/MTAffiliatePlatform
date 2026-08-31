from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.publishing.models import PublishingLedgerEntry


class PublishingLedgerRepository(Protocol):
    def append(self, entry: PublishingLedgerEntry) -> None: ...

    def history_for_video(self, video_id: str) -> list[PublishingLedgerEntry]: ...
