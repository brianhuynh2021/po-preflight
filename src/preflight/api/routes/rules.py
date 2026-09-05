from __future__ import annotations

from decimal import Decimal
from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from preflight.api.deps import get_store
from preflight.api.schemas import (
    CreateOrganizationScopeRequest,
    CreateRuleDefinitionRequest,
    OrganizationScopeResponse,
    RuleConfigResponse,
    RuleConfigUpdateRequest,
    RuleDefinitionResponse,
    UpdateRuleDefinitionRequest,
)
from preflight.models import OrganizationScope, RuleDefinitionRecord, RulePolicy
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import BaseAuditStore


router = APIRouter(prefix="/api/v1/rules", tags=["Rules & Validation Policy Engine"])


# ---------------------------------------------------------
# Dynamic Policy Thresholds Endpoints
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Dynamic Organization Scopes Endpoints
# ---------------------------------------------------------
@router.get(
    "/scopes",
    response_model=list[OrganizationScopeResponse],
    summary="List Organization Scopes",
    description="Retrieve all available organizational scopes (e.g. global, regions, channels).",
)
def list_scopes(
    store: BaseAuditStore = Depends(get_store),
) -> list[OrganizationScopeResponse]:
    scopes = store.list_organization_scopes()
    return [
        OrganizationScopeResponse(
            id=s.id,
            code=s.code,
            name=s.name,
            description=s.description,
            icon=s.icon,
            parent_code=s.parent_code,
            is_active=s.is_active,
            created_at=s.created_at,
        )
        for s in scopes
    ]


@router.post(
    "/scopes",
    response_model=OrganizationScopeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization Scope",
    description="Add a new organizational hierarchy scope (e.g. branch, warehouse, channel).",
)
def create_scope(
    payload: CreateOrganizationScopeRequest,
    store: BaseAuditStore = Depends(get_store),
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
) -> OrganizationScopeResponse:
    try:
        created = store.create_organization_scope(
            code=payload.code,
            name=payload.name,
            description=payload.description,
            icon=payload.icon,
            parent_code=payload.parent_code,
        )
        return OrganizationScopeResponse(
            id=created.id,
            code=created.code,
            name=created.name,
            description=created.description,
            icon=created.icon,
            parent_code=created.parent_code,
            is_active=created.is_active,
            created_at=created.created_at,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể tạo phạm vi chính sách '{payload.code}': {exc}",
        ) from exc


@router.delete(
    "/scopes/{code}",
    summary="Delete Organization Scope",
    description="Remove a custom scope. Global scope cannot be removed.",
)
def delete_scope(
    code: str,
    store: BaseAuditStore = Depends(get_store),
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
) -> dict[str, Any]:
    if code.lower() == "global":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa phạm vi gốc 'global'",
        )
    success = store.delete_organization_scope(code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy phạm vi '{code}' để xóa",
        )
    return {"success": True, "message": f"Đã xóa phạm vi '{code}' thành công"}


# ---------------------------------------------------------
# Dynamic Rule Definitions Endpoints
# ---------------------------------------------------------
@router.get(
    "/definitions",
    response_model=list[RuleDefinitionResponse],
    summary="List Rule Definitions",
    description="Retrieve configurable rule matrix filtered by organizational scope.",
)
def list_rule_definitions(
    scope: str = "global",
    store: BaseAuditStore = Depends(get_store),
) -> list[RuleDefinitionResponse]:
    rules = store.list_rule_definitions(scope=scope)
    return [
        RuleDefinitionResponse(
            id=r.id,
            code=r.code,
            name=r.name,
            description=r.description,
            category=r.category,
            severity=r.severity,
            owner=r.owner,
            enabled=r.enabled,
            scope=r.scope,
            custom_condition=r.custom_condition,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rules
    ]


@router.post(
    "/definitions",
    response_model=RuleDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Rule Definition",
    description="Create a new custom business rule via Declarative Rule Builder.",
)
def create_rule_definition(
    payload: CreateRuleDefinitionRequest,
    store: BaseAuditStore = Depends(get_store),
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
) -> RuleDefinitionResponse:
    rule_id = payload.id or f"custom_{uuid.uuid4().hex[:8]}"
    record = RuleDefinitionRecord(
        id=rule_id,
        code=payload.code.strip().upper(),
        name=payload.name.strip(),
        description=payload.description.strip(),
        category=payload.category,
        severity=payload.severity,
        owner=payload.owner.strip(),
        enabled=payload.enabled,
        scope=payload.scope.strip().lower(),
        custom_condition=payload.custom_condition.strip() if payload.custom_condition else None,
    )
    saved = store.upsert_rule_definition(record)
    return RuleDefinitionResponse(
        id=saved.id,
        code=saved.code,
        name=saved.name,
        description=saved.description,
        category=saved.category,
        severity=saved.severity,
        owner=saved.owner,
        enabled=saved.enabled,
        scope=saved.scope,
        custom_condition=saved.custom_condition,
        created_at=saved.created_at,
        updated_at=saved.updated_at,
    )


@router.put(
    "/definitions/{rule_id}",
    response_model=RuleDefinitionResponse,
    summary="Update Rule Definition",
    description="Update rule severity, enabled status, or custom conditions.",
)
def update_rule_definition(
    rule_id: str,
    payload: UpdateRuleDefinitionRequest,
    store: BaseAuditStore = Depends(get_store),
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
) -> RuleDefinitionResponse:
    existing_rules = {r.id: r for r in store.list_rule_definitions(scope="all")}
    if rule_id not in existing_rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy quy tắc '{rule_id}'",
        )
    existing = existing_rules[rule_id]
    updated_record = RuleDefinitionRecord(
        id=existing.id,
        code=existing.code,
        name=payload.name if payload.name is not None else existing.name,
        description=payload.description if payload.description is not None else existing.description,
        category=payload.category if payload.category is not None else existing.category,
        severity=payload.severity if payload.severity is not None else existing.severity,
        owner=payload.owner if payload.owner is not None else existing.owner,
        enabled=payload.enabled if payload.enabled is not None else existing.enabled,
        scope=payload.scope if payload.scope is not None else existing.scope,
        custom_condition=payload.custom_condition if payload.custom_condition is not None else existing.custom_condition,
        created_at=existing.created_at,
    )
    saved = store.upsert_rule_definition(updated_record)
    return RuleDefinitionResponse(
        id=saved.id,
        code=saved.code,
        name=saved.name,
        description=saved.description,
        category=saved.category,
        severity=saved.severity,
        owner=saved.owner,
        enabled=saved.enabled,
        scope=saved.scope,
        custom_condition=saved.custom_condition,
        created_at=saved.created_at,
        updated_at=saved.updated_at,
    )


@router.delete(
    "/definitions/{rule_id}",
    summary="Delete Rule Definition",
    description="Delete a custom rule definition.",
)
def delete_rule_definition(
    rule_id: str,
    store: BaseAuditStore = Depends(get_store),
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
) -> dict[str, Any]:
    success = store.delete_rule_definition(rule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy quy tắc '{rule_id}' để xóa",
        )
    return {"success": True, "message": f"Đã xóa quy tắc '{rule_id}' thành công"}
