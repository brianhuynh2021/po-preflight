from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from preflight.api.deps import get_catalog, get_db_path
from preflight.api.logging_config import RequestLoggingMiddleware, logger
from preflight.security.rate_limiter import RateLimitMiddleware
from preflight.api.routes import (
    agent,
    b2b,
    bot,
    catalog,
    dashboard,
    erp,
    events,
    health,
    ingestion,
    matcher,
    metrics,
    orders,
    rules,
    system,
)

from preflight.parsers import parse_order
from preflight.rules import analyze_order
from preflight.store import AuditStore


def seed_initial_data() -> None:
    """Seed sample orders if the database is newly created or empty."""
    db_path = get_db_path()
    store = AuditStore(db_path)
    try:
        if store.list_orders(limit=1):
            return  # Already seeded

        catalog_data = get_catalog()
        samples = [
            ("examples/orders/po-clean.json", "PO-2026-1001 (Ready - VND)"),
            ("examples/orders/po-review.json", "PO-2026-1002 (Review Required - VND)"),
            ("examples/orders/po-usd.json", "PO-10433 (Global Order - USD)"),
            ("examples/orders/po-blocked.txt", "PO-2026-1003 (Blocked - VND)"),
        ]

        for filepath_str, name in samples:
            p = Path(filepath_str)
            if p.exists():
                try:
                    order = parse_order(p)
                    dup = store.has_po(order.po_number)
                    analysis = analyze_order(order, catalog_data, duplicate=dup)
                    store.record_analysis(analysis, p.name)
                    logger.info(f"Seeded sample order {name} -> {analysis.status}")
                except Exception as e:
                    logger.warning(f"Could not seed {filepath_str}: {e}")

        # Seed an approval decision on PO-10427 for testing
        if store.has_po("PO-10427"):
            from preflight.services.decisions import Principal, decide_order
            principal = Principal(user_id="operations_manager", display_name="operations_manager", role=Role.MANAGER, channel="api")
            try:
                decide_order(
                    store,
                    order_ref="PO-10427",
                    decision="approved",
                    note="Auto-verified clean PO, approved for ERP sync.",
                    principal=principal,
                )
            except Exception as e:
                logger.warning(f"Could not seed initial decision for PO-10427: {e}")
    finally:
        store.close()



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("⚡ Starting PO Preflight REST Gateway...")

    # Startup Security Auditing
    env_name = os.getenv("PREFLIGHT_ENV", "development").strip().lower()
    is_production = env_name in ("production", "prod")
    auth_required = os.getenv("PREFLIGHT_AUTH_REQUIRED", "true").lower() in ("true", "1", "yes")

    if is_production:
        has_prod_key = any(
            os.getenv(k)
            for k in [
                "PREFLIGHT_ADMIN_KEY",
                "PREFLIGHT_MANAGER_KEY",
                "PREFLIGHT_AUDITOR_KEY",
                "PREFLIGHT_VIEWER_KEY",
            ]
        )
        if not has_prod_key:
            logger.error(
                "SECURITY ALERT: Running in PRODUCTION mode with no PREFLIGHT_*_KEY configured! "
                "All authenticated endpoints will reject requests."
            )
    elif not auth_required:
        logger.warning(
            "SECURITY NOTICE: Running in OPEN DEVELOPMENT mode (PREFLIGHT_AUTH_REQUIRED=false). "
            "Anonymous requests will receive dev_admin privileges."
        )

    seed_initial_data()
    logger.info("🚀 PO Preflight REST Gateway is ready! Swagger UI at http://localhost:8000/docs")
    yield
    logger.info("🛑 Shutting down PO Preflight REST Gateway...")



app = FastAPI(
    title="PO Preflight — AI-Native B2B Order Intake & Verification Gateway",
    description="""
# 🚀 PO Preflight REST API

Welcome to the **PO Preflight API Gateway**.

This gateway provides deterministic B2B Purchase Order (PO) intake, validation rules evaluation,
risk scoring, visual grounding evidence citations, and Human-in-the-loop approval workflows.

---

### 🔑 Key Capabilities:
* **System Health:** `/health` - Real-time diagnostics & database health.
* **Order Queue:** `/api/v1/orders` - Filter, search, and inspect orders with violation findings.
* **Intake & Preflight:** `POST /api/v1/orders/upload` - Multipart file upload (PDF/JSON/CSV/TXT).
* **Human Decision:** `POST /api/v1/orders/{order_id}/decide` - Approve, reject, or request changes.
* **Analytics:** `/api/v1/dashboard/stats` - Preflight KPIs, pass rates, and violation breakdown.
* **Catalog:** `/api/v1/catalog` - Master SKU index and warehouse inventory availability.
""",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

import os

# CORS Configuration with environment override
raw_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
)
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
is_wildcard = allowed_origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=not is_wildcard,  # Spec disallows allow_credentials with wildcard '*'
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Logging & Latency Middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Mount Routers
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(orders.router)
app.include_router(dashboard.router)
app.include_router(catalog.router)
app.include_router(rules.router)
app.include_router(matcher.router)
app.include_router(b2b.router)
app.include_router(agent.router)

app.include_router(bot.router)
app.include_router(ingestion.router)
app.include_router(erp.router)
app.include_router(events.router)
app.include_router(system.router)


from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from preflight.api.errors import PreflightError, ValidationFailed


@app.exception_handler(PreflightError)
async def preflight_error_handler(request: Request, exc: PreflightError) -> JSONResponse:
    req_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID", "")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_problem_dict(req_id),
        media_type="application/problem+json",
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    req_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID", "")
    errors = []
    for err in exc.errors():
        loc = ".".join(str(l) for l in err.get("loc", []) if l != "body")
        msg = err.get("msg", "Dữ liệu không hợp lệ.")
        err_type = err.get("type", "")
        if "missing" in err_type:
            msg = "Trường này là bắt buộc."
        elif "string_too_short" in err_type:
            msg = "Độ dài chuỗi quá ngắn."
        elif "int_parsing" in err_type or "decimal" in err_type:
            msg = "Định dạng số không hợp lệ."
        errors.append({"field": loc, "message": msg, "type": err_type})

    validation_exc = ValidationFailed(
        "Dữ liệu yêu cầu không hợp lệ. Vui lòng kiểm tra lại các trường thông tin.",
        errors=errors,
    )
    return JSONResponse(
        status_code=422,
        content=validation_exc.to_problem_dict(req_id),
        media_type="application/problem+json",
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    req_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID", "")
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        413: "PAYLOAD_TOO_LARGE",
        415: "UNSUPPORTED_FORMAT",
        422: "VALIDATION_FAILED",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        503: "UPSTREAM_UNAVAILABLE",
    }
    code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
    doc = {
        "type": f"https://popreflight.vn/errors/{code.lower()}",
        "title": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
        "status": exc.status_code,
        "code": code,
        "detail": str(exc.detail),
        "request_id": req_id,
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=doc,
        media_type="application/problem+json",
    )


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    req_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID", "")
    logger.exception(f"Unhandled system exception occurred [request_id={req_id}]: {exc}")
    doc = {
        "type": "https://popreflight.vn/errors/internal_error",
        "title": "Internal Server Error",
        "status": 500,
        "code": "INTERNAL_ERROR",
        "detail": f"Lỗi hệ thống. Mã tham chiếu: {req_id}",
        "request_id": req_id,
    }
    return JSONResponse(
        status_code=500,
        content=doc,
        media_type="application/problem+json",
    )


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")
