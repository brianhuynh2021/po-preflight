import os
import time
from pathlib import Path
from typing import Generator

from preflight.catalog import load_catalog
from preflight.models import Product
from preflight.store import AuditStore, BaseAuditStore, create_audit_store

DEFAULT_DB_PATH = Path("runtime/preflight.db")
DEFAULT_CATALOG_PATH = Path("examples/catalog.csv")

SERVER_START_TIME = time.time()


def get_catalog_path() -> Path:
    env_path = os.getenv("CATALOG_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_CATALOG_PATH


def get_db_path() -> Path:
    return DEFAULT_DB_PATH


def get_catalog() -> dict[str, Product]:
    cat_path = get_catalog_path()
    if cat_path.exists():
        return load_catalog(cat_path)
    return {}


def get_audit_store() -> Generator[BaseAuditStore, None, None]:
    db_path = get_db_path()
    store = create_audit_store(db_path)
    try:
        yield store
    finally:
        store.close()


get_store = get_audit_store

