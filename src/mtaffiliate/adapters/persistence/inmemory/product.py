from __future__ import annotations

from mtaffiliate.domain.product.models import ProductObservation


class InMemoryProductRepository:
    def __init__(self) -> None:
        self._observations: list[ProductObservation] = []
        self._seen_observation_ids: set[str] = set()

    def add_observations(self, observations: list[ProductObservation]) -> int:
        accepted = 0
        for observation in observations:
            if observation.observation_id in self._seen_observation_ids:
                continue
            self._seen_observation_ids.add(observation.observation_id)
            self._observations.append(observation)
            accepted += 1
        return accepted

    def latest_observations(self) -> list[ProductObservation]:
        latest: dict[tuple[str, str, str], ProductObservation] = {}
        for observation in self._observations:
            current = latest.get(observation.canonical_key)
            if current is None or observation.collected_at > current.collected_at:
                latest[observation.canonical_key] = observation
        return list(latest.values())
