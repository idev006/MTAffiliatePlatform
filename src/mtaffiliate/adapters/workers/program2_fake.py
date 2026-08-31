from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable

from mtaffiliate.domain.affiliate_offer.models import AffiliateOfferObservation
from mtaffiliate.domain.affiliate_offer.worker import (
    OfferDiscoveryCommand,
    OfferObservationBatch,
)


class FakeProgram2OfferWorker:
    """Deterministic worker test double; it never owns commercial decisions."""

    def __init__(
        self,
        worker_id: str,
        observation_factory: Callable[
            [OfferDiscoveryCommand], list[AffiliateOfferObservation]
        ],
    ) -> None:
        if not worker_id.strip():
            raise ValueError("worker_id must be non-empty")
        self.worker_id = worker_id
        self._observation_factory = observation_factory

    def execute(
        self,
        command: OfferDiscoveryCommand,
        *,
        now: datetime | None = None,
    ) -> OfferObservationBatch:
        observations = self._observation_factory(command)
        for observation in observations:
            if observation.product_id != command.product_id:
                raise ValueError("worker observation product_id differs from command")
            if observation.platform != command.platform:
                raise ValueError("worker observation platform differs from command")
            if observation.affiliate_account_id != command.affiliate_account_id:
                raise ValueError("worker observation account context differs from command")
        return OfferObservationBatch(
            batch_id=f"batch-{command.command_id}",
            command_id=command.command_id,
            worker_id=self.worker_id,
            affiliate_account_id=command.affiliate_account_id,
            observations=observations,
            captured_at=now or datetime.now(UTC),
            extractor_version="fake-program2-worker-v1",
        )
