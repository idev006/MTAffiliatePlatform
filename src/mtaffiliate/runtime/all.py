from __future__ import annotations

from mtaffiliate.runtime._factory import create_runtime_app

app = create_runtime_app({"program1", "program2", "program3"}, default_profile="portable")
