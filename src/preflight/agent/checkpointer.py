from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver


def get_agent_checkpointer(db_url: str | None = None) -> Any:
    """Get persistent checkpointer for LangGraph agent (PostgreSQL or SQLite)."""
    url = db_url or os.getenv("DATABASE_URL")
    if url and (url.startswith("postgresql://") or url.startswith("postgres://")):
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            from psycopg_pool import ConnectionPool

            pool = ConnectionPool(conninfo=url, max_size=10, open=True)
            saver = PostgresSaver(pool)
            saver.setup()
            return saver
        except Exception:
            pass

    # Default to persistent SQLite checkpointer file
    checkpoint_dir = Path("runtime")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    db_file = checkpoint_dir / "agent_checkpoints.db"
    conn = sqlite3.connect(str(db_file), check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()
    return saver
