from __future__ import annotations

import os
from pathlib import Path

from mtaffiliate.domain.affiliate_offer.worker import OutboxEnvelope


class FileOutbox:
    """Small portable outbox using atomic replace inside a managed runtime directory."""

    def __init__(self, outbox_dir: Path) -> None:
        self._dir = outbox_dir.resolve()
        self._dir.mkdir(parents=True, exist_ok=True)

    def put(self, envelope: OutboxEnvelope) -> None:
        target = self._path(envelope.envelope_id)
        temp = target.with_suffix(".tmp")
        temp.write_text(envelope.model_dump_json(), encoding="utf-8")
        os.replace(temp, target)

    def pending(self) -> list[OutboxEnvelope]:
        return [
            OutboxEnvelope.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self._dir.glob("*.json"))
        ]

    def acknowledge(self, envelope_id: str) -> None:
        self._path(envelope_id).unlink(missing_ok=True)

    def _path(self, envelope_id: str) -> Path:
        if not envelope_id or envelope_id in {".", ".."}:
            raise ValueError("invalid envelope_id")
        if Path(envelope_id).name != envelope_id or any(char in envelope_id for char in ("/", "\\")):
            raise ValueError("envelope_id must be a simple file-safe identifier")
        return self._dir / f"{envelope_id}.json"
