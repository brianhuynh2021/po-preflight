from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends

from preflight.api.deps import get_audit_store, get_catalog
from preflight.models import Product
from preflight.rag.matcher import HybridSKUMatcher
from preflight.rag.schemas import BatchResolveRequest, MatchResult, ResolveRequest
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import AuditStore
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/sku", tags=["SKU Resolution & Hybrid RAG"])


class LearnAliasRequest(BaseModel):
    customer_id: str = Field(..., description="Customer account identifier")
    raw_query: str = Field(..., description="Customer-specific vernacular product name / nickname")
    target_sku: str = Field(..., description="Official catalog SKU code to associate")


@router.post(
    "/resolve",
    response_model=MatchResult,
    summary="Resolve Ambiguous SKU via 4-Tier Hybrid RAG",
    description=(
        "Cascade through Tier 0 (Active Learning) -> Tier 1 (Exact) -> Tier 2 (Fuzzy) -> Tier 3 (Semantic Vector) -> Tier 4 (LLM Context) "
        "to resolve raw order line item text to official catalog product SKU with confidence scoring."
    ),
)
def resolve_sku(
    payload: ResolveRequest,
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
    catalog: dict[str, Product] = Depends(get_catalog),
    store: AuditStore = Depends(get_audit_store),
) -> MatchResult:
    matcher = HybridSKUMatcher(catalog, store=store)
    return matcher.resolve(payload.raw_text, customer_id=payload.customer_id)


@router.post(
    "/batch-resolve",
    response_model=list[MatchResult],
    summary="Batch Resolve Multiple SKUs",
    description="Resolve multiple line items in parallel via the 4-tier waterfall engine.",
)
def batch_resolve_skus(
    payload: BatchResolveRequest,
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
    catalog: dict[str, Product] = Depends(get_catalog),
    store: AuditStore = Depends(get_audit_store),
) -> list[MatchResult]:
    matcher = HybridSKUMatcher(catalog, store=store)
    return [matcher.resolve(item.raw_text, customer_id=item.customer_id) for item in payload.items]


@router.post(
    "/aliases/learn",
    summary="Record Learned Customer Alias (Active Learning)",
    description="Train the active learning engine with a customer-specific product alias/nickname.",
)
def learn_customer_alias(
    payload: LearnAliasRequest,
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    catalog: dict[str, Product] = Depends(get_catalog),
    store: AuditStore = Depends(get_audit_store),
) -> dict[str, Any]:

    matcher = HybridSKUMatcher(catalog, store=store)
    matcher.learn_alias(payload.customer_id, payload.raw_query, payload.target_sku)
    return {
        "success": True,
        "message": f"Successfully mapped '{payload.raw_query}' -> '{payload.target_sku}' for customer '{payload.customer_id}'",
        "customer_id": payload.customer_id,
        "raw_query": payload.raw_query,
        "target_sku": payload.target_sku,
    }


@router.get(
    "/aliases",
    summary="List Learned Customer Aliases",
    description="Retrieve all active learning product nicknames and alias memory mappings.",
)
def list_aliases(
    customer_id: str | None = None,
    store: AuditStore = Depends(get_audit_store),
) -> list[dict[str, Any]]:
    return store.list_customer_aliases(customer_id=customer_id)
