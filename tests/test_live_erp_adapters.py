from __future__ import annotations

import unittest
from decimal import Decimal

from preflight.erp.adapters.misa_live import MisaAmisLiveAdapter
from preflight.erp.adapters.odoo_live import OdooLiveAdapter
from preflight.erp.adapters.sap_live import SAPLiveAdapter
from preflight.erp.schemas import ERPAdapterType, ERPSyncPayload


class TestLiveERPAdapters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = ERPSyncPayload(
            event_id="evt_test_9988",
            po_number="PO-2026-9988",
            customer="Vingroup Infrastructure Corp",
            items=[
                {"sku": "LAPTOP-A14", "description": "A14 Laptop", "quantity": 10, "unit_price": "18500000", "uom": "PCE"},
                {"sku": "CAB-CAT6-3M", "description": "Cat6 Cable", "quantity": 50, "unit_price": "72000", "uom": "PCE"},
            ],
            total_amount=Decimal("188600000"),
            currency="VND",
            idempotency_key="sha256_idempotency_key_test_12345",
        )

    def test_odoo_live_adapter_dry_run_and_idempotency(self):
        """Test OdooLiveAdapter dry run generation and idempotency preservation."""
        adapter = OdooLiveAdapter(dry_run=True)
        res = adapter.sync_order(self.payload)
        self.assertTrue(res.success)
        self.assertEqual(res.adapter_type, ERPAdapterType.ODOO_LIVE)
        self.assertEqual(res.idempotency_key, self.payload.idempotency_key)
        self.assertIn("SO/2026/", res.transaction_id)

    def test_sap_live_adapter_dry_run_and_idempotency(self):
        """Test SAPLiveAdapter dry run generation and idempotency preservation."""
        adapter = SAPLiveAdapter(dry_run=True)
        res = adapter.sync_order(self.payload)
        self.assertTrue(res.success)
        self.assertEqual(res.adapter_type, ERPAdapterType.SAP_ODATA_LIVE)
        self.assertEqual(res.idempotency_key, self.payload.idempotency_key)
        self.assertIn("SAP-SO-", res.transaction_id)

    def test_misa_amis_live_adapter_dry_run_and_idempotency(self):
        """Test MisaAmisLiveAdapter dry run generation and idempotency preservation."""
        adapter = MisaAmisLiveAdapter(dry_run=True)
        res = adapter.sync_order(self.payload)
        self.assertTrue(res.success)
        self.assertEqual(res.adapter_type, ERPAdapterType.MISA_AMIS_LIVE)
        self.assertEqual(res.idempotency_key, self.payload.idempotency_key)
        self.assertIn("DH-", res.transaction_id)


if __name__ == "__main__":
    unittest.main()
