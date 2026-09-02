from __future__ import annotations

import json
import shutil
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query, UploadFile, File, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from preflight.api.deps import get_audit_store, get_catalog
from preflight.api.errors import (
    DecisionConflict,
    Forbidden,
    NotFound,
    ParseError,
    PayloadTooLarge,
    Unauthorized,
    UnsupportedFormat,
    ValidationFailed,
)
from preflight.api.events import event_bus
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
from preflight.rules import DecisionValidationError, analyze_order, validate_order_decision
from preflight.rules_context import build_rule_context
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.services.decisions import DecisionError, Principal, decide_order
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
        raise NotFound(f"Không tìm thấy đơn hàng {order_id} trong hệ thống.")

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
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
    store: AuditStore = Depends(get_audit_store),
    catalog: dict[str, Product] = Depends(get_catalog),
) -> OrderDetailResponse:

    filename = file.filename or "uploaded_order.tmp"
    suffix = Path(filename).suffix.lower()
    ALLOWED_EXTENSIONS = {".json", ".pdf", ".png", ".jpg", ".jpeg", ".txt", ".csv"}
    if suffix not in ALLOWED_EXTENSIONS:
        raise UnsupportedFormat(
            f"Định dạng tệp '{suffix}' không được hỗ trợ. Vui lòng tải lên tệp PDF, JSON, PNG, JPG hoặc TXT."
        )

    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB Limit

    upload_dir = Path("runtime/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_name = f"tmp_{uuid.uuid4().hex}_{Path(filename).name}"
    temp_path = upload_dir / temp_name

    try:
        content = bytearray()
        chunk_size = 64 * 1024
        while chunk := await file.read(chunk_size):
            content.extend(chunk)
            if len(content) > MAX_UPLOAD_SIZE:
                raise PayloadTooLarge(
                    f"Kích thước tệp vượt quá giới hạn 10MB cho phép (kích thước hiện tại: {len(content) / (1024*1024):.1f}MB)."
                )
        temp_path.write_bytes(content)

        # Parse order in dedicated guarded try-block
        try:
            order = parse_order(temp_path)
        except Exception as exc:
            logger.warning(f"Failed to parse PO document '{filename}': {exc}")
            raise ParseError(
                "Không thể đọc hoặc phân tích nội dung tệp PO. Vui lòng kiểm tra định dạng dữ liệu."
            ) from None

        duplicate = store.has_po(order.po_number)

        if staged_review:
            # Stage in extraction_review state without rules evaluation
            analysis = Analysis(order=order, findings=[], status="extraction_review")
        else:
            # Run preflight rules immediately with comprehensive RuleContext
            ctx = build_rule_context(store, catalog, order, duplicate=duplicate)
            analysis = analyze_order(order, ctx)

        # Persist to database
        analysis_id = store.record_analysis(analysis, str(filename))

        # Store permanent file in structured hierarchy <analysis_id>/<safe_name>
        final_dir = upload_dir / str(analysis_id)
        final_dir.mkdir(parents=True, exist_ok=True)
        final_path = final_dir / Path(filename).name
        shutil.move(str(temp_path), str(final_path))

        # Broadcast SSE Real-Time Event
        event_bus.publish(
            "order.created",
            {
                "id": str(analysis_id),
                "po_number": order.po_number,
                "customer": order.customer,
                "status": analysis.status,
                "total_amount": float(order.total) if order.total else 0.0,
                "currency": order.currency,
            },
        )

        # Return full detail
        return get_order_detail(str(analysis_id), store=store, catalog=catalog)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


@router.post(
    "/{order_id}/confirm-extraction",
    response_model=OrderDetailResponse,
    summary="Confirm or Edit Extracted PO Data and Run Preflight Rules",
    description="Submit reviewed/corrected line items from the extraction review step. Evaluates preflight rules and transitions to ready_for_approval/review_required/blocked.",
)
def confirm_extraction(
    order_id: str,
    payload: ConfirmExtractionRequest,
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: AuditStore = Depends(get_audit_store),
    catalog: dict[str, Product] = Depends(get_catalog),
) -> OrderDetailResponse:
    row = store.get_order(order_id)
    if not row:
        raise NotFound(f"Không tìm thấy đơn hàng {order_id}.")

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
        raise ValidationFailed("Đơn hàng phải có ít nhất một dòng sản phẩm.")

    updated_order = Order(
        po_number=po_number,
        customer=customer,
        items=items,
        currency=payload.currency,
    )

    # Run deterministic preflight rules on confirmed order with RuleContext
    ctx = build_rule_context(store, catalog, updated_order, duplicate=False)
    analysis = analyze_order(updated_order, ctx)

    # Active Learning Feedback Loop: Persist customer nickname/alias mappings when human corrects SKUs
    try:
        orig_order_json = json.loads(row.get("order_json", "{}"))
        orig_items = orig_order_json.get("items", [])
        for idx, confirmed_item in enumerate(payload.items):
            canonical_sku = confirmed_item.sku.strip().upper()
            if idx < len(orig_items):
                raw_orig = str(orig_items[idx].get("sku", "")).strip()
                if raw_orig and raw_orig.upper() != canonical_sku:
                    store.learn_alias(customer_id=customer, raw_query=raw_orig, target_sku=canonical_sku)
    except Exception as exc:
        logger.warning(f"Failed to learn customer alias during extraction confirmation: {exc}")

    # Update database record
    store.update_analysis(int(row["id"]), analysis)

    event_bus.publish(
        "order.confirmed",
        {"id": str(row["id"]), "po_number": po_number, "status": analysis.status},
    )

    return get_order_detail(str(row["id"]), store=store, catalog=catalog)


@router.post(
    "/{order_id}/decide",
    response_model=DecisionResponse,
    summary="Record Human Approval Decision",
    description="Authorize or reject a Purchase Order via unified DecisionService. Audits authenticated actor and channel.",
)
def record_decision(
    order_id: str,
    payload: DecisionRequest,
    request: Request,
    response: Response,
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: AuditStore = Depends(get_audit_store),
) -> DecisionResponse:
    if payload.actor is not None:
        response.headers["X-Deprecated-Field"] = "actor"

    channel = "web" if request.headers.get("X-Client") == "web" else "api"
    principal = Principal(
        user_id=user.username,
        display_name=user.username,
        role=user.role,
        channel=channel,
    )

    try:
        result = decide_order(
            store=store,
            order_ref=order_id,
            decision=payload.decision,
            note=payload.note,
            principal=principal,
            event_bus=event_bus,
        )
        return DecisionResponse(
            success=True,
            id=result.decision_id,
            po_number=result.po_number,
            decision=result.decision,
            actor=result.actor,
            note=result.note,
            created_at=result.created_at,
        )
    except DecisionError as err:
        if err.status_code == 404:
            raise NotFound(err.message)
        elif err.status_code == 403:
            raise Forbidden(err.message)
        elif err.status_code == 409:
            raise DecisionConflict(err.message)
        elif err.status_code == 422:
            raise ValidationFailed(err.message)
        else:
            raise DecisionConflict(err.message)


@router.get(
    "/{order_id}/audit-certificate",
    summary="Cryptographic Compliance Audit Certificate",
    description="Generate a tamper-evident SHA-256 Merkle-style audit certificate verifying complete event history integrity for SOX 404 & SOC2 Type II compliance.",
)
def get_audit_certificate(
    order_id: str,
    store: AuditStore = Depends(get_audit_store),
) -> dict[str, Any]:
    row = store.get_order(order_id)
    if not row:
        raise NotFound(f"Không tìm thấy đơn hàng {order_id}.")

    po_number = row["po_number"]
    decisions = row.get("decisions", [])

    from preflight.security.audit_chain import AuditHashChain

    stored_blocks = store.get_audit_blocks(po_number)

    return AuditHashChain.generate_compliance_certificate(
        po_number=po_number,
        order_data=row,
        decisions=decisions,
        stored_blocks=stored_blocks if stored_blocks else None,
    )


@router.get(
    "/events/stream",
    summary="Order Real-Time Event Stream",
    description="Subscribe to real-time Server-Sent Events for order lifecycle transitions.",
)
async def orders_events_stream() -> StreamingResponse:
    return StreamingResponse(
        event_bus.event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
