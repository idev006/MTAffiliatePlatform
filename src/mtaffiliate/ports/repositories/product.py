from __future__ import annotations

from typing import Protocol

from mtaffiliate.domain.product.models import ProductObservation


class ObservationConflictError(ValueError):
    """Raised when an observation identity is reused with different durable facts."""


class ProductRepository(Protocol):
    def add_observations(self, observations: list[ProductObservation]) -> int: ...

    def latest_observations(self) -> list[ProductObservation]: ...

    def observation_history(
        self,
        product_key: tuple[str, str, str],
    ) -> list[ProductObservation]: ...
