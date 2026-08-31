from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.ports.repositories.ingestion import (
    IngestionBatchConflictError,
    IngestionBatchReceipt,
)

from .models import IngestionBatchRow


class SQLAlchemyIngestionBatchStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get(self, batch_id: str) -> IngestionBatchReceipt | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(IngestionBatchRow).where(IngestionBatchRow.batch_id == batch_id)
            )
            if row is None:
                return None
            return IngestionBatchReceipt(
                fingerprint=row.fingerprint,
                accepted_count=row.accepted_count,
                received_count=row.received_count,
            )

    def put(self, batch_id: str, receipt: IngestionBatchReceipt) -> None:
        with self._session_factory() as session, session.begin():
            existing = session.get(IngestionBatchRow, batch_id)
            if existing is not None:
                stored = IngestionBatchReceipt(
                    fingerprint=existing.fingerprint,
                    accepted_count=existing.accepted_count,
                    received_count=existing.received_count,
                )
                if stored != receipt:
                    raise IngestionBatchConflictError(f"batch_id collision: {batch_id}")
                return
            try:
                with session.begin_nested():
                    session.add(
                        IngestionBatchRow(
                            batch_id=batch_id,
                            fingerprint=receipt.fingerprint,
                            accepted_count=receipt.accepted_count,
                            received_count=receipt.received_count,
                        )
                    )
                    session.flush()
            except IntegrityError:
                existing = session.get(IngestionBatchRow, batch_id)
                if existing is None:
                    raise
                stored = IngestionBatchReceipt(
                    fingerprint=existing.fingerprint,
                    accepted_count=existing.accepted_count,
                    received_count=existing.received_count,
                )
                if stored != receipt:
                    raise IngestionBatchConflictError(f"batch_id collision: {batch_id}") from None
