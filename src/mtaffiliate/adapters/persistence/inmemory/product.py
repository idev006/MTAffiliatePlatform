from __future__ import annotations

from threading import RLock

from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.ports.repositories.product import ObservationConflictError


class InMemoryProductRepository:
    def __init__(self) -> None:
        self._observations: list[ProductObservation] = []
        self._by_observation_id: dict[str, ProductObservation] = {}
        self._lock = RLock()

    def add_observations(self, observations: list[ProductObservation]) -> int:
        accepted = 0
        with self._lock:
            for observation in observations:
                existing = self._by_observation_id.get(observation.observation_id)
                if existing is not None:
                    if existing != observation:
                        raise ObservationConflictError(
                            f"observation_id collision: {observation.observation_id}"
                        )
                    continue
                self._by_observation_id[observation.observation_id] = observation
                self._observations.append(observation)
                accepted += 1
        return accepted

    def latest_observations(self) -> list[ProductObservation]:
        with self._lock:
            latest: dict[tuple[str, str, str], ProductObservation] = {}
            for observation in self._observations:
                current = latest.get(observation.canonical_key)
                if current is None or (
                    observation.collected_at,
                    observation.observation_id,
                ) > (
                    current.collected_at,
                    current.observation_id,
                ):
                    latest[observation.canonical_key] = observation
            return list(latest.values())
