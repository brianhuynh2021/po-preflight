from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone, timedelta
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

    # Gather all orders to compute sums, analytics, and violations
    all_rows = store.list_orders(limit=500)

    ready_count = sum(1 for r in all_rows if r["status"] == "ready_for_approval")
    review_required_count = sum(1 for r in all_rows if r["status"] in {"review_required", "needs_changes"})
    blocked_count = sum(1 for r in all_rows if r["status"] == "blocked")
    approved_count = sum(1 for r in all_rows if r.get("latest_decision") == "approved")

    total_value = sum((Decimal(r["total"]) for r in all_rows), start=Decimal("0"))

    now_utc = datetime.now(timezone.utc)
    today_date = now_utc.date()

    approved_today = 0
    decision_durations: list[float] = []

    # 7-day bucket initialization: index 0 is 6 days ago, index 6 is today
    daily_buckets = [0] * 7

    for r in all_rows:
        # Check approved today
        latest_dec = r.get("latest_decision")
        decided_at_str = r.get("decided_at")
        created_at_str = r.get("created_at")

        if decided_at_str:
            try:
                decided_dt = datetime.fromisoformat(decided_at_str.replace("Z", "+00:00"))
                if latest_dec == "approved" and decided_dt.date() == today_date:
                    approved_today += 1
                if created_at_str:
                    created_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    diff_mins = (decided_dt - created_dt).total_seconds() / 60.0
                    if diff_mins >= 0:
                        decision_durations.append(diff_mins)
            except Exception:
                pass

        if created_at_str:
            try:
                created_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                days_ago = (today_date - created_dt.date()).days
                if 0 <= days_ago < 7:
                    daily_buckets[6 - days_ago] += 1
            except Exception:
                pass

    avg_decision_minutes = (
        round(sum(decision_durations) / len(decision_durations), 1) if decision_durations else None
    )
    straight_through_rate = (
        round((ready_count / total_orders * 100), 1) if total_orders > 0 else 0.0
    )

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
        approved_today=approved_today,
        avg_decision_minutes=avg_decision_minutes,
        orders_last_7_days=daily_buckets,
        straight_through_rate=straight_through_rate,
        pass_rate_percent=pass_rate,
        total_pipeline_value=total_value,
        violations_breakdown=violations_breakdown,
        recent_orders=stats["recent_orders"],
    )
