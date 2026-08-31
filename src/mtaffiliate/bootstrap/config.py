from __future__ import annotations

import os
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .paths import PathManager


class AppConfig(BaseModel):
    name: str = "MTAffiliatePlatform"
    environment: str = "development"


class PathsConfig(BaseModel):
    data_dir: str = "data"
    log_dir: str = "logs"
    outbox_dir: str = "runtime/outbox"
    artifact_dir: str = "runtime/artifacts"


class Program1ScoringConfig(BaseModel):
    demand_weight: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    rating_weight: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    review_weight: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    price_fit_weight: float = Field(default=1.0, ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_weight_sum(self) -> "Program1ScoringConfig":
        if (
            self.demand_weight
            + self.rating_weight
            + self.review_weight
            + self.price_fit_weight
            <= 0
        ):
            raise ValueError("at least one Program 1 scoring weight must be positive")
        return self


class Program1Config(BaseModel):
    platform: str = "shopee"
    shortlist_limit: int = Field(default=20, ge=1)
    minimum_score: float = Field(default=0.0, ge=0, le=100, allow_inf_nan=False)
    scoring: Program1ScoringConfig = Program1ScoringConfig()


class WorkerConfig(BaseModel):
    heartbeat_seconds: int = Field(default=30, ge=5)
    batch_size: int = Field(default=50, ge=1)


class DatabaseConfig(BaseModel):
    url: str = "sqlite:///data/app.db"


class Settings(BaseModel):
    app: AppConfig = AppConfig()
    paths: PathsConfig = PathsConfig()
    program1: Program1Config = Program1Config()
    worker: WorkerConfig = WorkerConfig()
    database: DatabaseConfig = DatabaseConfig()

    def path_manager(self, project_root: Path) -> PathManager:
        return PathManager.from_relative(project_root, **self.paths.model_dump())


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_settings(project_root: Path, profile: str = "portable") -> Settings:
    """Load deterministic TOML hierarchy.

    default.toml -> <profile>.toml -> local.toml -> selected environment overrides.
    Secrets should be supplied outside TOML via environment/secret management.
    """
    config_dir = project_root / "config"
    data: dict[str, Any] = {}
    for filename in ("default.toml", f"{profile}.toml", "local.toml"):
        data = _deep_merge(data, _load_toml(config_dir / filename))

    database_url = os.getenv("MTAFFILIATE_DATABASE_URL")
    if database_url:
        data = _deep_merge(data, {"database": {"url": database_url}})
    return Settings.model_validate(data)
