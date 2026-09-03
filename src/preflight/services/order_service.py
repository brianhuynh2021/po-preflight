from __future__ import annotations

import json
import logging
import os
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

from preflight.api.events import event_bus
from preflight.catalog import get_catalog
from preflight.ingestion.detector import detect_document_type
from preflight.ingestion.pipeline import IntelligentIngestionPipeline
from preflight.ingestion.schemas import DocumentType
from preflight.jobs.queue import sync_enqueue_job
from preflight.models import Analysis, Order, Product
from preflight.rules import analyze_order as evaluate_order_rules
from preflight.rules_context import build_rule_context
from preflight.services.customer_resolver import resolve_customer
from preflight.store import BaseAuditStore

logger = logging.getLogger("PreflightOrderService")


def is_ocr_needed(file_bytes: bytes, filename: str) -> bool:
    """Determine if a document requires AI Vision / OCR extraction."""
    doc_type = detect_document_type(file_bytes, filename)
    return doc_type in (DocumentType.SCANNED_PDF, DocumentType.IMAGE_RASTER)


def create_received_order_for_ocr(
    file_bytes: bytes,
    filename: str,
    store: BaseAuditStore,
    user_name: str = "system",
) -> dict[str, Any]:
    """Create an order with status 'received', save raw file, and enqueue background OCR extraction."""
    upload_dir = Path("runtime/uploads/pending")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_filename = f"ocr_{uuid.uuid4().hex}_{Path(filename).name}"
    temp_path = upload_dir / temp_filename
    temp_path.write_bytes(file_bytes)

    # Temporary PO number to track in queue and SSE stream
    po_stub = f"PO-OCR-{uuid.uuid4().hex[:6].upper()}"
    source_file = f"upload://{filename}"

    order_id = store.record_received_order(
        po_number=po_stub,
        customer="Đang bóc tách...",
        source_file=source_file,
        metadata={
            "original_filename": filename,
            "temp_path": str(temp_path),
            "uploaded_by": user_name,
            "ocr_pending": True,
        },
    )

    # Publish real-time SSE notification
    event_bus.publish("order.received", {
        "order_id": order_id,
        "po_number": po_stub,
        "status": "received",
        "message": "Đang bóc tách dữ liệu bằng AI OCR trong nền...",
    })

    # Enqueue background arq/in-memory job
    sync_enqueue_job("run_ocr", order_id=order_id, file_path=str(temp_path), filename=filename)

    logger.info("Enqueued async OCR for order_id=%s, PO='%s', file='%s'", order_id, po_stub, filename)

    return {
        "status": "received",
        "order_id": order_id,
        "po_number": po_stub,
        "message": "Đang bóc tách dữ liệu bằng AI OCR trong nền...",
        "sse_channel": "/api/v1/events/stream",
    }


def process_order_sync(
    file_bytes: bytes,
    filename: str,
    store: BaseAuditStore,
    catalog: dict[str, Product] | None = None,
    user_name: str = "system",
    on_conflict: str = "reject",
) -> tuple[Analysis, int]:
    """Unified synchronous extraction, validation, and persistence for deterministic documents."""
    cat = catalog or get_catalog()
    pipeline = IntelligentIngestionPipeline()
    extracted_order, domain_order = pipeline.process_file_bytes(file_bytes, filename)

    domain_order.created_by = user_name
    domain_order.last_modified_by = user_name

    # Customer resolution
    resolved_cust, cust_finding = resolve_customer(domain_order.customer, store=store)
    effective_customer = resolved_cust.name if resolved_cust else domain_order.customer
    domain_order.customer = effective_customer

    # Check existing PO
    existing = store.get_order_by_po(domain_order.po_number, customer=effective_customer)
    duplicate = False
    revision = 1
    supersedes_order_id = None

    if existing:
        old_status = existing.get("status")
        old_decision = existing.get("latest_decision")

        if old_decision == "approved" or old_status in ("approved", "exported"):
            duplicate = True
        elif old_decision in ("rejected", "needs_changes") or old_status in ("rejected", "needs_changes"):
            duplicate = False
            revision = int(existing.get("revision", 1)) + 1
            supersedes_order_id = int(existing["id"])
            store.mark_superseded(int(existing["id"]))
        else:
            if on_conflict.lower().strip() == "revise":
                duplicate = False
                revision = int(existing.get("revision", 1)) + 1
                supersedes_order_id = int(existing["id"])
                store.mark_superseded(int(existing["id"]))
            else:
                from preflight.api.errors import DuplicatePendingError
                raise DuplicatePendingError(
                    existing_order_id=existing["id"],
                    po_number=domain_order.po_number,
                )

    rule_ctx = build_rule_context(store, cat, domain_order, duplicate=duplicate)
    analysis = evaluate_order_rules(domain_order, rule_ctx)
    if cust_finding:
        analysis.findings.append(cust_finding)

    analysis.revision = revision
    analysis.supersedes_order_id = supersedes_order_id

    source_path = f"upload://{filename}"
    order_id = store.record_analysis(analysis, source_path)
    analysis.analysis_id = order_id

    # Broadcast event
    event_bus.publish("order.analyzed", {
        "order_id": order_id,
        "po_number": domain_order.po_number,
        "status": analysis.status,
    })

    return analysis, order_id
