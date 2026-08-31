from __future__ import annotations

import os
from pathlib import Path

from mtaffiliate.bootstrap.config import load_settings
from mtaffiliate.bootstrap.migrations import upgrade_database_to_head
from mtaffiliate.bootstrap.program1 import build_durable_program1
from mtaffiliate.interfaces.api.app import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE = os.getenv("MTAFFILIATE_PROFILE", "portable")
SETTINGS = load_settings(PROJECT_ROOT, profile=PROFILE)
PATHS = SETTINGS.path_manager(PROJECT_ROOT)
PATHS.ensure_runtime_dirs()

if SETTINGS.database.auto_migrate:
    upgrade_database_to_head(SETTINGS.database.url, project_root=PROJECT_ROOT)

PROGRAM1 = build_durable_program1(SETTINGS, project_root=PROJECT_ROOT)
app = create_app(SETTINGS, program1=PROGRAM1)
