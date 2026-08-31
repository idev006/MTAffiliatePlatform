from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathManager:
    """Resolve project/runtime-owned paths from explicit relative roots.

    Domain/application code should pass logical/relative references. Absolute
    paths are produced only here at the infrastructure boundary. Managed paths
    are not allowed to escape the project root.
    """

    project_root: Path
    data_dir: Path
    log_dir: Path
    outbox_dir: Path
    artifact_dir: Path

    @classmethod
    def from_relative(
        cls,
        project_root: Path,
        *,
        data_dir: str = "data",
        log_dir: str = "logs",
        outbox_dir: str = "runtime/outbox",
        artifact_dir: str = "runtime/artifacts",
    ) -> PathManager:
        root = project_root.resolve()
        return cls(
            project_root=root,
            data_dir=cls._resolve_under(root, data_dir),
            log_dir=cls._resolve_under(root, log_dir),
            outbox_dir=cls._resolve_under(root, outbox_dir),
            artifact_dir=cls._resolve_under(root, artifact_dir),
        )

    @staticmethod
    def _resolve_under(root: Path, value: str | Path) -> Path:
        candidate = Path(value)
        if candidate.is_absolute():
            raise ValueError("managed paths must be relative")
        resolved = (root / candidate).resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError("managed path escapes project root") from exc
        return resolved

    def ensure_runtime_dirs(self) -> None:
        for path in (self.data_dir, self.log_dir, self.outbox_dir, self.artifact_dir):
            path.mkdir(parents=True, exist_ok=True)
