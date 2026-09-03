"""
FastAPI Routes for Pilot Telemetry & Operational Reporting.
Provides endpoints for KPI aggregation, RFC-4180 CSV export, and weekly summary emails.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, Response

from preflight.api.deps import get_audit_store
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.services.pilot_reports import (
    generate_pilot_csv,
    generate_pilot_report,
    send_weekly_pilot_email,
)
from preflight.store import BaseAuditStore

logger = logging.getLogger("PreflightAPIReporters")

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/pilot", summary="Get Pilot KPI Report (JSON)")
def get_pilot_metrics(
    from_date: str | None = Query(None, description="Start date (ISO format)"),
    to_date: str | None = Query(None, description="End date (ISO format)"),
    current_user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: BaseAuditStore = Depends(get_audit_store),
) -> dict[str, Any]:
    """Retrieve comprehensive pilot performance and operational impact metrics."""
    return generate_pilot_report(store, from_date=from_date, to_date=to_date)


@router.get("/pilot.csv", summary="Export Pilot KPI Report (CSV)")
def export_pilot_metrics_csv(
    from_date: str | None = Query(None, description="Start date (ISO format)"),
    to_date: str | None = Query(None, description="End date (ISO format)"),
    current_user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: BaseAuditStore = Depends(get_audit_store),
) -> Response:
    """Download pilot operational report as RFC-4180 compliant CSV."""
    report_data = generate_pilot_report(store, from_date=from_date, to_date=to_date)
    csv_content = generate_pilot_csv(report_data)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="po_preflight_pilot_report.csv"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


@router.post("/send-weekly-email", summary="Trigger Weekly Pilot Email Dispatch")
def trigger_weekly_email(
    to_email: str | None = Query(None, description="Optional override recipient email"),
    current_user: UserPrincipal = Depends(require_role(Role.ADMIN)),
    store: BaseAuditStore = Depends(get_audit_store),
) -> dict[str, Any]:
    """Dispatch automated weekly summary email to administrator or designated recipient."""
    report_data = generate_pilot_report(store)
    return send_weekly_pilot_email(to_email=to_email, report_data=report_data)
