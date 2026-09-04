from __future__ import annotations

import hashlib
from datetime import UTC

from sqlalchemy.orm import Session, sessionmaker

from mtaffiliate.domain.affiliate_offer.models import OfferDiscoveryWorkPackage
from mtaffiliate.ports.repositories.program2_work import Program2WorkConflictError

from .models import Program2WorkRow


class SQLAlchemyProgram2WorkRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _fingerprint(package: OfferDiscoveryWorkPackage) -> str:
        return hashlib.sha256(package.model_dump_json().encode("utf-8")).hexdigest()

    def put(self, reference: str, package: OfferDiscoveryWorkPackage) -> None:
        if not reference.strip():
            raise ValueError("Program 2 work reference must be non-empty")
        fingerprint = self._fingerprint(package)
        with self._session_factory() as session, session.begin():
            existing = session.get(Program2WorkRow, reference)
            if existing is not None:
                if existing.fingerprint != fingerprint:
                    raise Program2WorkConflictError(
                        f"Program 2 work reference conflict: {reference}"
                    )
                return
            session.add(
                Program2WorkRow(
                    reference=reference,
                    fingerprint=fingerprint,
                    package_json=package.model_dump_json(),
                    created_at=package.discovery_plan.created_at,
                )
            )

    def get(self, reference: str) -> OfferDiscoveryWorkPackage | None:
        with self._session_factory() as session:
            row = session.get(Program2WorkRow, reference)
            if row is None:
                return None
            package = OfferDiscoveryWorkPackage.model_validate_json(row.package_json)
            created_at = package.discovery_plan.created_at
            if created_at.tzinfo is None:
                package = package.model_copy(
                    update={
                        "discovery_plan": package.discovery_plan.model_copy(
                            update={"created_at": created_at.replace(tzinfo=UTC)}
                        )
                    }
                )
            return package
