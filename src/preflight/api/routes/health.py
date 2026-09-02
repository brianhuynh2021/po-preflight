from __future__ import annotations

import time
from datetime import UTC, datetime
from fastapi import APIRouter, Depends

from preflight.api.deps import (
    SERVER_START_TIME,
    get_audit_store,
    get_catalog,
    get_catalog_path,
    get_db_path,
)
from preflight.api.schemas import CatalogStatus, DatabaseStatus, HealthResponse
import preflight
from preflight.models import Product
from preflight.store import AuditStore, PostgresAuditStore

router = APIRouter(tags=["System Health & Diagnostics"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health & Diagnostic Status",
    description="Returns the operational health, database connectivity, loaded catalog stats, and server uptime.",
)
def get_health(
    store: AuditStore = Depends(get_audit_store),
    catalog: dict[str, Product] = Depends(get_catalog),
) -> HealthResponse:
    uptime = time.time() - SERVER_START_TIME

    # Check database connectivity and tables
    db_connected = False
    tables = []
    db_type = "postgresql" if isinstance(store, PostgresAuditStore) else "sqlite"
    db_path = getattr(store, "database_url", str(get_db_path()))

    try:
        if isinstance(store, PostgresAuditStore):
            with store._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                    )
                    tables = [row["table_name"] if isinstance(row, dict) else row[0] for row in cur.fetchall()]
            db_connected = True
        else:
            cursor = store.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            db_connected = True
    except Exception:
        db_connected = False

    return HealthResponse(
        status="healthy" if (db_connected and len(catalog) > 0) else "degraded",
        version=getattr(preflight, "__version__", "0.2.0"),
        timestamp=datetime.now(UTC).isoformat(),
        uptime_seconds=round(uptime, 2),
        database=DatabaseStatus(
            connected=db_connected,
            type=db_type,
            path=str(db_path),
            tables=tables,
        ),
        catalog=CatalogStatus(
            loaded=len(catalog) > 0,
            total_skus=len(catalog),
            source=str(get_catalog_path()),
        ),
    )
