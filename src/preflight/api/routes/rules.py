from __future__ import annotations

from fastapi import APIRouter

from preflight.api.schemas import RuleConfigResponse

router = APIRouter(prefix="/api/v1/rules", tags=["Rules & Validation Policy Engine"])


@router.get(
    "",
    response_model=RuleConfigResponse,
    summary="Get Preflight Validation Policy",
    description="Retrieve currently active rule thresholds and tolerances for deterministic evaluation.",
)
def get_rule_policy() -> RuleConfigResponse:
    return RuleConfigResponse(
        price_tolerance_percent=0.0,
        stock_safety_margin=0,
        allow_inactive_sku=False,
        auto_approve_ready=False,
    )
