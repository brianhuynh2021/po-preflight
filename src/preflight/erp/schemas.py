from __future__ import annotations

import time
from decimal import Decimal
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


class ERPEventStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


class ERPAdapterType(str, Enum):
    MOCK_SAP = "MOCK_SAP"
    MOCK_ODOO = "MOCK_ODOO"
    ODOO_LIVE = "ODOO_LIVE"
    SAP_ODATA_LIVE = "SAP_ODATA_LIVE"
    SAP_LIVE = "SAP_LIVE"
    MISA_AMIS_LIVE = "MISA_AMIS_LIVE"
    MISA_LIVE = "MISA_LIVE"


class ERPSyncPayload(BaseModel):
    event_id: str = Field(..., description="Unique outbox event identifier")
    po_number: str = Field(..., description="Purchase Order number")
    customer: str = Field(..., description="Customer enterprise name")
    items: list[dict[str, Any]] = Field(default_factory=list, description="Line items")
    total_amount: Decimal = Field(..., description="Total monetary order value")
    currency: str = Field("VND", description="Order currency")
    idempotency_key: str = Field(..., description="SHA256 Idempotency key preventing double-booking")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp")
    approved_by: str | None = Field(None, description="Principal actor who approved the order")
    approved_at: str | None = Field(None, description="Timestamp of human approval")
    source_analysis_id: int | None = Field(None, description="Preflight order analysis ID")


class ERPSyncResponse(BaseModel):
    success: bool = Field(..., description="Whether ERP synchronization succeeded")
    transaction_id: str | None = Field(None, description="ERP Sales Order ID (e.g. SAP-SO-10427, SO/2026/001)")
    adapter_type: ERPAdapterType = Field(..., description="ERP backend adapter utilized")
    idempotency_key: str = Field(..., description="Echoed idempotency key")
    mode: Literal["live", "dry_run", "mock"] = Field("mock", description="Adapter execution mode")
    timestamp: float = Field(default_factory=time.time, description="Synchronization completion time")
    error_message: str | None = Field(None, description="Failure reason if sync failed")


class OutboxStats(BaseModel):
    pending_count: int = Field(0, description="Events waiting in queue")
    processing_count: int = Field(0, description="Events currently in flight")
    sent_count: int = Field(0, description="Successfully delivered orders")
    failed_count: int = Field(0, description="Permanently failed events")
    dead_letter_count: int = Field(0, description="Events placed in dead-letter queue after 3 retries")
    total_events: int = Field(0, description="Total outbox events recorded")
