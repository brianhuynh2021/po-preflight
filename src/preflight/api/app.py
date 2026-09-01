from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from preflight.api.deps import get_catalog, get_db_path
from preflight.api.logging_config import RequestLoggingMiddleware, logger
from preflight.api.routes import (
    agent,
    bot,
    catalog,
    dashboard,
    erp,
    health,
    ingestion,
    matcher,
    orders,
    rules,
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
            store.record_decision(
                po_number="PO-10427",
                decision="approved",
                actor="operations_manager",
                note="Auto-verified clean PO, approved for ERP sync.",
            )
    finally:
        store.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("⚡ Starting PO Preflight REST Gateway...")
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

# CORS Configuration for local Web development (Vite, Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev (Vite on :5173, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Logging & Latency Middleware
app.add_middleware(RequestLoggingMiddleware)

# Mount Routers
app.include_router(health.router)
app.include_router(orders.router)
app.include_router(dashboard.router)
app.include_router(catalog.router)
app.include_router(rules.router)
app.include_router(matcher.router)
app.include_router(agent.router)
app.include_router(bot.router)
app.include_router(ingestion.router)
app.include_router(erp.router)


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")
