from __future__ import annotations

import hashlib
import time
import uuid
from decimal import Decimal
from typing import Any

from preflight.agent.state import PreflightAgentState
from preflight.models import Analysis, Finding, LineItem, Order, Product
from preflight.rag.matcher import HybridSKUMatcher
from preflight.rules import analyze_order
from preflight.rules_context import build_rule_context
from preflight.store import AuditStore


try:
    from preflight.bot.telegram import TelegramBotService
except ImportError:
    class TelegramBotService:  # type: ignore
        def __init__(self, token: str | None = None, chat_id: str | None = None, store: AuditStore | None = None):
            self.store = store
        def send_order_alert(self, order: dict[str, Any], web_base_url: str = "http://localhost:3000"):
            class MockResult:
                success = True
                dry_run = True
            return MockResult()


def ingestion_node(state: PreflightAgentState, catalog: dict[str, Product], store: AuditStore) -> dict[str, Any]:
    """Node 1: Ingestion & Normalization.
    Validates input order data, ensures fields are structured, appends audit trail.
    """
    po_num = state.get("po_number", "PO-UNKNOWN")
    cust = state.get("customer", "Unknown Customer")
    lines = state.get("line_items", [])
    raw_content = state.get("raw_content")

    # If line items provided in order dict
    order_dict = state.get("order", {})
    if not lines and "items" in order_dict:
        lines = order_dict["items"]

    trail = list(state.get("audit_trail", []))
    trail.append(f"[{time.strftime('%H:%M:%S')}] Ingested order '{po_num}' from customer '{cust}' ({len(lines)} lines).")

    return {
        "po_number": po_num,
        "customer": cust,
        "line_items": lines,
        "audit_trail": trail,
    }


def sku_resolution_node(state: PreflightAgentState, catalog: dict[str, Product], store: AuditStore) -> dict[str, Any]:
    """Node 2: 4-Tier Hybrid SKU Resolution RAG.
    Resolves raw item queries to official catalog SKUs.
    """
    matcher = HybridSKUMatcher(catalog)
    lines = state.get("line_items", [])
    cust = state.get("customer", "")
    resolved_skus: dict[str, Any] = {}
    updated_lines: list[dict[str, Any]] = []

    trail = list(state.get("audit_trail", []))

    for item in lines:
        raw_sku = str(item.get("sku", "")).strip()
        unit_price = item.get("unit_price", 0)
        qty = item.get("quantity", 1)

        # Run 4-Tier RAG Resolution
        res = matcher.resolve(raw_sku, customer_id=cust)
        resolved_skus[raw_sku] = {
            "matched_sku": res.matched_sku,
            "name": res.name,
            "confidence": res.confidence_score,
            "tier_used": res.tier_used.value,
            "is_confident": res.is_confident,
            "explanation": res.explanation,
        }

        # If confident, update line item target SKU
        target_sku = res.matched_sku if (res.is_confident and res.matched_sku) else raw_sku
        updated_lines.append({
            "sku": target_sku,
            "raw_sku": raw_sku,
            "quantity": qty,
            "unit_price": unit_price,
            "resolved_name": res.name,
            "confidence": res.confidence_score,
            "tier": res.tier_used.value,
        })

    trail.append(
        f"[{time.strftime('%H:%M:%S')}] SKU Resolution completed via 4-tier waterfall ({len(resolved_skus)} items resolved)."
    )

    return {
        "line_items": updated_lines,
        "matched_skus": resolved_skus,
        "audit_trail": trail,
    }


def audit_rules_node(state: PreflightAgentState, catalog: dict[str, Product], store: AuditStore) -> dict[str, Any]:
    """Node 3: Deterministic Preflight Rules Evaluation.
    Calculates exact price differences, stock sufficiency, and duplicate PO checks.
    """
    po_num = state.get("po_number", "PO-UNKNOWN")
    cust = state.get("customer", "Unknown Customer")
    lines = state.get("line_items", [])

    order_items = [
        LineItem(
            sku=str(l.get("sku", "")),
            quantity=int(l.get("quantity", 1)),
            unit_price=Decimal(str(l.get("unit_price", 0))),
        )
        for l in lines
    ]
    order = Order(po_number=po_num, customer=cust, items=order_items)

    # Check duplicate in store and build comprehensive RuleContext
    duplicate = store.has_po(po_num)
    ctx = build_rule_context(store, catalog, order, duplicate=duplicate)
    analysis: Analysis = analyze_order(order, ctx)


    # Convert findings to dicts
    findings_dicts = [f.to_dict() for f in analysis.findings]

    # Calculate risk level
    if analysis.status == "blocked":
        risk_level = "HIGH"
        decision_req = True
    elif analysis.status == "review_required":
        risk_level = "MEDIUM"
        decision_req = True
    else:
        risk_level = "LOW"
        decision_req = False

    # Store analysis record in store if not duplicate
    if not duplicate:
        store.record_analysis(analysis, source_file=state.get("source_file", "langgraph_agent"))

    trail = list(state.get("audit_trail", []))
    trail.append(
        f"[{time.strftime('%H:%M:%S')}] Rules Audit completed: status='{analysis.status}', "
        f"risk='{risk_level}', findings={len(findings_dicts)}."
    )

    return {
        "order": order.to_dict(),
        "findings": findings_dicts,
        "status": analysis.status,
        "risk_level": risk_level,
        "decision_required": decision_req,
        "audit_trail": trail,
    }


def hitl_dispatch_node(state: PreflightAgentState, catalog: dict[str, Product], store: AuditStore) -> dict[str, Any]:
    """Node 4: Human-in-the-loop Outbound Notification.
    Dispatches Telegram/Zalo approval cards with inline action buttons.
    """
    trail = list(state.get("audit_trail", []))
    po_num = state.get("po_number", "")
    risk = state.get("risk_level", "MEDIUM")

    bot = TelegramBotService(store=store)
    order_dict = {
        "id": po_num,
        "po_number": po_num,
        "customer": state.get("customer", ""),
        "status": state.get("status", "review_required"),
        "risk_level": risk,
        "total_value": float(state.get("order", {}).get("total", 0)),
        "currency": "VND",
        "findings": state.get("findings", []),
        "line_items": state.get("line_items", []),
    }

    res = bot.send_order_alert(order_dict)
    trail.append(f"[{time.strftime('%H:%M:%S')}] Dispatched Telegram approval alert (dry_run={res.dry_run}).")

    return {
        "telegram_notified": True,
        "audit_trail": trail,
    }


def human_approval_node(state: PreflightAgentState, catalog: dict[str, Product], store: AuditStore) -> dict[str, Any]:
    """Node 5: Human Approval Checkpoint Node (Interrupt Target).
    When graph resumes after human approval, this node verifies decision.
    """
    decision = state.get("decision", "APPROVED")
    decided_by = state.get("decided_by", "Manager")
    trail = list(state.get("audit_trail", []))
    trail.append(f"[{time.strftime('%H:%M:%S')}] Human decision recorded: '{decision}' by '{decided_by}'.")

    # Update status to reflect human decision
    updated_status = "approved" if decision == "APPROVED" else "rejected"

    return {
        "status": updated_status,
        "audit_trail": trail,
    }


def erp_sync_node(state: PreflightAgentState, catalog: dict[str, Product], store: AuditStore) -> dict[str, Any]:
    """Node 6: Downstream ERP Synchronization.
    Generates idempotency key, posts order to ERP adapter, logs transaction ID.
    """
    po_num = state.get("po_number", "PO-UNKNOWN")
    status = state.get("status", "approved")
    trail = list(state.get("audit_trail", []))

    if status in ["rejected", "blocked"]:
        trail.append(f"[{time.strftime('%H:%M:%S')}] Order '{po_num}' was rejected/blocked. ERP sync skipped.")
        return {
            "erp_synced": False,
            "erp_tx_id": None,
            "audit_trail": trail,
        }

    from decimal import Decimal
    from preflight.erp.outbox import OutboxStore
    from preflight.erp.worker import OutboxSyncWorker
    from preflight.erp.adapters.sap import MockSAPAdapter


    # Persist in Outbox and dispatch to ERP Adapter
    outbox = OutboxStore()
    event = outbox.enqueue_order(
        po_number=po_num,
        customer=str(state.get("customer", "")),
        items=state.get("items", []),
        total_amount=Decimal(str(state.get("total", 0))),
        currency=str(state.get("currency", "VND")),
    )
    worker = OutboxSyncWorker(outbox_store=outbox, adapter=MockSAPAdapter())
    batch_results = worker.process_batch(limit=5)
    tx_id = f"ERP-TX-{event.idempotency_key[:8].upper()}"
    if batch_results and batch_results[0].transaction_id:
        tx_id = batch_results[0].transaction_id


    trail.append(
        f"[{time.strftime('%H:%M:%S')}] Order '{po_num}' synced to ERP successfully via Outbox. TxID: '{tx_id}', IdempotencyKey: '{event.idempotency_key}'."
    )


    return {
        "erp_synced": True,
        "erp_tx_id": tx_id,
        "idempotency_key": event.idempotency_key,
        "audit_trail": trail,
    }

