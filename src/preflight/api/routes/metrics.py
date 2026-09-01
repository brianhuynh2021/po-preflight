from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from preflight.api.deps import SERVER_START_TIME, get_audit_store, get_catalog
from preflight.models import Product
from preflight.observability.metrics import metrics_registry
from preflight.store import AuditStore

router = APIRouter(tags=["Observability & Health"])


@router.get(
    "/metrics",
    summary="Prometheus Telemetry Metrics",
    description="Export real-time SLA quantiles, order throughput, RAG tier distributions, and error rates in Prometheus OpenMetrics format.",
    response_class=Response,
)
def get_prometheus_metrics() -> Response:
    content = metrics_registry.generate_prometheus_text()
    return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")


@router.get(
    "/health/live",
    summary="Kubernetes Liveness Probe",
    description="Check if the FastAPI application process is alive and responding.",
)
def liveness_probe() -> dict[str, Any]:
    return {
        "status": "alive",
        "uptime_seconds": round(time.time() - SERVER_START_TIME, 2),
    }


@router.get(
    "/health/ready",
    summary="Kubernetes Readiness Probe",
    description="Deep diagnostic verifying database integrity, catalog accessibility, and runtime storage.",
)
def readiness_probe(
    store: AuditStore = Depends(get_audit_store),
    catalog: dict[str, Product] = Depends(get_catalog),
) -> dict[str, Any]:
    checks: dict[str, str] = {}

    # Check 1: Catalog loaded
    if catalog and len(catalog) > 0:
        checks["catalog"] = f"OK ({len(catalog)} SKUs)"
    else:
        checks["catalog"] = "WARN (Empty catalog)"

    # Check 2: Database connectivity
    try:
        store.list_orders(limit=1)
        checks["database"] = "OK (SQLite connection verified)"
    except Exception as exc:
        checks["database"] = f"ERROR: {exc}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": checks},
        )

    # Check 3: Runtime uploads directory
    uploads_dir = Path("runtime/uploads")
    try:
        uploads_dir.mkdir(parents=True, exist_ok=True)
        checks["storage"] = "OK (Writable)"
    except Exception as exc:
        checks["storage"] = f"ERROR: {exc}"

    all_healthy = all("OK" in str(v) for v in checks.values())

    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
        "database_type": "sqlite",
        "catalog_skus": len(catalog),
    }


@router.get(
    "/api/v1/currency/rate",
    summary="Dynamic FX Currency Exchange Rate",
    description="Retrieve live cached FX exchange rate between supported currencies (USD, VND, EUR) with offline fallback.",
)
def get_exchange_rate(
    base: str = "USD",
    target: str = "VND",
) -> dict[str, Any]:
    from preflight.currency import fx_engine

    rate = fx_engine.get_rate(base, target)
    return {
        "base": base.upper(),
        "target": target.upper(),
        "rate": rate,
        "sample_100_base_in_target": rate * 100.0,
        "cached_engine": "DynamicFXEngine (12h TTL)",
    }
