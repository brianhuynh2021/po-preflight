from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from preflight.api.schemas import RuleConfigResponse, RuleConfigUpdateRequest
from preflight.security.rbac import Role, UserPrincipal, require_role


router = APIRouter(prefix="/api/v1/rules", tags=["Rules & Validation Policy Engine"])

# In-memory policy state
_POLICY_STATE: dict[str, Any] = {
    "price_tolerance_percent": 0.0,
    "stock_safety_margin": 0,
    "allow_inactive_sku": False,
    "auto_approve_ready": False,
}


@router.get(
    "",
    response_model=RuleConfigResponse,
    summary="Get Preflight Validation Policy",
    description="Retrieve currently active rule thresholds and tolerances for deterministic evaluation.",
)
def get_rule_policy() -> RuleConfigResponse:
    return RuleConfigResponse(**_POLICY_STATE)


@router.put(
    "",
    response_model=RuleConfigResponse,
    summary="Update Preflight Validation Policy Thresholds",
    description="Update rule tolerances such as price variance percent or stock safety margins. Requires MANAGER role.",
)
def update_rule_policy(
    payload: RuleConfigUpdateRequest,
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
) -> RuleConfigResponse:
    if payload.price_tolerance_percent is not None:
        _POLICY_STATE["price_tolerance_percent"] = payload.price_tolerance_percent
    if payload.stock_safety_margin is not None:
        _POLICY_STATE["stock_safety_margin"] = payload.stock_safety_margin
    if payload.allow_inactive_sku is not None:
        _POLICY_STATE["allow_inactive_sku"] = payload.allow_inactive_sku
    if payload.auto_approve_ready is not None:
        _POLICY_STATE["auto_approve_ready"] = payload.auto_approve_ready
    return RuleConfigResponse(**_POLICY_STATE)

