from __future__ import annotations

import unittest
from decimal import Decimal

from starlette.testclient import TestClient

from preflight.agent import build_preflight_graph
from preflight.api.app import app
from preflight.models import Product
from preflight.security.rate_limiter import global_rate_limiter
from preflight.store import AuditStore


import uuid


class TestLangGraphAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = {
            "LAPTOP-A14": Product(
                sku="LAPTOP-A14",
                name="A14 Business Laptop",
                unit_price=Decimal("18500000"),
                stock=50,
                active=True,
            ),
            "CAB-CAT6-3M": Product(
                sku="CAB-CAT6-3M",
                name="Cat6 Ethernet Cable 3m",
                unit_price=Decimal("72000"),
                stock=200,
                active=True,
            ),
            "HEADSET-PRO": Product(
                sku="HEADSET-PRO",
                name="Professional Headset",
                unit_price=Decimal("1450000"),
                stock=0,  # Zero stock triggers warning
                active=True,
            ),
        }
        cls.client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})


    def setUp(self):
        global_rate_limiter.reset()
        self.store = AuditStore(":memory:")
        self.graph = build_preflight_graph(self.catalog, self.store)

    def test_clean_order_auto_erp_sync(self):
        """Test clean order flows straight through to ERP without interruption."""
        thread_id = f"test-clean-{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "thread_id": thread_id,
            "po_number": "PO-CLEAN-01",
            "customer": "Acme Global",
            "line_items": [
                {"sku": "LAPTOP-A14", "quantity": 2, "unit_price": 18500000},
            ],
            "audit_trail": [],
        }

        final_state = self.graph.invoke(initial_state, config=config)
        self.assertEqual(final_state["status"], "ready_for_approval")
        self.assertEqual(final_state["risk_level"], "LOW")
        self.assertTrue(final_state["erp_synced"])
        self.assertIsNotNone(final_state["erp_tx_id"])
        self.assertIsNotNone(final_state["idempotency_key"])

        # Verify no further nodes waiting
        next_nodes = list(self.graph.get_state(config).next)
        self.assertEqual(len(next_nodes), 0)

    def test_risky_order_hitl_interrupt_and_resume(self):
        """Test risky order interrupts at human_approval, then resumes upon approval."""
        thread_id = f"test-risk-{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id}}

        # Out of stock item triggers warning
        initial_state = {
            "thread_id": thread_id,
            "po_number": "PO-RISK-01",
            "customer": "Northstar Retail",
            "line_items": [
                {"sku": "HEADSET-PRO", "quantity": 5, "unit_price": 1450000},
            ],
            "audit_trail": [],
        }

        # 1. First run -> should interrupt before human_approval
        paused_state = self.graph.invoke(initial_state, config=config)
        self.assertEqual(paused_state["status"], "review_required")
        self.assertEqual(paused_state["risk_level"], "MEDIUM")
        self.assertFalse(paused_state.get("erp_synced", False))

        # Check graph state is paused at human_approval
        snapshot = self.graph.get_state(config)
        self.assertIn("human_approval", snapshot.next)

        # 2. Resume with human approval
        self.graph.update_state(
            config,
            {
                "decision": "APPROVED",
                "decided_by": "Telegram:@chief_manager",
                "decision_notes": "Stock override approved by operations",
            },
        )

        resumed_state = self.graph.invoke(None, config=config)
        self.assertEqual(resumed_state["status"], "approved")
        self.assertTrue(resumed_state["erp_synced"])
        self.assertIsNotNone(resumed_state["erp_tx_id"])

        # Check audit trail logs all steps
        audit_trail_text = " ".join(resumed_state["audit_trail"])
        self.assertIn("Ingested order", audit_trail_text)
        self.assertIn("Rules Audit completed", audit_trail_text)
        self.assertIn("Human decision recorded: 'APPROVED'", audit_trail_text)
        self.assertIn("synced to ERP successfully", audit_trail_text)

    def test_api_agent_endpoints(self):
        """Test REST API /api/v1/agent/run and /api/v1/agent/resume."""
        import uuid
        unique_po = f"PO-API-{uuid.uuid4().hex[:6].upper()}"
        run_payload = {
            "po_number": unique_po,
            "customer": "Apex Solutions",
            "line_items": [
                {"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000},
            ],
        }
        res = self.client.post("/api/v1/agent/run", json=run_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ready_for_approval")
        self.assertTrue(data["erp_synced"])


if __name__ == "__main__":
    unittest.main()
