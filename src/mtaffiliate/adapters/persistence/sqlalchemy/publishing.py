from __future__ import annotations

from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.domain.publishing.models import PublishingLedgerEntry

from .models import PublishingLedgerRow


class SQLAlchemyPublishingLedgerRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _to_domain(row: PublishingLedgerRow) -> PublishingLedgerEntry:
        updated_at = row.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)
        return PublishingLedgerEntry(
            publish_job_id=row.publish_job_id,
            platform=row.platform,
            target_account_id=row.target_account_id,
            video_id=row.video_id,
            video_sha256=row.video_sha256,
            status=row.status,
            updated_at=updated_at,
        )

    def append(self, entry: PublishingLedgerEntry) -> None:
        with self._session_factory() as session, session.begin():
            session.add(
                PublishingLedgerRow(
                    publish_job_id=entry.publish_job_id,
                    platform=entry.platform,
                    target_account_id=entry.target_account_id,
                    video_id=entry.video_id,
                    video_sha256=entry.video_sha256,
                    status=entry.status,
                    updated_at=entry.updated_at,
                )
            )

    def history_for_video(self, video_id: str) -> list[PublishingLedgerEntry]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(PublishingLedgerRow)
                .where(PublishingLedgerRow.video_id == video_id)
                .order_by(PublishingLedgerRow.updated_at, PublishingLedgerRow.id)
            ).all()
        return [self._to_domain(row) for row in rows]
