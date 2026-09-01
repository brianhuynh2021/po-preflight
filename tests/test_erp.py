from __future__ import annotations

import unittest
from decimal import Decimal

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.erp.adapters.odoo import MockOdooAdapter
from preflight.erp.adapters.sap import MockSAPAdapter
from preflight.erp.outbox import OutboxStore
from preflight.erp.schemas import (
    ERPAdapterType,
    ERPEventStatus,
    ERPSyncPayload,
)
from preflight.erp.worker import OutboxSyncWorker
from preflight.security.rate_limiter import global_rate_limiter


class TestERPAndOutboxWorker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})

    def setUp(self):
        global_rate_limiter.reset()
        self.outbox = OutboxStore(":memory:")
        self.sap_adapter = MockSAPAdapter()
        self.odoo_adapter = MockOdooAdapter()
        self.worker = OutboxSyncWorker(outbox_store=self.outbox, adapter=self.sap_adapter)


    def test_mock_sap_adapter(self):
        """Test Mock SAP Adapter returns SAP-SO reference."""
        payload = ERPSyncPayload(
            event_id="evt_01",
            po_number="PO-10427",
            customer="Acme Corp",
            items=[{"sku": "LAPTOP-A14", "quantity": 1}],
            total_amount=Decimal("18500000"),
            currency="VND",
            idempotency_key="idemp_12345",
        )
        res = self.sap_adapter.sync_order(payload)
        self.assertTrue(res.success)
        self.assertEqual(res.adapter_type, ERPAdapterType.MOCK_SAP)
        self.assertIn("SAP-SO-", res.transaction_id)
        self.assertEqual(res.idempotency_key, "idemp_12345")

    def test_mock_odoo_adapter(self):
        """Test Mock Odoo Adapter returns SO/2026 reference."""
        payload = ERPSyncPayload(
            event_id="evt_02",
            po_number="PO-2026-99",
            customer="Northstar",
            items=[{"sku": "CAB-CAT6-3M", "quantity": 5}],
            total_amount=Decimal("360000"),
            currency="VND",
            idempotency_key="idemp_67890",
        )
        res = self.odoo_adapter.sync_order(payload)
        self.assertTrue(res.success)
        self.assertEqual(res.adapter_type, ERPAdapterType.MOCK_ODOO)
        self.assertIn("SO/2026/", res.transaction_id)

    def test_outbox_enqueue_and_idempotency(self):
        """Test outbox deduplicates enqueues using SHA256 idempotency key."""
        # First enqueue
        p1 = self.outbox.enqueue_order(
            po_number="PO-IDEMP-01",
            customer="Acme Corp",
            items=[{"sku": "LAPTOP-A14", "quantity": 1}],
            total_amount=Decimal("18500000"),
        )
        self.assertIsNotNone(p1.event_id)

        # Duplicate enqueue
        p2 = self.outbox.enqueue_order(
            po_number="PO-IDEMP-01",
            customer="Acme Corp",
            items=[{"sku": "LAPTOP-A14", "quantity": 1}],
            total_amount=Decimal("18500000"),
        )
        self.assertEqual(p1.idempotency_key, p2.idempotency_key)
        self.assertEqual(p1.event_id, p2.event_id)

        # Outbox stats should count 1 event
        stats = self.outbox.get_stats()
        self.assertEqual(stats.total_events, 1)
        self.assertEqual(stats.pending_count, 1)

    def test_outbox_worker_process_batch(self):
        """Test OutboxSyncWorker drains pending queue to ERP and updates status to SENT."""
        self.outbox.enqueue_order(
            po_number="PO-WORKER-01",
            customer="Beta LLC",
            items=[{"sku": "CAB-CAT6-3M", "quantity": 10}],
            total_amount=Decimal("720000"),
        )

        # Process queue
        responses = self.worker.process_batch(limit=5)
        self.assertEqual(len(responses), 1)
        self.assertTrue(responses[0].success)

        # Stats should show 1 sent, 0 pending
        stats = self.outbox.get_stats()
        self.assertEqual(stats.sent_count, 1)
        self.assertEqual(stats.pending_count, 0)

    def test_api_erp_routes(self):
        """Test REST endpoints for outbox processing and status."""
        res_status = self.client.get("/api/v1/erp/outbox/status")
        self.assertEqual(res_status.status_code, 200)
        self.assertIn("stats", res_status.json())

        res_process = self.client.post("/api/v1/erp/outbox/process?limit=5")
        self.assertEqual(res_process.status_code, 200)
        self.assertIn("processed_count", res_process.json())


if __name__ == "__main__":
    unittest.main()
