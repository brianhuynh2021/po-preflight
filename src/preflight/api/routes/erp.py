from __future__ import annotations

import os
from decimal import Decimal
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from preflight.api.deps import get_audit_store, get_db_path
from preflight.api.events import event_bus
from preflight.erp.outbox import BaseOutboxStore, OutboxStore, compute_idempotency_key, create_outbox_store
from preflight.erp.payload import build_erp_payload
from preflight.erp.registry import get_adapter
from preflight.erp.schemas import ERPAdapterType, ERPSyncResponse, OutboxStats
from preflight.erp.worker import OutboxSyncWorker
from preflight.observability.metrics import metrics_registry
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import AuditStore, BaseAuditStore

router = APIRouter(prefix="/api/v1/erp", tags=["ERP Integration & Outbox Worker"])


def get_outbox_store(db_path: str = Depends(get_db_path)) -> BaseOutboxStore:
    return create_outbox_store(db_path)


@router.post(
    "/sync/{order_id}",
    summary="Synchronize Approved Purchase Order to ERP",
    description="Enqueues an approved order into the Transactional Outbox and dispatches it to the ERP adapter.",
    response_model=ERPSyncResponse,
)
def sync_order_to_erp(
    order_id: int,
    adapter_type: ERPAdapterType | None = Query(None, description="ERP target system override (Admin only)"),
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: AuditStore = Depends(get_audit_store),
    outbox: BaseOutboxStore = Depends(get_outbox_store),
) -> ERPSyncResponse:

    order = store.get_order(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found.")

    # Governance check: only approved orders can be synced
    decisions = order.get("decisions", [])
    latest_decision = decisions[-1].get("decision") if decisions else None
    is_approved = (order.get("status") == "approved") or (latest_decision == "approved")

    if not is_approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order has not been approved yet. Only approved orders can be synchronized to ERP.",
        )

    # Adapter selection & RBAC check on override
    default_adapter_name = os.getenv("ERP_DEFAULT_ADAPTER", "MOCK_SAP")
    if adapter_type is not None and adapter_type.value != default_adapter_name:
        if user.role < Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can override the default ERP adapter.",
            )

    selected_adapter_name = adapter_type.value if adapter_type else default_adapter_name
    adapter = get_adapter(selected_adapter_name)
    resolved_adapter_type = getattr(adapter, "adapter_type", None)
    if not resolved_adapter_type:
        try:
            resolved_adapter_type = ERPAdapterType(selected_adapter_name)
        except Exception:
            resolved_adapter_type = ERPAdapterType.MOCK_SAP

    # Build validated ERPOrderDraft
    try:
        draft = build_erp_payload(order, source_analysis_id=order_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    idemp_key = compute_idempotency_key(order_id, draft.po_number, draft.items)

    # Check if this exact order revision has already been successfully synced in the outbox
    existing = outbox.get_by_idempotency_key(idemp_key)
    if existing and existing.get("status") == "SENT":
        existing_adapter_str = existing.get("adapter_type") or resolved_adapter_type.value
        try:
            ex_adapter_type = ERPAdapterType(existing_adapter_str)
        except Exception:
            ex_adapter_type = resolved_adapter_type

        mode_val = "live" if "LIVE" in ex_adapter_type.value else "mock"
        return ERPSyncResponse(
            success=True,
            transaction_id=existing.get("transaction_id"),
            adapter_type=ex_adapter_type,
            idempotency_key=idemp_key,
            mode=mode_val,
            error_message=None,
        )

    # Enqueue event into Transactional Outbox
    items_dicts = [it.to_dict() for it in draft.items]
    event_payload = outbox.enqueue_order(
        po_number=draft.po_number,
        customer=draft.customer,
        items=items_dicts,
        total_amount=draft.subtotal,
        currency=draft.currency,
        idempotency_key=idemp_key,
        approved_by=draft.approved_by,
        approved_at=draft.approved_at,
        source_analysis_id=order_id,
    )

    worker = OutboxSyncWorker(outbox_store=outbox, adapter=adapter, metrics_registry=metrics_registry)

    # Execute sync
    results = worker.process_batch(limit=5)
    matching = next((r for r in results if r.idempotency_key == event_payload.idempotency_key), None)

    if matching:
        if matching.success:
            event_bus.publish(
                "erp.synced",
                {
                    "order_id": order_id,
                    "po_number": draft.po_number,
                    "transaction_id": matching.transaction_id,
                    "adapter": resolved_adapter_type.value,
                },
            )
        return matching

    # Fallback to current state in DB if not directly in batch results
    ev = outbox.get_by_idempotency_key(idemp_key)
    is_sent = bool(ev and ev.get("status") == "SENT")
    mode_val = "live" if "LIVE" in resolved_adapter_type.value else "mock"
    return ERPSyncResponse(
        success=is_sent,
        transaction_id=ev.get("transaction_id") if ev else None,
        adapter_type=resolved_adapter_type,
        idempotency_key=idemp_key,
        mode=mode_val,
        error_message=ev.get("last_error") if ev else "Event queued in outbox",
    )


@router.post(
    "/outbox/process",
    summary="Trigger Outbox Sync Worker Batch Run",
    description="Processes all pending events in the transactional outbox queue and delivers them to ERP.",
)
def process_outbox_queue(
    limit: int = Query(10, ge=1, le=50, description="Max batch size"),
    adapter_type: ERPAdapterType | None = Query(None, description="ERP target adapter override"),
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    outbox: BaseOutboxStore = Depends(get_outbox_store),
) -> dict[str, Any]:

    adapter = get_adapter(adapter_type)
    worker = OutboxSyncWorker(outbox_store=outbox, adapter=adapter, metrics_registry=metrics_registry)

    responses = worker.process_batch(limit=limit)
    stats = outbox.get_stats()

    return {
        "processed_count": len(responses),
        "adapter_used": getattr(adapter, "adapter_type", ERPAdapterType.MOCK_SAP).value if hasattr(adapter, "adapter_type") else "MOCK_SAP",
        "responses": [r.model_dump() for r in responses],
        "outbox_stats": stats.model_dump(),
    }


@router.get(
    "/outbox/status",
    summary="Get Transactional Outbox Statistics & Queue History",
    description="Inspect pending, processing, sent, failed, and dead-letter ERP sync events.",
)
def get_outbox_status(
    limit: int = Query(20, ge=1, le=100),
    outbox: BaseOutboxStore = Depends(get_outbox_store),
) -> dict[str, Any]:
    stats = outbox.get_stats()
    events = outbox.list_events(limit=limit)

    return {
        "stats": stats.model_dump(),
        "events": events,
    }
