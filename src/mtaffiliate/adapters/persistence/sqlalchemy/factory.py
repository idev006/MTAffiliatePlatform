from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def resolve_database_url(database_url: str, project_root: Path) -> str:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix) or database_url.startswith("sqlite:////"):
        return database_url
    relative = database_url.removeprefix(prefix)
    if not relative or relative == ":memory:":
        return database_url
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("SQLite managed database path must be relative and remain under project root")
    resolved = (project_root.resolve() / candidate).resolve()
    if resolved != project_root.resolve() and project_root.resolve() not in resolved.parents:
        raise ValueError("SQLite database path escapes project root")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{resolved.as_posix()}"


def build_engine(database_url: str, *, project_root: Path) -> Engine:
    url = resolve_database_url(database_url, project_root)
    engine = create_engine(url, future=True)
    if url.startswith("sqlite:"):
        @event.listens_for(engine, "connect")
        def configure_sqlite(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()
    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
