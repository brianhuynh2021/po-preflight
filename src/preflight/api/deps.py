import os
import time
from pathlib import Path
from typing import Any, Generator

from preflight.catalog import load_catalog
from preflight.config import get_settings
from preflight.models import Product
from preflight.store import BaseAuditStore, create_audit_store

DEFAULT_DB_PATH = Path("runtime/preflight.db")
DEFAULT_CATALOG_PATH = Path("examples/catalog.csv")

SERVER_START_TIME = time.time()


def get_catalog_path() -> Path:
    env_path = os.getenv("CATALOG_PATH")
    if env_path:
        return Path(env_path)
    return Path(get_settings().catalog_path)


def get_db_path() -> str | Path:
    env_db = os.getenv("DATABASE_URL")
    if env_db:
        if env_db.startswith("postgres"):
            return env_db
        if env_db.startswith("sqlite:///"):
            return Path(env_db.replace("sqlite:///", ""))
        return Path(env_db)

    settings = get_settings()
    if settings.database_url.startswith("postgres"):
        return settings.database_url
    if settings.database_url.startswith("sqlite:///"):
        return Path(settings.database_url.replace("sqlite:///", ""))
    return Path(settings.database_url)


def get_catalog() -> dict[str, Product]:
    cat_path = get_catalog_path()
    if cat_path.exists():
        return load_catalog(cat_path)
    return {}


def get_audit_store() -> Generator[BaseAuditStore, None, None]:
    db_target = get_db_path()
    store = create_audit_store(db_target)
    try:
        yield store
    finally:
        store.close()


get_store = get_audit_store


def get_outbox_store() -> Generator[Any, None, None]:
    from preflight.erp.outbox import create_outbox_store
    db_target = get_db_path()
    outbox = create_outbox_store(db_target)
    try:
        yield outbox
    finally:
        outbox.close()

