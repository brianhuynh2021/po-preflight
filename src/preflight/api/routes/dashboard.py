from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal

from fastapi import APIRouter, Depends

from preflight.api.deps import get_audit_store
from preflight.api.schemas import DashboardStatsResponse, ViolationBreakdown
from preflight.store import AuditStore

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard & Analytics"])


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get Preflight KPI Metrics & Breakdown",
    description="Retrieve aggregated statistics, risk distribution, pass rate, and violation breakdown.",
)
def get_dashboard_stats(store: AuditStore = Depends(get_audit_store)) -> DashboardStatsResponse:
    stats = store.get_dashboard_stats()
    total_orders = stats["total_orders"]

    # Gather all orders to compute sums and violations
    all_rows = store.list_orders(limit=500)

    ready_count = sum(1 for r in all_rows if r["status"] == "ready_for_approval")
    review_required_count = sum(1 for r in all_rows if r["status"] in {"review_required", "needs_changes"})
    blocked_count = sum(1 for r in all_rows if r["status"] == "blocked")
    approved_count = sum(1 for r in all_rows if r.get("latest_decision") == "approved")

    total_value = sum((Decimal(r["total"]) for r in all_rows), start=Decimal("0"))

    # Compute violations breakdown
    code_counts: Counter[str] = Counter()
    total_findings = 0
    for r in all_rows:
        if r.get("findings_json"):
            try:
                findings = json.loads(r["findings_json"])
                for f in findings:
                    code_counts[f["code"]] += 1
                    total_findings += 1
            except Exception:
                pass

    violations_breakdown = [
        ViolationBreakdown(
            code=code,
            count=count,
            percentage=round((count / total_findings * 100), 1) if total_findings > 0 else 0.0,
        )
        for code, count in code_counts.most_common()
    ]

    pass_rate = round(((ready_count + approved_count) / total_orders * 100), 1) if total_orders > 0 else 100.0

    return DashboardStatsResponse(
        total_orders=total_orders,
        ready_count=ready_count,
        review_required_count=review_required_count,
        blocked_count=blocked_count,
        approved_count=approved_count,
        pass_rate_percent=pass_rate,
        total_pipeline_value=total_value,
        violations_breakdown=violations_breakdown,
        recent_orders=stats["recent_orders"],
    )
