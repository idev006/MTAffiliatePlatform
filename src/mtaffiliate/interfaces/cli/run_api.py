from __future__ import annotations

import os

import uvicorn


def _run(module_path: str) -> None:
    host = os.getenv("MTAFFILIATE_HOST", "127.0.0.1")
    port = int(os.getenv("MTAFFILIATE_PORT", "8000"))
    uvicorn.run(module_path, host=host, port=port)


def main_all() -> None:
    _run("mtaffiliate.runtime.all:app")


def main_program1() -> None:
    _run("mtaffiliate.runtime.program1:app")


def main_program2() -> None:
    _run("mtaffiliate.runtime.program2:app")


def main_program3() -> None:
    _run("mtaffiliate.runtime.program3:app")
