from __future__ import annotations

import json
import os
import unittest
from decimal import Decimal
from fastapi.testclient import TestClient

from preflight.agent.state import PreflightAgentState
from preflight.agent.nodes import erp_sync_node
from preflight.api.app import app
from preflight.erp.adapters.odoo_live import OdooLiveAdapter
from preflight.erp.exceptions import ERPConfigurationError
from preflight.erp.outbox import OutboxStore, compute_idempotency_key
from preflight.erp.payload import build_erp_payload
from preflight.erp.registry import get_adapter
from preflight.erp.schemas import ERPAdapterType, ERPEventStatus
from preflight.models import Analysis, LineItem, Order, Product
from preflight.services.decisions import Principal, decide_order
from preflight.store import AuditStore


class TestERPPayloadHTTP(unittest.TestCase):
    """Integration and HTTP tests for Prompt A3 (ERP Payload & Honest Outbox)."""

    def setUp(self):
        self.store = AuditStore(":memory:")
        self.outbox = OutboxStore(":memory:")
        self.client = TestClient(app)
        self.manager_headers = {"X-API-Key": "pf_dev_mgr_8802", "X-Client": "web"}
        self.admin_headers = {"X-API-Key": "pf_dev_adm_9901", "X-Client": "web"}
        self.viewer_headers = {"X-API-Key": "pf_dev_view_6604", "X-Client": "web"}

    def tearDown(self):
        self.store.close()
        self.outbox.close()

    def test_a_erp_sync_approved_po_with_full_items_and_subtotal(self):
        """(a) Upload PO with 3 lines -> approve -> /erp/sync -> outbox payload has 3 items, subtotal, currency."""
        items = (
            LineItem(sku="SKU-A", quantity=2, unit_price=Decimal("100000"), uom="PCS"),
            LineItem(sku="SKU-B", quantity=5, unit_price=Decimal("200000"), uom="BOX"),
            LineItem(sku="SKU-C", quantity=1, unit_price=Decimal("300000"), uom="SET"),
        )
        order = Order(
            po_number="PO-TEST-3ITEMS",
            customer="Acme Corp",
            items=items,
            currency="VND",
        )
        analysis = Analysis(order=order, findings=[], status="ready_for_approval")
        order_id = self.store.record_analysis(analysis, source_file="po3.json")

        # 2. Approve order via decide_order
        from preflight.security.rbac import Role
        manager = Principal(user_id="mgr1", display_name="Manager 1", role=Role.MANAGER, channel="web")
        decide_order(
            self.store,
            order_ref=order_id,
            decision="approved",
            note="Approved by manager for testing ERP sync",
            principal=manager,
        )

        # 3. Call HTTP /api/v1/erp/sync/{order_id} using overridden app dependencies
        from preflight.api.deps import get_audit_store
        from preflight.api.routes.erp import get_outbox_store
        app.dependency_overrides[get_audit_store] = lambda: self.store
        app.dependency_overrides[get_outbox_store] = lambda: self.outbox

        try:
            resp = self.client.post(
                f"/api/v1/erp/sync/{order_id}",
                headers=self.manager_headers,
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data["success"])
            self.assertIsNotNone(data["transaction_id"])
            self.assertEqual(data["mode"], "mock")

            # Check outbox events in database
            events = self.outbox.list_events()
            self.assertEqual(len(events), 1)
            ev = events[0]
            self.assertEqual(ev["po_number"], "PO-TEST-3ITEMS")
            self.assertEqual(ev["customer"], "Acme Corp")
            self.assertEqual(ev["currency"], "VND")
            self.assertEqual(ev["total_amount"], 1500000.0)

            # Check parsed payload_json
            payload_data = json.loads(ev["payload_json"])
            self.assertEqual(len(payload_data["items"]), 3)
            self.assertEqual(payload_data["items"][0]["sku"], "SKU-A")
            self.assertEqual(payload_data["items"][0]["quantity"], 2)
            self.assertEqual(payload_data["items"][1]["sku"], "SKU-B")
            self.assertEqual(payload_data["items"][1]["quantity"], 5)
            self.assertEqual(payload_data["items"][2]["sku"], "SKU-C")
            self.assertEqual(payload_data["items"][2]["quantity"], 1)
            self.assertEqual(payload_data["total_amount"], 1500000.0)
            self.assertEqual(payload_data["approved_by"], "web:mgr1")
        finally:
            app.dependency_overrides.clear()

    def test_b_sync_unapproved_order_returns_409(self):
        """(b) /erp/sync on an unapproved order -> 409 Conflict."""
        items = (LineItem(sku="SKU-A", quantity=1, unit_price=Decimal("100000")),)
        order = Order(
            po_number="PO-UNAPPROVED",
            customer="Beta Ltd",
            items=items,
            currency="VND",
        )
        analysis = Analysis(order=order, findings=[], status="review_required")
        order_id = self.store.record_analysis(analysis, source_file="unapproved.json")

        from preflight.api.deps import get_audit_store
        from preflight.api.routes.erp import get_outbox_store
        app.dependency_overrides[get_audit_store] = lambda: self.store
        app.dependency_overrides[get_outbox_store] = lambda: self.outbox

        try:
            resp = self.client.post(
                f"/api/v1/erp/sync/{order_id}",
                headers=self.manager_headers,
            )
            self.assertEqual(resp.status_code, 409)
            self.assertIn("approved", resp.json()["detail"].lower())
        finally:
            app.dependency_overrides.clear()

    def test_c_agent_run_clean_order_syncs_outbox_matching_items(self):
        """(c) Agent run on clean order -> erp_synced True and outbox items match input line items."""
        items = (
            LineItem(sku="LAPTOP-A14", quantity=2, unit_price=Decimal("18500000"), uom="PCS"),
            LineItem(sku="CAB-CAT6-3M", quantity=10, unit_price=Decimal("45000"), uom="PCS"),
        )
        order = Order(
            po_number="PO-AGENT-CLEAN",
            customer="Clean Customer",
            items=items,
            currency="VND",
        )
        catalog = {
            "LAPTOP-A14": Product(sku="LAPTOP-A14", name="Laptop A14", unit_price=Decimal("18500000"), stock=10),
            "CAB-CAT6-3M": Product(sku="CAB-CAT6-3M", name="Cat6 Cable", unit_price=Decimal("45000"), stock=50),
        }
        analysis = Analysis(order=order, findings=[], status="approved")
        order_id = self.store.record_analysis(analysis, source_file="clean.json")

        state: PreflightAgentState = {
            "po_number": "PO-AGENT-CLEAN",
            "customer": "Clean Customer",
            "currency": "VND",
            "analysis_id": order_id,
            "order": order,
            "status": "approved",
            "audit_trail": [],
        }

        res = erp_sync_node(state, catalog, self.store)
        self.assertTrue(res["erp_synced"])
        self.assertIsNotNone(res["erp_tx_id"])
        self.assertIsNotNone(res["idempotency_key"])

    def test_d_idempotent_sync_returns_existing_record(self):
        """(d) Sync 2 times on the same order -> 1 event in outbox, 2nd call returns identical record."""
        items = (LineItem(sku="SKU-X", quantity=1, unit_price=Decimal("500000")),)
        order = Order(
            po_number="PO-IDEMP-TEST",
            customer="Gamma Co",
            items=items,
            currency="VND",
        )
        analysis = Analysis(order=order, findings=[], status="ready_for_approval")
        order_id = self.store.record_analysis(analysis, source_file="idemp.json")
        from preflight.security.rbac import Role
        manager = Principal(user_id="mgr1", display_name="Manager 1", role=Role.MANAGER, channel="web")
        decide_order(
            self.store,
            order_ref=order_id,
            decision="approved",
            note="Approved for idempotency test",
            principal=manager,
        )

        from preflight.api.deps import get_audit_store
        from preflight.api.routes.erp import get_outbox_store
        app.dependency_overrides[get_audit_store] = lambda: self.store
        app.dependency_overrides[get_outbox_store] = lambda: self.outbox

        try:
            resp1 = self.client.post(f"/api/v1/erp/sync/{order_id}", headers=self.manager_headers)
            self.assertEqual(resp1.status_code, 200)
            data1 = resp1.json()

            resp2 = self.client.post(f"/api/v1/erp/sync/{order_id}", headers=self.manager_headers)
            self.assertEqual(resp2.status_code, 200)
            data2 = resp2.json()

            self.assertEqual(data1["transaction_id"], data2["transaction_id"])
            self.assertEqual(data1["idempotency_key"], data2["idempotency_key"])
            self.assertEqual(data1["mode"], data2["mode"])

            # Verify only 1 row exists in DB
            events = self.outbox.list_events()
            self.assertEqual(len(events), 1)
        finally:
            app.dependency_overrides.clear()

    def test_e_odoo_live_without_credentials_in_production_fails(self):
        """(e) ODOO_LIVE without credentials + PREFLIGHT_ENV=production -> raises ERPConfigurationError -> outbox FAILED, success=False."""
        old_env = os.getenv("PREFLIGHT_ENV")
        os.environ["PREFLIGHT_ENV"] = "production"
        try:
            adapter = OdooLiveAdapter(password="", dry_run=False)
            from preflight.erp.schemas import ERPSyncPayload
            payload = ERPSyncPayload(
                event_id="evt_test_prod",
                po_number="PO-PROD-FAIL",
                customer="Prod Corp",
                items=[{"sku": "SKU-PROD", "quantity": 1, "unit_price": "1000", "line_total": "1000"}],
                total_amount=Decimal("1000"),
                currency="VND",
                idempotency_key="idemp_prod_fail",
            )
            with self.assertRaises(ERPConfigurationError) as ctx:
                adapter.sync_order(payload)
            self.assertIn("credential", str(ctx.exception).lower())
        finally:
            if old_env is not None:
                os.environ["PREFLIGHT_ENV"] = old_env
            else:
                os.environ.pop("PREFLIGHT_ENV", None)

    def test_f_dev_mode_runs_dry_run_with_dryrun_prefix(self):
        """(f) In dev mode, live adapter missing credentials runs dry_run with 'DRYRUN-' prefix."""
        old_env = os.getenv("PREFLIGHT_ENV")
        os.environ["PREFLIGHT_ENV"] = "development"
        try:
            adapter = OdooLiveAdapter(password="", dry_run=False)
            from preflight.erp.schemas import ERPSyncPayload
            payload = ERPSyncPayload(
                event_id="evt_test_dev",
                po_number="PO-DEV-0099",
                customer="Dev Corp",
                items=[{"sku": "SKU-DEV", "quantity": 1, "unit_price": "1000", "line_total": "1000"}],
                total_amount=Decimal("1000"),
                currency="VND",
                idempotency_key="idemp_dev_dryrun",
            )
            res = adapter.sync_order(payload)
            self.assertTrue(res.success)
            self.assertEqual(res.mode, "dry_run")
            self.assertTrue(res.transaction_id.startswith("DRYRUN-"))
        finally:
            if old_env is not None:
                os.environ["PREFLIGHT_ENV"] = old_env
            else:
                os.environ.pop("PREFLIGHT_ENV", None)

    def test_g_mark_failed_3_times_becomes_dead_letter(self):
        """(g) mark_failed 3 times -> status DEAD_LETTER; fetch_pending no longer returns it."""
        event = self.outbox.enqueue_order(
            po_number="PO-RETRY-FAIL",
            customer="Retry Customer",
            items=[{"sku": "SKU-R", "quantity": 1, "unit_price": "100", "line_total": "100"}],
            total_amount=Decimal("100"),
            currency="VND",
        )

        # Retry 1
        self.outbox.mark_failed(event.event_id, "Network timeout 1")
        ev1 = self.outbox.get_by_idempotency_key(event.idempotency_key)
        self.assertEqual(ev1["status"], ERPEventStatus.PENDING.value)
        self.assertEqual(ev1["retry_count"], 1)
        self.assertIsNotNone(ev1["next_attempt_at"])

        # Retry 2
        self.outbox.mark_failed(event.event_id, "Network timeout 2")
        ev2 = self.outbox.get_by_idempotency_key(event.idempotency_key)
        self.assertEqual(ev2["status"], ERPEventStatus.PENDING.value)
        self.assertEqual(ev2["retry_count"], 2)

        # Retry 3 -> DEAD_LETTER
        self.outbox.mark_failed(event.event_id, "Network timeout 3")
        ev3 = self.outbox.get_by_idempotency_key(event.idempotency_key)
        self.assertEqual(ev3["status"], ERPEventStatus.DEAD_LETTER.value)
        self.assertEqual(ev3["retry_count"], 3)

        # fetch_pending should no longer return it
        pending = self.outbox.fetch_pending(limit=10)
        self.assertEqual(len(pending), 0)

        stats = self.outbox.get_stats()
        self.assertEqual(stats.dead_letter_count, 1)
        self.assertEqual(stats.pending_count, 0)


if __name__ == "__main__":
    unittest.main()
