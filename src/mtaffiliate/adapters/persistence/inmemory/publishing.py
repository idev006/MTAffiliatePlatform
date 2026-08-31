from __future__ import annotations

from threading import RLock

from mtaffiliate.domain.publishing.models import PublishingLedgerEntry


class InMemoryPublishingLedgerRepository:
    def __init__(self) -> None:
        self._entries: list[PublishingLedgerEntry] = []
        self._lock = RLock()

    def append(self, entry: PublishingLedgerEntry) -> None:
        with self._lock:
            self._entries.append(entry)

    def history_for_video(self, video_id: str) -> list[PublishingLedgerEntry]:
        with self._lock:
            return [entry for entry in self._entries if entry.video_id == video_id]
