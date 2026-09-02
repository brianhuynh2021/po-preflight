from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from preflight.api.deps import get_audit_store
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import AuditStore

router = APIRouter(prefix="/api/v1/audit", tags=["Cryptographic Audit Trail"])


class AuditEventResponse(BaseModel):
    id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event: DECISION, AUDIT_BLOCK, or INGESTION")
    timestamp: str = Field(..., description="ISO 8601 event timestamp")
    po_number: str = Field(..., description="Associated Purchase Order identifier")
    action: str = Field(..., description="Action performed (e.g. APPROVED, REJECTED, CATALOG_IMPORTED, OUTBOX_DELIVERED)")
    actor: str = Field(..., description="Actor username or system component")
    detail: str = Field("", description="Event details or justification note")
    hash: str | None = Field(None, description="Cryptographic SHA-256 block hash if applicable")


@router.get(
    "/events",
    response_model=list[AuditEventResponse],
    summary="List Unified Audit Events",
    description="Retrieve unified chronological audit log combining decisions and cryptographic audit blocks with filtering.",
)
def list_audit_events(
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    po_number: str | None = Query(None, description="Filter by PO number"),
    actor: str | None = Query(None, description="Filter by actor name"),
    action: str | None = Query(None, description="Filter by action code"),
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
    store: AuditStore = Depends(get_audit_store),
) -> list[AuditEventResponse]:
    events = store.list_audit_events(
        limit=limit,
        offset=offset,
        po_number=po_number,
        actor=actor,
        action=action,
    )
    return [
        AuditEventResponse(
            id=str(e["id"]),
            event_type=e.get("event_type", "AUDIT_BLOCK"),
            timestamp=str(e["timestamp"]),
            po_number=str(e["po_number"]),
            action=str(e["action"]),
            actor=str(e["actor"]),
            detail=str(e.get("detail", "")),
            hash=e.get("hash"),
        )
        for e in events
    ]


@router.get(
    "/blocks/{po_number}",
    summary="Get Cryptographic Chain for Order",
    description="Retrieve all SHA-256 tamper-evident blockchain blocks recorded for a specific purchase order.",
)
def get_order_audit_blocks(
    po_number: str,
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
    store: AuditStore = Depends(get_audit_store),
) -> list[dict[str, Any]]:
    return store.get_audit_blocks(po_number)
