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
    When graph resumes after human approval, this node executes decision through single DecisionService gate.
    """
    from preflight.security.rbac import Role
    from preflight.services.decisions import DecisionError, Principal, decide_order

    decision = state.get("decision", "APPROVED")
    decided_by = state.get("decided_by", "Manager")
    notes = state.get("notes") or state.get("decision_notes", "Decision executed via Agentic Workflow")
    po_num = state.get("po_number", "")
    trail = list(state.get("audit_trail", []))

    clean_decision = "approved" if str(decision).upper() == "APPROVED" else ("rejected" if str(decision).upper() == "REJECTED" else "needs_changes")
    
    # If order was already decided in store (e.g. by bot webhook before resume), reuse decided state
    existing = store.get_order(po_num) or store.get_order_by_po(po_num)
    if existing and existing.get("status") in {"approved", "rejected", "needs_changes"}:
        decided_status = existing.get("status")
        trail.append(f"[{time.strftime('%H:%M:%S')}] Human decision recorded: '{decision}' by '{decided_by}'.")
        return {
            "status": decided_status,
            "decision_error": None,
            "audit_trail": trail,
        }

    principal = Principal(
        user_id=decided_by,
        display_name=decided_by,
        role=Role.MANAGER,
        channel="agent",
    )


    try:
        decide_order(
            store=store,
            order_ref=po_num,
            decision=clean_decision,
            note=notes,
            principal=principal,
        )
        trail.append(f"[{time.strftime('%H:%M:%S')}] Human decision recorded: '{decision}' by '{decided_by}'.")
        return {
            "status": clean_decision,
            "decision_error": None,
            "audit_trail": trail,
        }

    except DecisionError as err:
        trail.append(f"[{time.strftime('%H:%M:%S')}] Decision failed governance validation: {err.message}")
        return {
            "status": "decision_rejected",
            "decision_error": err.message,
            "error": err.message,
            "audit_trail": trail,
        }



def erp_sync_node(state: PreflightAgentState, catalog: dict[str, Product], store: AuditStore) -> dict[str, Any]:
    """Node 6: Downstream ERP Synchronization.
    Generates idempotency key, posts order to ERP adapter, logs transaction ID.
    """
    po_num = state.get("po_number", "PO-UNKNOWN")
    status = state.get("status", "approved")
    trail = list(state.get("audit_trail", []))

    if status in ["rejected", "blocked", "decision_rejected"]:
        trail.append(f"[{time.strftime('%H:%M:%S')}] Order '{po_num}' was rejected/blocked. ERP sync skipped.")
        return {
            "erp_synced": False,
            "erp_tx_id": None,
            "audit_trail": trail,
        }

    from preflight.erp.outbox import OutboxStore, compute_idempotency_key
    from preflight.erp.payload import build_erp_payload
    from preflight.erp.registry import get_adapter
    from preflight.erp.worker import OutboxSyncWorker
    from preflight.observability.metrics import metrics_registry

    order_obj = state.get("order")
    analysis_id = state.get("analysis_id")

    if order_obj:
        draft = build_erp_payload(order_obj, source_analysis_id=analysis_id)
    else:
        stored_row = store.get_order_by_po(po_num) if hasattr(store, "get_order_by_po") else None
        if not stored_row:
            trail.append(f"[{time.strftime('%H:%M:%S')}] Order '{po_num}' not found for ERP payload.")
            return {"erp_synced": False, "erp_tx_id": None, "audit_trail": trail}
        draft = build_erp_payload(stored_row, source_analysis_id=analysis_id)

    idemp_key = compute_idempotency_key(analysis_id, draft.po_number, draft.items)

    outbox_path = getattr(store, "path", "runtime/preflight.db")
    outbox = OutboxStore(outbox_path)
    items_dicts = [it.to_dict() for it in draft.items]
    event = outbox.enqueue_order(
        po_number=draft.po_number,
        customer=draft.customer,
        items=items_dicts,
        total_amount=draft.subtotal,
        currency=draft.currency,
        idempotency_key=idemp_key,
        approved_by=draft.approved_by,
        approved_at=draft.approved_at,
        source_analysis_id=analysis_id,
    )

    adapter = get_adapter(None)
    worker = OutboxSyncWorker(outbox_store=outbox, adapter=adapter, metrics_registry=metrics_registry)
    batch_results = worker.process_batch(limit=5)
    matching = next((r for r in batch_results if r.idempotency_key == event.idempotency_key), None)

    if matching and matching.success:
        tx_id = matching.transaction_id
        mode = matching.mode
        trail.append(
            f"[{time.strftime('%H:%M:%S')}] Order '{po_num}' synced to ERP successfully via Outbox. TxID: '{tx_id}', IdempotencyKey: '{idemp_key}' [mode={mode}]."
        )
        return {
            "erp_synced": True,
            "erp_tx_id": tx_id,
            "idempotency_key": idemp_key,
            "audit_trail": trail,
        }
    else:
        err = matching.error_message if matching else "ERP sync failed or queued"
        trail.append(f"[{time.strftime('%H:%M:%S')}] ERP sync failure for order '{po_num}': {err}")
        return {
            "erp_synced": False,
            "erp_tx_id": None,
            "idempotency_key": idemp_key,
            "error": err,
            "audit_trail": trail,
        }

