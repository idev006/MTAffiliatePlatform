from __future__ import annotations

from pathlib import Path

from mtaffiliate.application.program2 import Program2Service
from mtaffiliate.application.program3 import Program3Service
from mtaffiliate.bootstrap.config import Settings
from mtaffiliate.bootstrap.program2 import build_durable_program2
from mtaffiliate.bootstrap.program3 import build_durable_program3


def build_durable_program2_program3(
    settings: Settings,
    *,
    project_root: Path,
) -> tuple[Program2Service, Program3Service]:
    return (
        build_durable_program2(settings, project_root=project_root),
        build_durable_program3(settings, project_root=project_root),
    )
