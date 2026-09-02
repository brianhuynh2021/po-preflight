from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# Health Check Schema
# ---------------------------------------------------------
class DatabaseStatus(BaseModel):
    connected: bool = Field(True, description="Whether the database connection is alive")
    type: str = Field("sqlite", description="Database engine type (sqlite/postgresql)")
    path: str = Field("runtime/preflight.db", description="Database file path or connection URI")
    tables: list[str] = Field(default_factory=lambda: ["analyses", "decisions"], description="Available tables")


class CatalogStatus(BaseModel):
    loaded: bool = Field(True, description="Whether catalog is loaded")
    total_skus: int = Field(24, description="Number of active/registered SKUs")
    source: str = Field("examples/catalog.csv", description="Catalog source path")


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"] = Field("healthy", description="Overall service status")
    version: str = Field("0.1.0", description="Application version")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    uptime_seconds: float = Field(..., description="Uptime of the API server in seconds")
    database: DatabaseStatus = Field(..., description="Database connection health")
    catalog: CatalogStatus = Field(..., description="Catalog index health")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "timestamp": "2026-08-31T07:15:00.000Z",
                "uptime_seconds": 342.15,
                "database": {
                    "connected": True,
                    "type": "sqlite",
                    "path": "runtime/preflight.db",
                    "tables": ["analyses", "decisions"],
                },
                "catalog": {
                    "loaded": True,
                    "total_skus": 24,
                    "source": "examples/catalog.csv",
                },
            }
        }
    }


# ---------------------------------------------------------
# Line Item & Finding Schemas
# ---------------------------------------------------------
class FindingResponse(BaseModel):
    code: str = Field(
        ..., description="Deterministic validation code (e.g., PRICE_MISMATCH, INSUFFICIENT_STOCK, CUSTOMER_BLOCKED, etc.)"
    )
    severity: Literal["error", "warning", "info"] = Field(..., description="Severity level")
    message: str = Field(..., description="Human-readable explanation")
    sku: str | None = Field(None, description="Affected SKU if applicable")

    evidence: str | None = Field(None, description="Grounding evidence citation")

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "PRICE_MISMATCH",
                "severity": "warning",
                "message": "SKU CAB-CAT6-3M: PO price 75,000, catalog price 72,000 (+4.17% diff).",
                "sku": "CAB-CAT6-3M",
                "evidence": "Catalog unit price is 72,000 VND per Master Price Agreement #2026-01.",
            }
        }
    }


class LineItemResponse(BaseModel):
    line_number: int = Field(..., description="Line index in the PO (1-based)")
    sku: str = Field(..., description="Extracted SKU from document")
    name: str = Field(..., description="Catalog product name or raw document text")
    quantity: int = Field(..., description="Ordered quantity")
    unit_price: Decimal = Field(..., description="Ordered unit price")
    catalog_unit_price: Decimal | None = Field(None, description="Official price in catalog")
    price_diff_percent: float | None = Field(None, description="Percentage price discrepancy")
    stock_available: int | None = Field(None, description="Current stock in warehouse")
    stock_status: Literal["IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK"] | None = Field(
        None, description="Inventory availability status"
    )
    status: Literal["MATCHED", "MISMATCH", "UNKNOWN"] = Field("MATCHED", description="Line verification status")


# ---------------------------------------------------------
# Order Schemas
# ---------------------------------------------------------
class OrderSummaryResponse(BaseModel):
    id: int = Field(..., description="Primary analysis ID in audit store")
    po_number: str = Field(..., description="Purchase Order number (e.g. PO-10428)")
    customer: str = Field(..., description="Customer company name")
    status: Literal["ready_for_approval", "review_required", "blocked", "approved", "rejected", "needs_changes", "extraction_review"] = (
        Field(..., description="Lifecycle status")
    )
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Computed risk score")
    total: Decimal = Field(..., description="Total monetary value of order")
    currency: str = Field("VND", description="Currency code (VND, USD, etc.)")
    items_count: int = Field(..., description="Number of line items in order")
    findings_count: int = Field(..., description="Total validation warnings/errors")
    error_count: int = Field(..., description="Total blocking errors")
    warning_count: int = Field(..., description="Total review warnings")
    source_file: str = Field(..., description="Source filename or origin channel")
    created_at: str = Field(..., description="Received timestamp")
    latest_decision: str | None = Field(None, description="Latest human decision if any")
    decided_at: str | None = Field(None, description="Decision timestamp if any")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "po_number": "PO-10428",
                "customer": "Northstar Retail",
                "status": "review_required",
                "risk_level": "MEDIUM",
                "total": "18500000.00",
                "currency": "VND",
                "items_count": 2,
                "findings_count": 1,
                "error_count": 0,
                "warning_count": 1,
                "source_file": "order-10428.pdf",
                "created_at": "2026-09-01T08:00:00Z",
                "latest_decision": None,
                "decided_at": None,
            }
        }
    }


class OrderDetailResponse(BaseModel):
    id: int = Field(..., description="Order ID in audit store")
    po_number: str = Field(..., description="Purchase Order identifier")
    customer: str = Field(..., description="Customer legal entity name")
    status: Literal["ready_for_approval", "review_required", "blocked", "approved", "rejected", "needs_changes", "extraction_review"] = (
        Field(..., description="Lifecycle verification state")
    )
    risk_level: str = Field(..., description="Computed risk level")
    total: Decimal = Field(..., description="Total order amount")
    currency: str = Field("VND", description="Currency code")
    source_file: str = Field(..., description="Original file path or channel")
    created_at: str = Field(..., description="Ingestion timestamp")
    items: list[LineItemResponse] = Field(default_factory=list, description="Parsed line items")
    findings: list[FindingResponse] = Field(default_factory=list, description="Validation findings")
    decisions: list[dict[str, Any]] = Field(default_factory=list, description="Audit decision timeline")


class DecisionRequest(BaseModel):
    decision: Literal["approved", "rejected", "needs_changes"] = Field(
        ..., description="Human decision action"
    )
    actor: str = Field("operations_manager", description="Username or email of the reviewer")
    note: str = Field("", description="Optional justification or rejection reason")

    model_config = {
        "json_schema_extra": {
            "example": {
                "decision": "approved",
                "actor": "manager@company.com",
                "note": "Approved with price exception per customer email agreement.",
            }
        }
    }


class DecisionResponse(BaseModel):
    success: bool = Field(True, description="Whether the decision was recorded")
    id: int = Field(..., description="Decision audit log ID")
    po_number: str = Field(..., description="Target PO number")
    decision: str = Field(..., description="Recorded decision")
    actor: str = Field(..., description="Reviewer actor")
    note: str = Field(..., description="Decision note")
    created_at: str = Field(..., description="Decision timestamp")


# ---------------------------------------------------------
# Dashboard Stats & Rule Config Schemas
# ---------------------------------------------------------
class ViolationBreakdown(BaseModel):
    code: str = Field(..., description="Violation code")
    count: int = Field(..., description="Occurrence count")
    percentage: float = Field(..., description="Percentage of total findings")


class DashboardStatsResponse(BaseModel):
    total_orders: int = Field(..., description="Total number of ingested POs")
    ready_count: int = Field(..., description="Orders ready for instant approval")
    review_required_count: int = Field(..., description="Orders requiring human review")
    blocked_count: int = Field(..., description="Orders blocked due to fatal errors")
    approved_count: int = Field(..., description="Orders successfully approved")
    pass_rate_percent: float = Field(..., description="Percentage of orders without errors")
    total_pipeline_value: Decimal = Field(..., description="Total monetary volume analyzed")
    violations_breakdown: list[ViolationBreakdown] = Field(default_factory=list, description="Top violations")
    recent_orders: list[dict[str, Any]] = Field(default_factory=list, description="5 most recent orders")


class CatalogItemResponse(BaseModel):
    sku: str = Field(..., description="Unique product SKU")
    name: str = Field(..., description="Product name")
    unit_price: Decimal = Field(..., description="Standard catalog unit price")
    stock: int = Field(..., description="Available warehouse stock")
    active: bool = Field(True, description="Whether product is active")


class RuleConfigResponse(BaseModel):
    price_tolerance_percent: float = Field(0.0, description="Allowed price variance before flagging")
    stock_safety_margin: int = Field(0, description="Buffer quantity for inventory checks")
    allow_inactive_sku: bool = Field(False, description="Allow purchasing deactivated items")
    auto_approve_ready: bool = Field(False, description="Auto-sync orders with zero warnings to ERP")


class RuleConfigUpdateRequest(BaseModel):
    price_tolerance_percent: float | None = Field(None, ge=0.0, le=100.0, description="Allowed price variance before flagging")
    stock_safety_margin: int | None = Field(None, ge=0, description="Buffer quantity for inventory checks")
    allow_inactive_sku: bool | None = Field(None, description="Allow purchasing deactivated items")
    auto_approve_ready: bool | None = Field(None, description="Auto-sync orders with zero warnings to ERP")



# ---------------------------------------------------------
# Extraction Confirmation Schemas (Issue #16)
# ---------------------------------------------------------
class ConfirmExtractionItem(BaseModel):
    sku: str = Field(..., description="Confirmed or corrected SKU code", example="LAPTOP-A14")
    quantity: int = Field(..., description="Confirmed item quantity", example=2)
    unit_price: Decimal = Field(..., description="Confirmed unit price", example=Decimal("18500000"))


class ConfirmExtractionRequest(BaseModel):
    po_number: str | None = Field(None, description="Optional edited PO number", example="PO-2026-1001")
    customer: str | None = Field(None, description="Optional edited customer name", example="Acme Corp")
    items: list[ConfirmExtractionItem] = Field(..., description="Confirmed line items table")
    currency: str = Field("VND", description="Order currency", example="VND")

