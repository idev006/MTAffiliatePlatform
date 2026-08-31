from datetime import datetime, timezone
from decimal import Decimal
from threading import Barrier, Thread

from mtaffiliate.adapters.persistence.inmemory.product import InMemoryProductRepository
from mtaffiliate.domain.product.models import ProductObservation


def make_observation() -> ProductObservation:
    return ProductObservation(
        observation_id="shared-observation",
        platform="shopee",
        shop_id="shop-1",
        item_id="item-1",
        collected_at=datetime(2026, 8, 31, tzinfo=timezone.utc),
        product_name="Product",
        price_current=Decimal("100"),
        sold_signal=100,
        rating=4.5,
        review_count=20,
    )


def test_20_threads_ingesting_same_observation_accept_exactly_once() -> None:
    repository = InMemoryProductRepository()
    observation = make_observation()
    barrier = Barrier(20)
    accepted: list[int] = []

    def worker() -> None:
        barrier.wait()
        accepted.append(repository.add_observations([observation]))

    threads = [Thread(target=worker) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sum(accepted) == 1
    assert len(repository.latest_observations()) == 1
