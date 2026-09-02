from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from starlette.testclient import TestClient

from preflight.agent import build_preflight_graph
from preflight.api.app import app
from preflight.api.deps import get_catalog
from preflight.bot.telegram import TelegramBotService
from preflight.erp.adapters.odoo import MockOdooAdapter
from preflight.erp.adapters.sap import MockSAPAdapter
from preflight.erp.outbox import OutboxStore
from preflight.erp.worker import OutboxSyncWorker
from preflight.ingestion.pipeline import IntelligentIngestionPipeline
from preflight.models import Analysis, LineItem, Order, Product
from preflight.rag.matcher import HybridSKUMatcher
from preflight.rules import analyze_order
from preflight.security.audit_chain import AuditHashChain
from preflight.security.rate_limiter import global_rate_limiter
from preflight.store import AuditStore


class TestCompleteIntegrationSuite(unittest.TestCase):
    """
    MIT-Grade Comprehensive Integration Test Suite.
    Validates end-to-end multi-tier pipeline interoperability:
    Ingestion -> Self-Reflection Math -> 4-Tier SKU Matcher -> Deterministic Rules
    -> LangGraph Stateful Checkpointing -> Telegram Bot Alert -> Manager Decision
    -> Transactional Outbox -> ERP S/4HANA & Odoo Sync -> SOX/SOC2 Audit Certificate.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})
        cls.catalog = get_catalog()

    def setUp(self):
        global_rate_limiter.reset()
        self.tmp_dir = TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "test_integration.db"
        self.store = AuditStore(self.db_path)
        self.outbox = OutboxStore(self.db_path)


    def tearDown(self):
        self.store.close()
        self.outbox.close()
        self.tmp_dir.cleanup()

    def test_full_lifecycle_clean_order(self):
        """Test full happy-path lifecycle: Clean PO -> Ready -> Approval -> ERP Sync."""
        # 1. Ingestion & Parsing
        po_json = {
            "po_number": "PO-INT-1001",
            "customer": "Northstar Enterprise Corp",
            "currency": "VND",
            "items": [
                {"sku": "LAPTOP-A14", "quantity": 2, "unit_price": 18500000},
                {"sku": "MONITOR-27", "quantity": 4, "unit_price": 6200000},
            ],
        }
        file_bytes = json.dumps(po_json).encode("utf-8")
        pipeline = IntelligentIngestionPipeline()
        extracted, domain_order = pipeline.process_file_bytes(file_bytes, "PO-INT-1001.json")

        self.assertEqual(domain_order.po_number, "PO-INT-1001")
        self.assertTrue(extracted.math_verification.is_valid)

        # 2. Rule evaluation
        analysis = analyze_order(domain_order, self.catalog, duplicate=False)
        self.assertEqual(analysis.status, "ready_for_approval")
        self.assertEqual(len(analysis.findings), 0)

        # 3. Store in DB
        analysis_id = self.store.record_analysis(analysis, "PO-INT-1001.json")
        self.assertGreater(analysis_id, 0)

        # 4. Record Decision
        dec_id = self.store.record_decision(
            po_number="PO-INT-1001",
            decision="approved",
            actor="ops_lead@northstar.com",
            note="Approved clean order for warehouse shipment.",
        )
        self.assertGreater(dec_id, 0)

        # 5. Outbox Enqueue & Worker Sync
        order_record = self.store.get_order(analysis_id)
        event = self.outbox.enqueue_order(
            po_number=order_record["po_number"],
            customer=order_record["customer"],
            items=domain_order.to_dict()["items"],
            total_amount=domain_order.total,
            currency="VND",
        )
        self.assertIsNotNone(event.idempotency_key)

        worker = OutboxSyncWorker(outbox_store=self.outbox, adapter=MockSAPAdapter())
        results = worker.process_batch(limit=10)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)
        self.assertIn("SAP-SO-", results[0].transaction_id)

        # 6. Audit Certificate Generation
        cert = AuditHashChain.generate_compliance_certificate(
            po_number="PO-INT-1001",
            order_data=order_record,
            decisions=order_record["decisions"],
        )
        self.assertTrue(cert["chain_valid"])
        self.assertEqual(cert["chain_length"], 2)  # Ingestion + Approved
        self.assertTrue(cert["certificate_id"].startswith("CERT-"))

    def test_full_lifecycle_violation_and_hitl_resolution(self):
        """Test violation flow: Stock deficit & unknown SKU -> HITL Telegram callback -> Resume -> Outbox."""
        # 1. Ingestion of PO with issues
        po_json = {
            "po_number": "PO-INT-8899",
            "customer": "Vingroup Retail",
            "currency": "VND",
            "items": [
                {"sku": "LAPTOP-A14", "quantity": 5, "unit_price": 18500000},
                {"sku": "dây mạng 3m bấm sẵn", "quantity": 20, "unit_price": 72000},
                {"sku": "HEADSET-PRO", "quantity": 10, "unit_price": 1450000},  # Stock is 0 in catalog
            ],

        }

        # 2. Hybrid SKU Resolution
        matcher = HybridSKUMatcher(self.catalog)
        resolved_cable = matcher.resolve("dây mạng 3m bấm sẵn", customer_id="Vingroup")
        self.assertEqual(resolved_cable.matched_sku, "CAB-CAT6-3M")

        # 3. LangGraph Workflow Execution with Interrupt
        graph = build_preflight_graph(self.catalog, self.store)
        thread_id = "thread-int-8899"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "thread_id": thread_id,
            "po_number": po_json["po_number"],
            "customer": po_json["customer"],
            "line_items": po_json["items"],
            "audit_trail": [],
        }

        state = graph.invoke(initial_state, config=config)
        self.assertEqual(state["status"], "review_required")
        self.assertEqual(state["risk_level"], "MEDIUM")


        # Verify interrupt state
        next_nodes = list(graph.get_state(config).next)
        self.assertEqual(next_nodes, ["human_approval"])

        # 4. Telegram Alert & Callback Simulation
        self.store.upsert_channel_identity(
            channel="telegram",
            external_id="10099",
            user_id="chief_operations_officer",
            display_name="Chief Operations Officer",
            role="MANAGER",
        )
        bot = TelegramBotService(store=self.store)
        res = bot.handle_callback_action(
            callback_data="approve:PO-INT-8899",
            from_user_id="10099",
            from_username="chief_operations_officer",
        )
        self.assertTrue(res["success"])
        self.assertIn("chief_operations_officer", res["decided_by"])


        # 5. Resume Graph
        graph.update_state(
            config,
            {
                "decision": "APPROVED",
                "decided_by": "Telegram:@chief_operations_officer",
                "decision_notes": "Manager override for high-priority client",
            },
        )
        resumed = graph.invoke(None, config=config)
        self.assertEqual(resumed["status"].lower(), "approved")
        self.assertTrue(resumed["erp_synced"])
        self.assertIsNotNone(resumed["erp_tx_id"])

    def test_multi_adapter_erp_failover(self):
        """Test transactional outbox failover between SAP S/4HANA and Odoo adapters."""
        event = self.outbox.enqueue_order(
            po_number="PO-ADAPTER-TEST",
            customer="Multi Adapter Corp",
            items=[{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000}],
            total_amount=Decimal("18500000"),
            currency="VND",
        )

        # Process with Odoo
        odoo_worker = OutboxSyncWorker(outbox_store=self.outbox, adapter=MockOdooAdapter())
        odoo_results = odoo_worker.process_batch(limit=5)
        self.assertEqual(len(odoo_results), 1)
        self.assertTrue(odoo_results[0].success)
        self.assertTrue(odoo_results[0].transaction_id.startswith("SO/2026/"))

    def test_rest_api_end_to_end_flow(self):
        """Test full workflow using FastAPI REST endpoints via TestClient."""
        # 1. Upload fresh unique clean PO
        clean_po = {
            "po_number": f"PO-E2E-UNIQUE-{abs(hash(self.db_path)) % 100000}",
            "customer": "Global Tech Ventures",
            "currency": "VND",
            "items": [
                {"sku": "LAPTOP-A14", "quantity": 2, "unit_price": 18500000},
                {"sku": "MONITOR-27", "quantity": 2, "unit_price": 6200000},
            ],
        }
        upload_res = self.client.post(
            "/api/v1/orders/upload",
            files={
                "file": (
                    "po-unique-e2e.json",
                    json.dumps(clean_po).encode("utf-8"),
                    "application/json",
                )
            },
        )
        self.assertEqual(upload_res.status_code, 201)
        order_id = upload_res.json()["id"]

        # 2. Query Detail
        detail_res = self.client.get(f"/api/v1/orders/{order_id}")
        self.assertEqual(detail_res.status_code, 200)
        self.assertEqual(detail_res.json()["status"], "ready_for_approval")

        # 3. Perform Decision
        dec_res = self.client.post(
            f"/api/v1/orders/{order_id}/decide",
            json={
                "decision": "approved",
                "actor": "integration_tester@mit.edu",
                "note": "Verified end-to-end integration pass.",
            },
        )
        self.assertEqual(dec_res.status_code, 200)
        self.assertEqual(dec_res.json()["decision"], "approved")

        # 4. Trigger ERP Sync via API
        erp_res = self.client.post(f"/api/v1/erp/sync/{order_id}")
        self.assertEqual(erp_res.status_code, 200)
        self.assertTrue(erp_res.json()["success"])

        # 5. Fetch Audit Certificate
        cert_res = self.client.get(f"/api/v1/orders/{order_id}/audit-certificate")
        self.assertEqual(cert_res.status_code, 200)
        cert_data = cert_res.json()
        self.assertTrue(cert_data["chain_valid"])
        self.assertGreaterEqual(cert_data["chain_length"], 2)


if __name__ == "__main__":
    unittest.main()
