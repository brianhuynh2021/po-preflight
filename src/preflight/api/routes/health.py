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
from preflight.models import Product
from preflight.store import AuditStore

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

    # Check database tables
    db_connected = False
    tables = []
    try:
        cursor = store.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        db_connected = True
    except Exception:
        db_connected = False

    return HealthResponse(
        status="healthy" if (db_connected and len(catalog) > 0) else "degraded",
        version="0.1.0",
        timestamp=datetime.now(UTC).isoformat(),
        uptime_seconds=round(uptime, 2),
        database=DatabaseStatus(
            connected=db_connected,
            type="sqlite",
            path=str(get_db_path()),
            tables=tables,
        ),
        catalog=CatalogStatus(
            loaded=len(catalog) > 0,
            total_skus=len(catalog),
            source=str(get_catalog_path()),
        ),
    )
