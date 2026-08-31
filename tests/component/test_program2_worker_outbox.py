from __future__ import annotations

from datetime import UTC, datetime

import pytest

from mtaffiliate.adapters.workers.file_outbox import FileOutbox
from mtaffiliate.adapters.workers.program2_fake import FakeProgram2OfferWorker
from mtaffiliate.domain.affiliate_offer.models import AffiliateOfferObservation
from mtaffiliate.domain.affiliate_offer.worker import OfferDiscoveryCommand, OutboxEnvelope

NOW = datetime(2026, 8, 31, tzinfo=UTC)


def command() -> OfferDiscoveryCommand:
    return OfferDiscoveryCommand(
        command_id="cmd-1",
        product_id="product-1",
        platform="shopee",
        affiliate_account_id="account-1",
        session_context_id="session-1",
        issued_at=NOW,
    )


def observed(**updates) -> AffiliateOfferObservation:
    data = {
        "observation_id": "obs-1",
        "offer_id": "offer-1",
        "product_id": "product-1",
        "platform": "shopee",
        "shop_id": "shop-1",
        "item_id": "item-1",
        "affiliate_account_id": "account-1",
        "observed_at": NOW,
        "product_name": "Product",
        "commission_rate": 10,
    }
    data.update(updates)
    return AffiliateOfferObservation(**data)


def test_fake_worker_preserves_command_context() -> None:
    worker = FakeProgram2OfferWorker("worker-1", lambda _command: [observed()])
    batch = worker.execute(command(), now=NOW)
    assert batch.command_id == "cmd-1"
    assert batch.worker_id == "worker-1"
    assert batch.affiliate_account_id == "account-1"
    assert batch.observations == [observed()]


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"product_id": "wrong"}, "product_id"),
        ({"platform": "wrong"}, "platform"),
        ({"affiliate_account_id": "wrong"}, "account context"),
    ],
)
def test_fake_worker_rejects_cross_context_observations(update, message) -> None:
    worker = FakeProgram2OfferWorker(
        "worker-1",
        lambda _command: [observed(**update)],
    )
    with pytest.raises(ValueError, match=message):
        worker.execute(command(), now=NOW)


def test_file_outbox_persists_until_ack_and_survives_reopen(tmp_path) -> None:
    envelope = OutboxEnvelope(
        envelope_id="env-1",
        kind="WORKER_EVENT",
        payload_json='{"event":"OFFER_DISCOVERY_COMPLETED"}',
        created_at=NOW,
    )
    first = FileOutbox(tmp_path / "outbox")
    first.put(envelope)
    assert first.pending() == [envelope]

    reopened = FileOutbox(tmp_path / "outbox")
    assert reopened.pending() == [envelope]
    reopened.acknowledge("env-1")
    assert reopened.pending() == []


def test_file_outbox_rejects_path_traversal_identifier(tmp_path) -> None:
    outbox = FileOutbox(tmp_path / "outbox")
    with pytest.raises(ValueError, match="file-safe"):
        outbox.acknowledge("../escape")
