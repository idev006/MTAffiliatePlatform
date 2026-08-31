from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mtaffiliate.adapters.persistence.inmemory.product import ObservationConflictError
from mtaffiliate.adapters.persistence.sqlalchemy.base import Base
from mtaffiliate.adapters.persistence.sqlalchemy.factory import build_engine, build_session_factory
from mtaffiliate.adapters.persistence.sqlalchemy.product import SQLAlchemyProductRepository
from mtaffiliate.domain.product.models import ProductObservation

pytestmark = pytest.mark.integration


def observation(observation_id: str, item_id: str, *, seconds: int = 0) -> ProductObservation:
    return ProductObservation(
        observation_id=observation_id,
        platform="shopee",
        shop_id="shop-1",
        item_id=item_id,
        collected_at=datetime(2026, 8, 31, tzinfo=UTC) + timedelta(seconds=seconds),
        product_name=f"Product {item_id}",
        price_current=Decimal(100),
        sold_signal=100,
        rating=4.5,
        review_count=20,
    )


def repository(tmp_path):
    engine = build_engine("sqlite:///data/program1-test.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    return SQLAlchemyProductRepository(build_session_factory(engine)), engine


def test_sqlite_repository_matches_duplicate_and_conflict_contract(tmp_path) -> None:
    repo, engine = repository(tmp_path)
    first = observation("obs-1", "item-A")
    assert repo.add_observations([first]) == 1
    assert repo.add_observations([first]) == 0
    with pytest.raises(ObservationConflictError):
        repo.add_observations([observation("obs-1", "item-B")])
    engine.dispose()


def test_sqlite_repository_latest_observation_survives_restart(tmp_path) -> None:
    repo, engine = repository(tmp_path)
    repo.add_observations([
        observation("old", "item-A"),
        observation("new", "item-A", seconds=10),
    ])
    engine.dispose()

    engine2 = build_engine("sqlite:///data/program1-test.db", project_root=tmp_path)
    repo2 = SQLAlchemyProductRepository(build_session_factory(engine2))
    latest = repo2.latest_observations()
    assert len(latest) == 1
    assert latest[0].observation_id == "new"
    engine2.dispose()


def test_sqlite_relative_database_path_stays_under_project_root(tmp_path) -> None:
    engine = build_engine("sqlite:///data/app.db", project_root=tmp_path)
    Base.metadata.create_all(engine)
    assert (tmp_path / "data" / "app.db").exists()
    engine.dispose()


def test_sqlite_database_path_escape_is_rejected(tmp_path) -> None:
    with pytest.raises(ValueError):
        build_engine("sqlite:///../outside.db", project_root=tmp_path)
