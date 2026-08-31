from __future__ import annotations

import os
from pathlib import Path

from mtaffiliate.bootstrap.config import load_settings
from mtaffiliate.interfaces.api.app import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE = os.getenv("MTAFFILIATE_PROFILE", "portable")
SETTINGS = load_settings(PROJECT_ROOT, profile=PROFILE)
PATHS = SETTINGS.path_manager(PROJECT_ROOT)
PATHS.ensure_runtime_dirs()

app = create_app(SETTINGS)
