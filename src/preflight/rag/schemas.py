from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ResolutionTier(str, Enum):
    TIER_1_EXACT = "TIER_1_EXACT"
    TIER_2_FUZZY = "TIER_2_FUZZY"
    TIER_3_SEMANTIC_VECTOR = "TIER_3_SEMANTIC_VECTOR"
    TIER_4_LLM_CONTEXT = "TIER_4_LLM_CONTEXT"
    UNRESOLVED = "UNRESOLVED"


class MatchCandidate(BaseModel):
    sku: str = Field(..., description="Target catalog SKU")
    name: str = Field(..., description="Product name in catalog")
    unit_price: Decimal = Field(..., description="Catalog unit price")
    stock: int = Field(..., description="Current warehouse stock")
    active: bool = Field(True, description="Whether product is active")
    score: float = Field(..., description="Match confidence score (0.0 to 1.0)")
    tier: ResolutionTier = Field(..., description="Resolution tier used")


class MatchResult(BaseModel):
    raw_query: str = Field(..., description="Original raw line item text or SKU from PO")
    matched_sku: str | None = Field(None, description="Resolved catalog SKU if found")
    name: str | None = Field(None, description="Official catalog product name")
    unit_price: Decimal | None = Field(None, description="Official catalog unit price")
    stock: int | None = Field(None, description="Available stock count")
    active: bool = Field(True, description="Product active status")
    confidence_score: float = Field(..., description="Normalized confidence score (0.0 to 1.0)")
    tier_used: ResolutionTier = Field(..., description="Waterfall tier that resolved this item")
    is_confident: bool = Field(..., description="Whether match exceeds confidence threshold (>= 0.80)")
    explanation: str = Field(..., description="Human-readable grounding rationale")
    candidates: list[MatchCandidate] = Field(default_factory=list, description="Top alternative candidates")


class ResolveRequest(BaseModel):
    raw_text: str = Field(..., description="Raw SKU or product name from incoming PO", example="Cáp mạng Cat6 3m bấm sẵn")
    customer_id: str | None = Field(None, description="Optional customer identifier for historical context", example="CUST-NORTHSTAR")


class BatchResolveRequest(BaseModel):
    items: list[ResolveRequest] = Field(..., description="List of raw item queries to resolve")
