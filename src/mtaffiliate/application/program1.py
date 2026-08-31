from __future__ import annotations

from dataclasses import dataclass

from mtaffiliate.domain.product.models import ProductObservation, ShortlistEntry
from mtaffiliate.engines.product_intelligence_engine.service import ProductIntelligenceEngine
from mtaffiliate.ports.repositories.product import ProductRepository


@dataclass(frozen=True)
class IngestResult:
    accepted_count: int
    received_count: int


class Program1Service:
    def __init__(
        self,
        repository: ProductRepository,
        intelligence: ProductIntelligenceEngine,
        *,
        shortlist_limit: int,
        minimum_score: float,
    ) -> None:
        self.repository = repository
        self.intelligence = intelligence
        self.shortlist_limit = shortlist_limit
        self.minimum_score = minimum_score

    def ingest(self, observations: list[ProductObservation]) -> IngestResult:
        accepted = self.repository.add_observations(observations)
        return IngestResult(accepted_count=accepted, received_count=len(observations))

    def build_shortlist(self) -> list[ShortlistEntry]:
        latest = self.repository.latest_observations()
        return self.intelligence.shortlist(
            latest,
            limit=self.shortlist_limit,
            minimum_score=self.minimum_score,
        )
