from __future__ import annotations

from decimal import Decimal
from fastapi import APIRouter, Depends
from preflight.api.deps import get_store
from preflight.api.schemas import RuleConfigResponse, RuleConfigUpdateRequest
from preflight.models import RulePolicy
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import BaseAuditStore


router = APIRouter(prefix="/api/v1/rules", tags=["Rules & Validation Policy Engine"])


@router.get(
    "",
    response_model=RuleConfigResponse,
    summary="Get Preflight Validation Policy",
    description="Retrieve currently active rule thresholds and tolerances for deterministic evaluation.",
)
def get_rule_policy(
    store: BaseAuditStore = Depends(get_store),
) -> RuleConfigResponse:
    policy = store.get_policy()
    return RuleConfigResponse(
        price_tolerance_percent=float(policy.price_tolerance_percent),
        stock_safety_margin=policy.stock_safety_margin,
        allow_inactive_sku=policy.allow_inactive_sku,
        auto_approve_ready=policy.auto_approve_ready,
    )


@router.put(
    "",
    response_model=RuleConfigResponse,
    summary="Update Preflight Validation Policy Thresholds",
    description="Update rule tolerances such as price variance percent or stock safety margins. Requires MANAGER role.",
)
def update_rule_policy(
    payload: RuleConfigUpdateRequest,
    store: BaseAuditStore = Depends(get_store),
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
) -> RuleConfigResponse:
    current = store.get_policy()
    updated = RulePolicy(
        price_tolerance_percent=Decimal(str(payload.price_tolerance_percent)) if payload.price_tolerance_percent is not None else current.price_tolerance_percent,
        stock_safety_margin=payload.stock_safety_margin if payload.stock_safety_margin is not None else current.stock_safety_margin,
        allow_inactive_sku=payload.allow_inactive_sku if payload.allow_inactive_sku is not None else current.allow_inactive_sku,
        auto_approve_ready=payload.auto_approve_ready if payload.auto_approve_ready is not None else current.auto_approve_ready,
    )
    store.set_policy(updated, updated_by=user.username)
    return RuleConfigResponse(
        price_tolerance_percent=float(updated.price_tolerance_percent),
        stock_safety_margin=updated.stock_safety_margin,
        allow_inactive_sku=updated.allow_inactive_sku,
        auto_approve_ready=updated.auto_approve_ready,
    )


