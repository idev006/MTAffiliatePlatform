from pathlib import Path

from mtaffiliate.bootstrap.paths import PathManager


def test_path_manager_resolves_relative_paths(tmp_path: Path) -> None:
    paths = PathManager.from_relative(tmp_path, data_dir="data", outbox_dir="runtime/outbox")
    assert paths.data_dir == (tmp_path / "data").resolve()
    assert paths.outbox_dir == (tmp_path / "runtime/outbox").resolve()
