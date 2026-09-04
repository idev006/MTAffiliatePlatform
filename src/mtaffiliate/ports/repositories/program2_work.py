from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.affiliate_offer.models import OfferDiscoveryWorkPackage


class Program2WorkConflictError(RuntimeError):
    pass


class Program2WorkRepository(Protocol):
    def put(self, reference: str, package: OfferDiscoveryWorkPackage) -> None: ...

    def get(self, reference: str) -> OfferDiscoveryWorkPackage | None: ...
