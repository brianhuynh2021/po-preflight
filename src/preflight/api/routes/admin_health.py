from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from preflight.api.deps import get_audit_store, get_outbox_store
from preflight.erp.outbox import BaseOutboxStore
from preflight.observability.tracing import is_otel_enabled
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import AuditStore, BaseAuditStore

router = APIRouter(prefix="/api/v1/admin/health", tags=["Admin System Health & Observability"])


class DatabaseHealth(BaseModel):
    status: str = Field(..., description="DB status: healthy / degraded / error")
    latency_ms: float = Field(..., description="Database query ping latency in milliseconds")
    db_type: str = Field(..., description="sqlite or postgresql")


class OutboxHealth(BaseModel):
    pending: int = 0
    processing: int = 0
    sent: int = 0
    failed: int = 0
    dead_letter: int = 0
    total: int = 0


class InventoryStaleness(BaseModel):
    total_snapshots: int = 0
    stale_count: int = 0
    newest_as_of: str | None = None


class RequestErrorRecord(BaseModel):
    id: int
    request_id: str
    endpoint: str
    status_code: int
    error_message: str
    traceback: str | None = None
    created_at: str


class AdminHealthResponse(BaseModel):
    status: str = Field("healthy", description="Overall cluster/service health")
    environment: str
    version: str
    log_format: str
    otel_enabled: bool
    sentry_enabled: bool
    uptime_seconds: float
    database: DatabaseHealth
    outbox: OutboxHealth
    inventory: InventoryStaleness
    recent_errors: list[RequestErrorRecord]


_START_TIME = time.time()


@router.get(
    "",
    response_model=AdminHealthResponse,
    summary="Comprehensive Admin System Health & Observability",
    description="Returns detailed runtime modes, database latency, outbox backlog, inventory freshness, and recent 5xx errors.",
)
def get_admin_health(
    user: UserPrincipal = Depends(require_role(Role.ADMIN)),
    store: BaseAuditStore = Depends(get_audit_store),
    outbox: BaseOutboxStore = Depends(get_outbox_store),
) -> AdminHealthResponse:
    import preflight

    # 1. Measure DB ping & latency
    t0 = time.perf_counter()
    db_healthy = True
    db_type = "postgresql" if "Postgres" in store.__class__.__name__ else "sqlite"
    try:
        store.get_dashboard_stats()
        db_latency = (time.perf_counter() - t0) * 1000.0
    except Exception:
        db_healthy = False
        db_latency = -1.0

    db_health = DatabaseHealth(
        status="healthy" if db_healthy else "error",
        latency_ms=round(db_latency, 2),
        db_type=db_type,
    )

    # 2. Outbox metrics
    try:
        stats = outbox.get_stats()
        outbox_health = OutboxHealth(
            pending=stats.pending_count,
            processing=stats.processing_count,
            sent=stats.sent_count,
            failed=stats.failed_count,
            dead_letter=stats.dead_letter_count,
            total=stats.total_events,
        )
    except Exception:
        outbox_health = OutboxHealth()

    # 3. Inventory freshness
    try:
        snapshots = store.get_latest_inventory_snapshots()
        policy = store.get_policy()
        stale_hours = policy.inventory_stale_hours
        now_dt = datetime.now(timezone.utc)

        stale_cnt = 0
        newest_str = None
        newest_dt = None

        for sn in snapshots.values():
            if sn.as_of:
                try:
                    dt = datetime.fromisoformat(sn.as_of.replace("Z", "+00:00"))
                    if newest_dt is None or dt > newest_dt:
                        newest_dt = dt
                        newest_str = sn.as_of
                    age = (now_dt - dt).total_seconds() / 3600.0
                    if age > stale_hours:
                        stale_cnt += 1
                except Exception:
                    pass

        inv_health = InventoryStaleness(
            total_snapshots=len(snapshots),
            stale_count=stale_cnt,
            newest_as_of=newest_str,
        )
    except Exception:
        inv_health = InventoryStaleness()

    # 4. Recent 5xx errors from store
    try:
        raw_errs = store.get_recent_request_errors(limit=10)
        recent_errors = [
            RequestErrorRecord(
                id=r["id"],
                request_id=r["request_id"],
                endpoint=r["endpoint"],
                status_code=r["status_code"],
                error_message=r["error_message"],
                traceback=r.get("traceback"),
                created_at=str(r["created_at"]),
            )
            for r in raw_errs
        ]
    except Exception:
        recent_errors = []

    env_val = os.getenv("PREFLIGHT_ENV", "development")
    log_fmt = os.getenv("PREFLIGHT_LOG_FORMAT", "text" if env_val != "production" else "json")
    sentry_on = bool(os.getenv("SENTRY_DSN"))

    overall_status = "healthy"
    if not db_healthy or outbox_health.dead_letter > 0:
        overall_status = "degraded"
    if not db_healthy:
        overall_status = "unhealthy"

    return AdminHealthResponse(
        status=overall_status,
        environment=env_val,
        version=getattr(preflight, "__version__", "0.1.0"),
        log_format=log_fmt,
        otel_enabled=is_otel_enabled(),
        sentry_enabled=sentry_on,
        uptime_seconds=round(time.time() - _START_TIME, 1),
        database=db_health,
        outbox=outbox_health,
        inventory=inv_health,
        recent_errors=recent_errors,
    )
