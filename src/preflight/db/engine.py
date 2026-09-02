"""PO Preflight Database Engine & Connection Factory.

Provides SQLAlchemy Core Engine with automatic dialect detection, connection pooling,
SQLite WAL/Foreign Key pragmas, and transaction utilities.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import Connection
from sqlalchemy.pool import StaticPool

from preflight.config import get_settings


def create_db_engine(database_url_or_path: str | Path | None = None, is_test: bool = False) -> Engine:
    """Create and configure a SQLAlchemy Engine."""
    target = database_url_or_path
    if target is None:
        target = os.getenv("DATABASE_URL") or get_settings().database_url

    url_str = str(target)

    # Normalize sqlite path or memory
    if url_str == ":memory:" or url_str == "sqlite:///:memory:":
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
    elif not (url_str.startswith("postgresql://") or url_str.startswith("postgres://") or url_str.startswith("sqlite://")):
        # Treat as raw filesystem path
        db_path = Path(url_str).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
    else:
        if url_str.startswith("sqlite:///"):
            raw_path = url_str.replace("sqlite:///", "")
            if raw_path != ":memory:":
                Path(raw_path).parent.mkdir(parents=True, exist_ok=True)
            engine = create_engine(
                url_str,
                connect_args={"check_same_thread": False},
                future=True,
            )
        elif url_str.startswith("postgres://"):
            # Normalize old postgres:// scheme to postgresql://
            url_str = url_str.replace("postgres://", "postgresql+psycopg://", 1)
            engine = create_engine(url_str, pool_pre_ping=True, future=True)
        elif url_str.startswith("postgresql://"):
            url_str = url_str.replace("postgresql://", "postgresql+psycopg://", 1)
            engine = create_engine(url_str, pool_pre_ping=True, future=True)
        else:
            engine = create_engine(url_str, future=True)

    # Configure SQLite WAL mode and foreign key enforcement
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA synchronous=NORMAL")
            except Exception:
                pass
            finally:
                cursor.close()

    return engine


_global_engine: Engine | None = None


def get_engine() -> Engine:
    """Returns singleton application engine."""
    global _global_engine
    if _global_engine is None:
        _global_engine = create_db_engine()
    return _global_engine


def get_db_connection() -> Generator[Connection, None, None]:
    """Dependency that yields a managed SQLAlchemy Connection inside a transaction."""
    engine = get_engine()
    with engine.begin() as connection:
        yield connection
