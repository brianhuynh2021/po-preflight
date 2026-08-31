from __future__ import annotations

from fastapi import APIRouter, Depends

from preflight.api.deps import get_catalog
from preflight.models import Product
from preflight.rag.matcher import HybridSKUMatcher
from preflight.rag.schemas import BatchResolveRequest, MatchResult, ResolveRequest

router = APIRouter(prefix="/api/v1/sku", tags=["SKU Resolution & Hybrid RAG"])


@router.post(
    "/resolve",
    response_model=MatchResult,
    summary="Resolve Ambiguous SKU via 4-Tier Hybrid RAG",
    description=(
        "Cascade through Tier 1 (Exact) -> Tier 2 (Fuzzy RapidFuzz) -> Tier 3 (Semantic Vector) -> Tier 4 (LLM Context) "
        "to resolve raw order line item text to official catalog product SKU with confidence scoring."
    ),
)
def resolve_sku(
    payload: ResolveRequest,
    catalog: dict[str, Product] = Depends(get_catalog),
) -> MatchResult:
    matcher = HybridSKUMatcher(catalog)
    return matcher.resolve(payload.raw_text, customer_id=payload.customer_id)


@router.post(
    "/batch-resolve",
    response_model=list[MatchResult],
    summary="Batch Resolve Multiple SKUs",
    description="Resolve multiple line items in parallel via the 4-tier waterfall engine.",
)
def batch_resolve_skus(
    payload: BatchResolveRequest,
    catalog: dict[str, Product] = Depends(get_catalog),
) -> list[MatchResult]:
    matcher = HybridSKUMatcher(catalog)
    return [matcher.resolve(item.raw_text, customer_id=item.customer_id) for item in payload.items]
