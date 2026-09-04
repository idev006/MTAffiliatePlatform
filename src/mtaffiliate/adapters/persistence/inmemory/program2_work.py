from __future__ import annotations

from threading import RLock

from mtaffiliate.domain.affiliate_offer.models import OfferDiscoveryWorkPackage
from mtaffiliate.ports.repositories.program2_work import Program2WorkConflictError


class InMemoryProgram2WorkRepository:
    def __init__(self) -> None:
        self._items: dict[str, OfferDiscoveryWorkPackage] = {}
        self._lock = RLock()

    def put(self, reference: str, package: OfferDiscoveryWorkPackage) -> None:
        if not reference.strip():
            raise ValueError("Program 2 work reference must be non-empty")
        with self._lock:
            existing = self._items.get(reference)
            if existing is not None:
                if existing != package:
                    raise Program2WorkConflictError(
                        f"Program 2 work reference conflict: {reference}"
                    )
                return
            self._items[reference] = package

    def get(self, reference: str) -> OfferDiscoveryWorkPackage | None:
        with self._lock:
            return self._items.get(reference)
