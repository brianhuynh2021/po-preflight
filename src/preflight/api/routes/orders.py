from __future__ import annotations

import json
import shutil
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse

from preflight.api.deps import get_audit_store, get_catalog
from preflight.api.logging_config import logger
from preflight.api.schemas import (
    ConfirmExtractionRequest,
    DecisionRequest,
    DecisionResponse,
    FindingResponse,
    LineItemResponse,
    OrderDetailResponse,
    OrderSummaryResponse,
)
from preflight.models import Analysis, LineItem, Order, Product
from preflight.parsers import parse_order
from preflight.rules import analyze_order
from preflight.store import AuditStore

router = APIRouter(prefix="/api/v1/orders", tags=["Purchase Orders & Preflight Operations"])


def _calculate_risk(status: str, error_count: int, warning_count: int) -> str:
    if status == "extraction_review":
        return "LOW"
    if status == "blocked" or error_count > 0:
        return "HIGH"
    if status in {"review_required", "needs_changes"} or warning_count > 0:
        return "MEDIUM"
    return "LOW"


@router.get(
    "",
    response_model=list[OrderSummaryResponse],
    summary="List Purchase Orders Queue",
    description="Retrieve all ingested POs with filter by status, search keyword, and pagination.",
)
def list_orders(
    status: str | None = Query(None, description="Filter by status (ready_for_approval, review_required, blocked, approved)"),
    search: str | None = Query(None, description="Search by PO Number or Customer Name"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    store: AuditStore = Depends(get_audit_store),
) -> list[OrderSummaryResponse]:
    rows = store.list_orders(status=status, search=search, limit=limit, offset=offset)
    results = []

    for row in rows:
        order_data = json.loads(row["order_json"]) if row.get("order_json") else {}
        findings_data = json.loads(row["findings_json"]) if row.get("findings_json") else []

        error_count = sum(1 for f in findings_data if f.get("severity") == "error")
        warning_count = sum(1 for f in findings_data if f.get("severity") == "warning")
        risk_level = _calculate_risk(row["status"], error_count, warning_count)

        # If latest_decision is present, reflect it in the summary status
        display_status = row.get("latest_decision") or row["status"]

        results.append(
            OrderSummaryResponse(
                id=row["id"],
                po_number=row["po_number"],
                customer=row["customer"],
                status=display_status,
                risk_level=risk_level,
                total=Decimal(row["total"]),
                currency=order_data.get("currency", "VND"),
                items_count=len(order_data.get("items", [])),
                findings_count=len(findings_data),
                error_count=error_count,
                warning_count=warning_count,
                source_file=row["source_file"],
                created_at=row["created_at"],
                latest_decision=row.get("latest_decision"),
                decided_at=row.get("decided_at"),
            )
        )
    return results


@router.get(
    "/{order_id}",
    response_model=OrderDetailResponse,
    summary="Get Order Preflight Details & Evidence",
    description="Retrieve deep line-item comparisons, visual evidence, catalog price diffs, and audit timeline.",
)
def get_order_detail(
    order_id: str,
    store: AuditStore = Depends(get_audit_store),
    catalog: dict[str, Product] = Depends(get_catalog),
) -> OrderDetailResponse:
    row = store.get_order(order_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found in preflight store.")

    order_data = json.loads(row["order_json"]) if row.get("order_json") else {}
    findings_data = json.loads(row["findings_json"]) if row.get("findings_json") else []

    error_count = sum(1 for f in findings_data if f.get("severity") == "error")
    warning_count = sum(1 for f in findings_data if f.get("severity") == "warning")
    risk_level = _calculate_risk(row["status"], error_count, warning_count)

    # Build line items with catalog comparison
    items: list[LineItemResponse] = []
    for idx, item in enumerate(order_data.get("items", []), start=1):
        sku = item["sku"]
        qty = item["quantity"]
        ordered_price = Decimal(str(item["unit_price"]))

        product = catalog.get(sku)
        cat_price = product.unit_price if product else None
        stock = product.stock if product else None

        price_diff = None
        if cat_price and cat_price > 0:
            price_diff = float(((ordered_price - cat_price) / cat_price) * 100)

        stock_status = None
        if stock is not None:
            if stock >= qty:
                stock_status = "IN_STOCK"
            elif stock > 0:
                stock_status = "LOW_STOCK"
            else:
                stock_status = "OUT_OF_STOCK"

        line_status = "MATCHED"
        if not product:
            line_status = "UNKNOWN"
        elif price_diff and abs(price_diff) > 0.01:
            line_status = "MISMATCH"

        items.append(
            LineItemResponse(
                line_number=idx,
                sku=sku,
                name=product.name if product else f"Raw: {sku}",
                quantity=qty,
                unit_price=ordered_price,
                catalog_unit_price=cat_price,
                price_diff_percent=price_diff,
                stock_available=stock,
                stock_status=stock_status,
                status=line_status,
            )
        )

    # Build findings list
    findings: list[FindingResponse] = [
        FindingResponse(
            code=f["code"],
            severity=f["severity"],
            message=f["message"],
            sku=f.get("sku"),
            evidence=f"Grounding rule: {f['code']} against Catalog v2026.08",
        )
        for f in findings_data
    ]

    return OrderDetailResponse(
        id=row["id"],
        po_number=row["po_number"],
        customer=row["customer"],
        status=row.get("latest_decision") or row["status"],
        risk_level=risk_level,
        total=Decimal(row["total"]),
        currency=order_data.get("currency", "VND"),
        source_file=row["source_file"],
        created_at=row["created_at"],
        items=items,
        findings=findings,
        decisions=row.get("decisions", []),
    )


@router.post(
    "/upload",
    response_model=OrderDetailResponse,
    status_code=201,
    summary="Upload & Preflight PO Document",
    description="Upload a PO file (PDF, JSON, CSV, or TXT), parse items, optionally stage in extraction_review, or run deterministic rules.",
)
async def upload_order(
    file: UploadFile = File(..., description="Purchase order document file"),
    staged_review: bool = Query(False, description="Stage order in extraction_review state before running preflight rules"),
    store: AuditStore = Depends(get_audit_store),
    catalog: dict[str, Product] = Depends(get_catalog),
) -> OrderDetailResponse:
    upload_dir = Path("runtime/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / (file.filename or "uploaded_order.tmp")

    try:
        content = await file.read()
        temp_path.write_bytes(content)

        # Parse order
        order = parse_order(temp_path)
        duplicate = store.has_po(order.po_number)

        if staged_review:
            # Stage in extraction_review state without rules evaluation
            analysis = Analysis(order=order, findings=[], status="extraction_review")
        else:
            # Run preflight rules immediately
            analysis = analyze_order(order, catalog, duplicate=duplicate)

        # Persist to database
        analysis_id = store.record_analysis(analysis, str(file.filename))

        # Return full detail
        return get_order_detail(str(analysis_id), store=store, catalog=catalog)
    except Exception as exc:
        logger.error(f"Failed to process PO file: {exc}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Failed to process PO file: {exc}")


@router.post(
    "/{order_id}/confirm-extraction",
    response_model=OrderDetailResponse,
    summary="Confirm or Edit Extracted PO Data and Run Preflight Rules",
    description="Submit reviewed/corrected line items from the extraction review step. Evaluates preflight rules and transitions to ready_for_approval/review_required/blocked.",
)
def confirm_extraction(
    order_id: str,
    payload: ConfirmExtractionRequest,
    store: AuditStore = Depends(get_audit_store),
    catalog: dict[str, Product] = Depends(get_catalog),
) -> OrderDetailResponse:
    row = store.get_order(order_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found.")

    po_number = payload.po_number or row["po_number"]
    customer = payload.customer or row["customer"]

    items = tuple(
        LineItem(
            sku=it.sku.strip().upper(),
            quantity=it.quantity,
            unit_price=it.unit_price,
        )
        for it in payload.items
    )
    if not items:
        raise HTTPException(status_code=400, detail="Order must have at least one line item.")

    updated_order = Order(
        po_number=po_number,
        customer=customer,
        items=items,
        currency=payload.currency,
    )

    # Run deterministic preflight rules on confirmed order
    analysis = analyze_order(updated_order, catalog, duplicate=False)

    # Update database record
    store.update_analysis(int(row["id"]), analysis)

    return get_order_detail(str(row["id"]), store=store, catalog=catalog)


@router.post(
    "/{order_id}/decide",
    response_model=DecisionResponse,
    summary="Record Human Approval Decision",
    description="Authorize or reject a Purchase Order. Triggers audit record creation with actor and timestamp.",
)
def record_decision(
    order_id: str,
    payload: DecisionRequest,
    store: AuditStore = Depends(get_audit_store),
) -> DecisionResponse:
    row = store.get_order(order_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found.")

    po_number = row["po_number"]
    try:
        decision_id = store.record_decision(
            po_number=po_number,
            decision=payload.decision,
            actor=payload.actor,
            note=payload.note,
        )
        history = store.history(po_number)
        latest = history["decisions"][-1]
        return DecisionResponse(
            success=True,
            id=decision_id,
            po_number=po_number,
            decision=latest["decision"],
            actor=latest["actor"],
            note=latest["note"],
            created_at=latest["created_at"],
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
