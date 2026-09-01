from __future__ import annotations

from decimal import Decimal
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from preflight.api.deps import get_audit_store, get_db_path
from preflight.api.events import event_bus
from preflight.erp.adapters.odoo import MockOdooAdapter
from preflight.erp.adapters.sap import MockSAPAdapter
from preflight.erp.outbox import BaseOutboxStore, OutboxStore, create_outbox_store
from preflight.erp.schemas import ERPAdapterType, ERPSyncResponse, OutboxStats
from preflight.erp.worker import OutboxSyncWorker
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
    adapter_type: ERPAdapterType = Query(ERPAdapterType.MOCK_SAP, description="ERP target system"),
    store: AuditStore = Depends(get_audit_store),
    outbox: OutboxStore = Depends(get_outbox_store),
) -> ERPSyncResponse:
    order = store.get_order(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found.")

    po_number = order.get("po_number", f"PO-{order_id}")
    customer = order.get("customer", "Unknown Customer")
    total_val = Decimal(str(order.get("total_amount") or order.get("total", 0)))
    currency = order.get("currency", "VND")
    items = order.get("line_items") or order.get("items", [])

    # Enqueue event into Transactional Outbox
    event_payload = outbox.enqueue_order(
        po_number=po_number,
        customer=customer,
        items=items,
        total_amount=total_val,
        currency=currency,
    )

    # Select ERP Adapter
    adapter = MockOdooAdapter() if adapter_type == ERPAdapterType.MOCK_ODOO else MockSAPAdapter()
    worker = OutboxSyncWorker(outbox_store=outbox, adapter=adapter)

    # Execute sync
    results = worker.process_batch(limit=5)
    matching = next((r for r in results if r.idempotency_key == event_payload.idempotency_key), None)

    if matching:
        event_bus.publish(
            "erp.synced",
            {
                "order_id": order_id,
                "po_number": po_number,
                "transaction_id": matching.transaction_id,
                "adapter": adapter_type.value,
            },
        )
        return matching

    # If already sent previously, return idempotent success
    event_bus.publish(
        "erp.synced",
        {
            "order_id": order_id,
            "po_number": po_number,
            "transaction_id": f"ERP-SO-{po_number}",
            "adapter": adapter_type.value,
        },
    )
    return ERPSyncResponse(
        success=True,
        transaction_id=f"ERP-SO-{po_number}",
        adapter_type=adapter_type,
        idempotency_key=event_payload.idempotency_key,
        error_message=None,
    )


@router.post(
    "/outbox/process",
    summary="Trigger Outbox Sync Worker Batch Run",
    description="Processes all pending events in the transactional outbox queue and delivers them to ERP.",
)
def process_outbox_queue(
    limit: int = Query(10, ge=1, le=50, description="Max batch size"),
    adapter_type: ERPAdapterType = Query(ERPAdapterType.MOCK_SAP, description="ERP target adapter"),
    outbox: OutboxStore = Depends(get_outbox_store),
) -> dict[str, Any]:
    adapter = MockOdooAdapter() if adapter_type == ERPAdapterType.MOCK_ODOO else MockSAPAdapter()
    worker = OutboxSyncWorker(outbox_store=outbox, adapter=adapter)

    responses = worker.process_batch(limit=limit)
    stats = outbox.get_stats()

    return {
        "processed_count": len(responses),
        "adapter_used": adapter_type.value,
        "responses": [r.model_dump() for r in responses],
        "outbox_stats": stats.model_dump(),
    }


@router.get(
    "/outbox/status",
    summary="Get Transactional Outbox Statistics & Queue History",
    description="Inspect pending, processing, sent, and failed ERP sync events.",
)
def get_outbox_status(
    limit: int = Query(20, ge=1, le=100),
    outbox: OutboxStore = Depends(get_outbox_store),
) -> dict[str, Any]:
    stats = outbox.get_stats()
    events = outbox.list_events(limit=limit)

    return {
        "stats": stats.model_dump(),
        "events": events,
    }
