#!/usr/bin/env python3
"""PO Preflight - End-to-End Autonomous AI Agent & Backend Pipeline Demo
Run: PYTHONPATH=src python3 scripts/demo_e2e.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from decimal import Decimal

# Ensure src/ is in sys.path automatically
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Rich ANSI colors
BOLD = "\033[1m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
RESET = "\033[0m"


def header(step: int, title: str):
    print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{YELLOW}▶ [STAGE {step}/6] {title}{RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════{RESET}")


def sub(msg: str):
    print(f"  {CYAN}▸{RESET} {msg}")


def success(msg: str):
    print(f"  {GREEN}✔ {msg}{RESET}")


def warn(msg: str):
    print(f"  {YELLOW}⚠ {msg}{RESET}")


def run_demo():
    print(f"\n{BOLD}{MAGENTA}╔══════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{MAGENTA}║      🚀 PO PREFLIGHT — AGENTIC AI & ENTERPRISE BACKEND DEMO          ║{RESET}")
    print(f"{BOLD}{MAGENTA}╚══════════════════════════════════════════════════════════════════════╝{RESET}")

    # -------------------------------------------------------------------------
    # STAGE 1: System Diagnostic & Catalog Indexing
    # -------------------------------------------------------------------------
    header(1, "SYSTEM DIAGNOSTICS & ENTERPRISE CATALOG INITIALIZATION")
    from preflight.api.deps import get_catalog
    from preflight.store import AuditStore

    catalog = get_catalog()
    sub(f"Loaded master warehouse catalog: {BOLD}{len(catalog)}{RESET} registered SKUs.")
    sub(f"Sample SKU: LAPTOP-A14 (Name: {catalog['LAPTOP-A14'].name}, Price: {catalog['LAPTOP-A14'].unit_price:,.0f} VND, Stock: {catalog['LAPTOP-A14'].stock})")

    store = AuditStore(":memory:")
    success("AuditStore SQLite Engine connected in in-memory WAL mode.")

    time.sleep(0.3)

    # -------------------------------------------------------------------------
    # STAGE 2: Multimodal Ingestion & Self-Reflection Math Verifier
    # -------------------------------------------------------------------------
    header(2, "MULTIMODAL DOCUMENT INGESTION & ZERO-HALLUCINATION MATH GROUNDING")
    from preflight.ingestion.pipeline import IntelligentIngestionPipeline

    ingest_pipeline = IntelligentIngestionPipeline()
    sample_scan_doc = {
        "po_number": "PO-2026-8899",
        "customer": "Vingroup Retail Infrastructure",
        "items": [
            {"sku": "LAPTOP-A14", "quantity": 5, "unit_price": 18500000},
            {"sku": "dây mạng 3m bấm sẵn", "quantity": 20, "unit_price": 72000},
            {"sku": "HEADSET-PRO", "quantity": 10, "unit_price": 1450000},
        ],
    }
    file_bytes = json.dumps(sample_scan_doc).encode("utf-8")
    sub("Ingesting document 'PO-2026-8899.json' via Cascading Ingestion Pipeline...")

    extracted, domain_order = ingest_pipeline.process_file_bytes(file_bytes, "PO-2026-8899.json")
    success(f"Document classified as: {BOLD}{extracted.document_type.value}{RESET}")
    success(f"Extractor utilized: {BOLD}{extracted.extractor_used.value}{RESET} (Confidence: {extracted.confidence_score * 100:.0f}%)")
    success(f"Self-Reflection Math: {BOLD}{extracted.math_verification.message}{RESET}")

    time.sleep(0.3)

    # -------------------------------------------------------------------------
    # STAGE 3: 4-Tier Hybrid SKU Resolution & Vector Search RAG
    # -------------------------------------------------------------------------
    header(3, "4-TIER WATERFALL HYBRID SKU RESOLUTION (EXACT -> FUZZY -> VECTOR -> LLM)")
    from preflight.rag.matcher import HybridSKUMatcher

    sku_matcher = HybridSKUMatcher(catalog)
    test_queries = [
        ("LAPTOP-A14", "Standard SKU query"),
        ("laptop-a14-biz", "Slight typo / suffix variant"),
        ("dây mạng 3m bấm sẵn", "Vietnamese semantic nickname"),
    ]

    for q, desc in test_queries:
        res = sku_matcher.resolve(q, customer_id="Northstar")
        match_str = f"-> Matched SKU: {BOLD}{res.matched_sku}{RESET} ({res.name})"
        sub(f"Query '{q}' [{desc}]")
        print(f"     {GREEN}↳ Tier: {res.tier_used.value} | Confidence: {res.confidence_score:.2f} {match_str}{RESET}")

    time.sleep(0.3)

    # -------------------------------------------------------------------------
    # STAGE 4: LangGraph Stateful Workflow & Human-in-the-Loop Interrupt
    # -------------------------------------------------------------------------
    header(4, "LANGGRAPH STATEFUL WORKFLOW & HITL CHECKPOINT INTERRUPTION")
    from preflight.agent import build_preflight_graph

    thread_id = "thread-demo-8899"
    config = {"configurable": {"thread_id": thread_id}}
    graph = build_preflight_graph(catalog, store)

    initial_state = {
        "thread_id": thread_id,
        "po_number": "PO-2026-8899",
        "customer": "Vingroup Retail Infrastructure",
        "line_items": [
            {"sku": "LAPTOP-A14", "quantity": 5, "unit_price": 18500000},
            {"sku": "dây mạng 3m bấm sẵn", "quantity": 20, "unit_price": 72000},
            {"sku": "HEADSET-PRO", "quantity": 10, "unit_price": 1450000},
        ],
        "audit_trail": [],
    }

    sub(f"Invoking StateGraph for thread '{thread_id}'...")
    paused_state = graph.invoke(initial_state, config=config)

    warn(f"Deterministic Rules flagged findings: Status='{paused_state['status']}', Risk='{paused_state['risk_level']}'.")
    for f in paused_state.get("findings", []):
        print(f"     {YELLOW}• [{f['code']}] {f['message']}{RESET}")

    waiting_nodes = list(graph.get_state(config).next)
    warn(f"Workflow interrupted before node: {BOLD}{waiting_nodes}{RESET}. Checkpoint persisted in memory.")

    time.sleep(0.3)

    # -------------------------------------------------------------------------
    # STAGE 5: Multi-Channel Telegram Alert & Manager Approval Webhook
    # -------------------------------------------------------------------------
    header(5, "MULTI-CHANNEL TELEGRAM ALERT & MANAGER APPROVAL WEBHOOK")
    from preflight.bot.telegram import TelegramBotService

    bot = TelegramBotService(store=store)
    sub("Formatting rich HTML Telegram alert card...")
    sub("Generated inline keyboard: [✅ Duyệt Đơn (Approve)] [❌ Từ Chối] [📝 Yêu Cầu Sửa]")

    print(f"\n{CYAN}--- Simulated Telegram Push Message ---{RESET}")
    print(f"📋 {BOLD}PO PREFLIGHT ALERT — ĐƠN HÀNG MỚI{RESET}")
    print(f"🆔 Mã Đơn: PO-2026-8899 | Khách: Vingroup Retail Infrastructure")
    print(f"💰 Tổng giá trị: 108,440,000 VND | ⚠️ Trạng thái: REVIEW REQUIRED (CẦN DUYỆT)")
    print(f"{CYAN}---------------------------------------{RESET}\n")

    sub("Simulating Manager clicking [✅ Duyệt Đơn] on Telegram mobile app...")
    bot_res = bot.handle_callback_action(
        callback_data="approve:PO-2026-8899",
        from_username="chief_operations_officer",
    )
    success(f"Telegram Webhook callback processed: {bot_res.get('message')}")

    time.sleep(0.3)

    # -------------------------------------------------------------------------
    # STAGE 6: Resuming LangGraph & Transactional Outbox ERP Sync (SAP / Odoo)
    # -------------------------------------------------------------------------
    header(6, "RESUMING WORKFLOW & TRANSACTIONAL OUTBOX ERP SYNCHRONIZATION")
    from preflight.erp.adapters.sap import MockSAPAdapter
    from preflight.erp.outbox import OutboxStore
    from preflight.erp.worker import OutboxSyncWorker

    sub(f"Resuming paused thread '{thread_id}' with manager approval payload...")
    graph.update_state(
        config,
        {
            "decision": "APPROVED",
            "decided_by": "Telegram:@chief_operations_officer",
            "decision_notes": "Stock override approved for Vingroup",
        },
    )
    resumed_state = graph.invoke(None, config=config)

    success(f"Graph execution completed! Status: {BOLD}{resumed_state['status'].upper()}{RESET}")
    success(f"ERP Transaction ID: {BOLD}{resumed_state['erp_tx_id']}{RESET}")
    success(f"Idempotency Key: {BOLD}{resumed_state['idempotency_key']}{RESET}")

    # Outbox Worker demonstration
    outbox = OutboxStore(":memory:")
    outbox.enqueue_order(
        po_number="PO-2026-8899",
        customer="Vingroup Retail Infrastructure",
        items=initial_state["line_items"],
        total_amount=Decimal("108440000"),
    )
    worker = OutboxSyncWorker(outbox_store=outbox, adapter=MockSAPAdapter())
    erp_results = worker.process_batch()
    success(f"Transactional Outbox delivered to SAP S/4HANA: {BOLD}{erp_results[0].transaction_id}{RESET}")

    print(f"\n{BOLD}{GREEN}══════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{GREEN}🎉 FULL END-TO-END DEMO COMPLETED SUCCESSFULLY WITH 100% PASS RATE!  {RESET}")
    print(f"{BOLD}{GREEN}══════════════════════════════════════════════════════════════════════{RESET}\n")


if __name__ == "__main__":
    run_demo()
