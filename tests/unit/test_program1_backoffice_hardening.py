from datetime import datetime, timezone, timedelta
from decimal import Decimal
import math
import random

import pytest
from pydantic import ValidationError

from mtaffiliate.adapters.persistence.inmemory.product import (
    InMemoryProductRepository,
    ObservationConflictError,
)
from mtaffiliate.application.program1 import IngestionBatchConflictError, Program1Service
from mtaffiliate.bootstrap.config import Settings, load_settings
from mtaffiliate.bootstrap.paths import PathManager
from mtaffiliate.domain.product.models import ProductObservation
from mtaffiliate.engines.product_intelligence_engine.service import (
    ProductIntelligenceEngine,
    ScoringPolicy,
)

NOW = datetime(2026, 8, 31, tzinfo=timezone.utc)


def make_observation(
    observation_id: str = "o1",
    *,
    shop_id: str = "s1",
    item_id: str = "i1",
    collected_at: datetime = NOW,
    price: str | None = "100",
    sold: int = 0,
    rating: float = 0,
    reviews: int = 0,
) -> ProductObservation:
    return ProductObservation(
        observation_id=observation_id,
        platform="shopee",
        shop_id=shop_id,
        item_id=item_id,
        collected_at=collected_at,
        product_name="Product",
        price_current=None if price is None else Decimal(price),
        sold_signal=sold,
        rating=rating,
        review_count=reviews,
    )


def make_service() -> Program1Service:
    return Program1Service(
        InMemoryProductRepository(),
        ProductIntelligenceEngine(ScoringPolicy()),
        shortlist_limit=20,
        minimum_score=0,
    )


def test_product_model_rejects_invalid_numeric_signals() -> None:
    with pytest.raises(ValidationError):
        make_observation(sold=-1)
    with pytest.raises(ValidationError):
        make_observation(reviews=-1)
    with pytest.raises(ValidationError):
        make_observation(rating=-0.1)
    with pytest.raises(ValidationError):
        make_observation(rating=5.1)
    with pytest.raises(ValidationError):
        make_observation(price="-1")


def test_product_model_rejects_blank_identity_and_name() -> None:
    baseline = make_observation().model_dump()
    for field in ("observation_id", "platform", "shop_id", "item_id", "product_name"):
        payload = dict(baseline)
        payload[field] = "   "
        with pytest.raises(ValidationError):
            ProductObservation.model_validate(payload)


def test_scoring_policy_rejects_negative_nan_infinite_and_all_zero_weights() -> None:
    with pytest.raises(ValueError):
        ScoringPolicy(demand_weight=-1)
    with pytest.raises(ValueError):
        ScoringPolicy(demand_weight=float("nan"))
    with pytest.raises(ValueError):
        ScoringPolicy(demand_weight=float("inf"))
    with pytest.raises(ValueError):
        ScoringPolicy(demand_weight=0, rating_weight=0, review_weight=0, price_fit_weight=0)


def test_scoring_boundaries_and_saturation() -> None:
    engine = ProductIntelligenceEngine(ScoringPolicy())
    assert engine.score(make_observation(price=None)).total_score == 0
    assert engine.score(make_observation(sold=1000, rating=5, reviews=500)).total_score == 87.5
    assert engine.score(make_observation(sold=9_999_999, rating=5, reviews=9_999_999)).total_score == 87.5


def test_randomized_10k_scores_are_finite_and_bounded() -> None:
    rng = random.Random(20260831)
    engine = ProductIntelligenceEngine(ScoringPolicy())
    for index in range(10_000):
        score = engine.score(
            make_observation(
                f"o{index}",
                sold=rng.randint(0, 10_000_000),
                rating=rng.random() * 5,
                reviews=rng.randint(0, 10_000_000),
                price=None if index % 2 else str(rng.randint(0, 100_000)),
            )
        ).total_score
        assert math.isfinite(score)
        assert 0 <= score <= 100


def test_shortlist_is_deterministic_for_equal_scores() -> None:
    engine = ProductIntelligenceEngine(ScoringPolicy())
    rows = [
        make_observation("1", item_id="c", sold=100),
        make_observation("2", item_id="a", sold=100),
        make_observation("3", item_id="b", sold=100),
    ]
    result = engine.shortlist(rows, limit=2)
    assert [entry.product_key[2] for entry in result] == ["a", "b"]
    assert [entry.rank for entry in result] == [1, 2]


def test_shortlist_rejects_invalid_limit_and_threshold() -> None:
    engine = ProductIntelligenceEngine(ScoringPolicy())
    with pytest.raises(ValueError):
        engine.shortlist([make_observation()], limit=0)
    with pytest.raises(ValueError):
        engine.shortlist([make_observation()], limit=1, minimum_score=-1)
    with pytest.raises(ValueError):
        engine.shortlist([make_observation()], limit=1, minimum_score=101)
    with pytest.raises(ValueError):
        engine.shortlist([make_observation()], limit=1, minimum_score=float("nan"))


def test_repository_duplicate_is_idempotent_but_collision_is_conflict() -> None:
    repository = InMemoryProductRepository()
    first = make_observation("same", item_id="A")
    assert repository.add_observations([first]) == 1
    assert repository.add_observations([first]) == 0
    with pytest.raises(ObservationConflictError):
        repository.add_observations([make_observation("same", item_id="B")])


def test_repository_latest_observation_wins_independent_of_ingest_order() -> None:
    repository = InMemoryProductRepository()
    newer = make_observation("new", collected_at=NOW + timedelta(seconds=1), sold=500)
    older = make_observation("old", collected_at=NOW, sold=10)
    repository.add_observations([newer, older])
    assert repository.latest_observations()[0].observation_id == "new"


def test_batch_retry_returns_identical_ack_and_does_not_duplicate() -> None:
    service = make_service()
    observation = make_observation("o1")
    first = service.ingest_batch("batch-1", [observation])
    retry = service.ingest_batch("batch-1", [observation])
    assert retry == first
    assert retry.accepted_count == 1
    assert len(service.repository.latest_observations()) == 1


def test_batch_id_reuse_with_different_payload_is_conflict() -> None:
    service = make_service()
    service.ingest_batch("batch-1", [make_observation("o1", item_id="A")])
    with pytest.raises(IngestionBatchConflictError):
        service.ingest_batch("batch-1", [make_observation("o2", item_id="B")])


def test_path_manager_is_relative_first_and_blocks_escape(tmp_path) -> None:
    paths = PathManager.from_relative(tmp_path, data_dir="data")
    assert paths.data_dir == tmp_path.resolve() / "data"
    with pytest.raises(ValueError):
        PathManager.from_relative(tmp_path, data_dir="../outside")
    with pytest.raises(ValueError):
        PathManager.from_relative(tmp_path, data_dir="/tmp/external")


def test_path_manager_creates_runtime_directories(tmp_path) -> None:
    paths = PathManager.from_relative(tmp_path)
    paths.ensure_runtime_dirs()
    assert all(
        path.is_dir()
        for path in (paths.data_dir, paths.log_dir, paths.outbox_dir, paths.artifact_dir)
    )


def test_settings_constraints_and_toml_precedence(tmp_path, monkeypatch) -> None:
    with pytest.raises(ValidationError):
        Settings(program1={"shortlist_limit": 0})
    with pytest.raises(ValidationError):
        Settings(program1={"minimum_score": 101})
    with pytest.raises(ValidationError):
        Settings(program1={"scoring": {"demand_weight": -1}})

    config = tmp_path / "config"
    config.mkdir()
    (config / "default.toml").write_text(
        '[program1]\nshortlist_limit=10\n[database]\nurl="sqlite:///default.db"\n',
        encoding="utf-8",
    )
    (config / "portable.toml").write_text(
        "[program1]\nshortlist_limit=5\n",
        encoding="utf-8",
    )
    (config / "local.toml").write_text(
        "[program1]\nminimum_score=42\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MTAFFILIATE_DATABASE_URL", "postgresql://test")
    settings = load_settings(tmp_path)
    assert settings.program1.shortlist_limit == 5
    assert settings.program1.minimum_score == 42
    assert settings.database.url == "postgresql://test"
