from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.product.models import ProductObservation


class ProductRepository(Protocol):
    def add_observations(self, observations: list[ProductObservation]) -> int: ...

    def latest_observations(self) -> list[ProductObservation]: ...
