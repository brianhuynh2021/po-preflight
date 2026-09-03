from __future__ import annotations

import functools
import json
import logging
import os
import traceback
from pathlib import Path
from typing import Any, Callable, Coroutine

from preflight.api.events import event_bus
from preflight.catalog import get_catalog
from preflight.erp.registry import get_adapter
from preflight.erp.outbox import create_outbox_store
from preflight.erp.worker import OutboxSyncWorker
from preflight.ingestion.pipeline import IntelligentIngestionPipeline
from preflight.jobs.queue import register_job
from preflight.models import Order
from preflight.rules import analyze_order as evaluate_order_rules
from preflight.rules_context import build_rule_context
from preflight.services.customer_resolver import resolve_customer
from preflight.store import BaseAuditStore, create_audit_store

logger = logging.getLogger("PreflightJobs")


def with_dead_letter_protection(job_name: str):
    """Decorator catching final retry errors and persisting to request_errors table."""
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @functools.wraps(func)
        async def wrapper(ctx: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
            try:
                return await func(ctx, *args, **kwargs)
            except Exception as exc:
                job_id = ctx.get("job_id", "unknown")
                job_try = ctx.get("job_try", 1)
                max_retries = ctx.get("max_retries", 3)

                logger.warning(
                    "Job '%s' (id=%s, try=%d/%d) failed: %s",
                    job_name, job_id, job_try, max_retries, exc,
                )

                if job_try >= max_retries:
                    tb_str = traceback.format_exc()
                    try:
                        store = ctx.get("store") or create_audit_store()
                        store.record_request_error(
                            request_id=f"job:{job_id}",
                            endpoint=f"arq:job:{job_name}",
                            status_code=500,
                            error_message=f"Dead-letter job '{job_name}' exceeded {max_retries} attempts: {exc}",
                            traceback_str=tb_str,
                        )
                        logger.error("Recorded dead-letter job '%s' (%s) to request_errors", job_name, job_id)
                    except Exception as store_err:
                        logger.error("Failed to write dead-letter error to store: %s", store_err)
                raise exc
        return wrapper
    return decorator


@with_dead_letter_protection("analyze_order")
async def analyze_order(ctx: dict[str, Any], order_id: int | str) -> dict[str, Any]:
    """Background job: Run preflight rule evaluation on an order."""
    store: BaseAuditStore = ctx.get("store") or create_audit_store()
    order_row = store.get_order(str(order_id))
    if not order_row:
        raise ValueError(f"Order {order_id} not found for background analysis")

    catalog = ctx.get("catalog") or get_catalog()
    order_data = json.loads(order_row["order_json"]) if order_row.get("order_json") else {}
    from preflight.models import LineItem
    items = [
        LineItem(
            sku=it.get("sku", ""),
            quantity=int(it.get("quantity", 1)),
            unit_price=it.get("unit_price", 0),
            uom=it.get("uom", "PCS"),
            description=it.get("description", ""),
        )
        for it in order_data.get("items", [])
    ]
    domain_order = Order(
        po_number=order_row["po_number"],
        customer=order_row["customer"],
        items=items,
        currency=order_data.get("currency", "VND"),
        source_file=order_row.get("source_file", ""),
    )

    rule_ctx = build_rule_context(store, catalog, domain_order)
    analysis = evaluate_order_rules(domain_order, rule_ctx)

    store.update_analysis(int(order_id), analysis)

    event_bus.publish("order.analyzed", {
        "order_id": int(order_id),
        "po_number": domain_order.po_number,
        "status": analysis.status,
    })

    return {"status": analysis.status, "order_id": int(order_id), "po_number": domain_order.po_number}


@with_dead_letter_protection("run_ocr")
async def run_ocr(
    ctx: dict[str, Any],
    order_id: int | str,
    file_path: str,
    filename: str,
) -> dict[str, Any]:
    """Background job: Run AI/Vision OCR extraction on raster images or scanned PDFs, then evaluate rules."""
    store: BaseAuditStore = ctx.get("store") or create_audit_store()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file for OCR not found: {file_path}")

    file_bytes = path.read_bytes()
    pipeline = IntelligentIngestionPipeline()
    extracted_order, domain_order = pipeline.process_file_bytes(file_bytes, filename)

    # Resolve customer
    resolved_cust, _ = resolve_customer(domain_order.customer, store=store)
    effective_customer = resolved_cust.name if resolved_cust else domain_order.customer

    domain_order.customer = effective_customer
    catalog = ctx.get("catalog") or get_catalog()

    rule_ctx = build_rule_context(store, catalog, domain_order)
    analysis = evaluate_order_rules(domain_order, rule_ctx)

    store.update_analysis(int(order_id), analysis)

    event_bus.publish("order.analyzed", {
        "order_id": int(order_id),
        "po_number": domain_order.po_number,
        "status": analysis.status,
    })

    logger.info("OCR completed for order %s: PO '%s' -> %s", order_id, domain_order.po_number, analysis.status)
    return {
        "status": analysis.status,
        "order_id": int(order_id),
        "po_number": domain_order.po_number,
        "findings_count": len(analysis.findings),
    }


@with_dead_letter_protection("outbox_dispatch")
async def outbox_dispatch(ctx: dict[str, Any]) -> dict[str, Any]:
    """Background job (cron 1m): Drain transactional outbox events to ERP, recovering stale leases."""
    outbox_store = ctx.get("outbox_store") or create_outbox_store()
    worker = OutboxSyncWorker(outbox_store=outbox_store)
    responses = worker.process_batch(limit=20, lease_seconds=60.0)
    success_count = sum(1 for r in responses if r.success)
    return {"dispatched": len(responses), "success": success_count}


@with_dead_letter_protection("inventory_sync")
async def inventory_sync(ctx: dict[str, Any], adapter: str | None = None) -> dict[str, Any]:
    """Background job (cron 30m): Sync live warehouse stock balances from ERP."""
    store: BaseAuditStore = ctx.get("store") or create_audit_store()
    catalog = ctx.get("catalog") or get_catalog()
    erp_adapter = get_adapter(adapter)

    snapshots = erp_adapter.fetch_inventory(skus=list(catalog.keys()))
    count = store.record_inventory_snapshots(snapshots)
    return {"adapter": erp_adapter.adapter_type.value, "synced_count": count}


@with_dead_letter_protection("email_poll")
async def email_poll(ctx: dict[str, Any]) -> dict[str, Any]:
    """Background job (cron 2m): Poll IMAP mailbox for incoming purchase orders."""
    from preflight.intake.email import EmailIntakeService
    store: BaseAuditStore = ctx.get("store") or create_audit_store()
    service = EmailIntakeService(store=store)
    results = service.poll_once(max_messages=20)
    created_count = sum(r.orders_created for r in results)
    return {"messages_polled": len(results), "orders_created": created_count}


@with_dead_letter_protection("notify")
async def notify(
    ctx: dict[str, Any],
    order_id: int | str,
    channel: str | None = None,
) -> dict[str, Any]:
    """Background job: Send multi-channel manager alert (Telegram/Zalo)."""
    store: BaseAuditStore = ctx.get("store") or create_audit_store()
    order_row = store.get_order(str(order_id))
    if not order_row:
        return {"status": "skipped", "reason": "order_not_found"}

    from preflight.bot.telegram import TelegramBotService
    from preflight.bot.zalo import ZaloOAService

    bot = TelegramBotService()
    res = bot.send_order_alert(dict(order_row))
    return {"status": "sent" if res.success else "failed", "channel": channel or "telegram"}


@with_dead_letter_protection("escalation_check")
async def escalation_check(ctx: dict[str, Any]) -> dict[str, Any]:
    """Background job: Scan orders in review_required/ready_for_approval and escalate based on waiting time."""
    from datetime import datetime, UTC
    store: BaseAuditStore = ctx.get("store") or create_audit_store()
    policy = store.get_policy() if hasattr(store, "get_policy") else None
    escalation_hours = getattr(policy, "escalation_hours", 4.0) if policy else 4.0

    orders = store.list_orders(limit=100)
    now = datetime.now(UTC)
    reminded = 0
    escalated_director = 0

    for o in orders:
        st = o.get("status", "")
        if st not in ("review_required", "ready_for_approval"):
            continue
        created_at_str = o.get("created_at")
        if not created_at_str:
            continue
        try:
            created_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=UTC)
            age_hours = (now - created_dt).total_seconds() / 3600.0

            if age_hours >= 24.0:
                escalated_director += 1
                event_bus.publish("order.escalated", {
                    "order_id": o["id"],
                    "po_number": o["po_number"],
                    "level": "director",
                    "age_hours": round(age_hours, 1),
                })
            elif age_hours >= escalation_hours:
                reminded += 1
                event_bus.publish("order.escalated", {
                    "order_id": o["id"],
                    "po_number": o["po_number"],
                    "level": "manager_reminder",
                    "age_hours": round(age_hours, 1),
                })
        except Exception:
            continue

    return {"reminded": reminded, "escalated_director": escalated_director}


@with_dead_letter_protection("rebuild_product_embeddings")
async def rebuild_product_embeddings(ctx: dict[str, Any]) -> dict[str, Any]:
    """Background job: Re-index all catalog product embeddings and learned aliases in SQLite/Postgres."""
    from preflight.api.deps import get_catalog
    from preflight.rag.vector import VectorSemanticMatcher
    store: BaseAuditStore = ctx.get("store") or create_audit_store()
    catalog = get_catalog()
    matcher = VectorSemanticMatcher(catalog, store=store)
    matcher.index_catalog()
    return {"status": "completed", "indexed_skus": len(catalog)}


# Register all jobs in queue registry for in-memory or arq dispatch
register_job("analyze_order", analyze_order)
register_job("run_ocr", run_ocr)
register_job("outbox_dispatch", outbox_dispatch)
register_job("inventory_sync", inventory_sync)
register_job("email_poll", email_poll)
register_job("notify", notify)
register_job("escalation_check", escalation_check)
register_job("rebuild_product_embeddings", rebuild_product_embeddings)
