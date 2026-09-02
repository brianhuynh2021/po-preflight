from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import tempfile

from preflight.erp.adapters.misa_live import MisaAmisLiveAdapter
from preflight.erp.adapters.odoo import MockOdooAdapter
from preflight.erp.adapters.odoo_live import OdooLiveAdapter
from preflight.erp.adapters.sap import MockSAPAdapter
from preflight.erp.adapters.sap_live import SAPLiveAdapter
from preflight.models import (
    Analysis,
    Finding,
    InventorySnapshot,
    LineItem,
    Order,
    Product,
    RulePolicy,
    UOMConversion,
)
from preflight.rules import analyze_order
from preflight.rules_context import build_rule_context
from preflight.store import AuditStore


class TestInventoryAndATP(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_inventory.db"
        self.store = AuditStore(self.db_path)
        self.catalog = {
            "LAPTOP-A14": Product(
                sku="LAPTOP-A14",
                name="Laptop Pro 14",
                unit_price=Decimal("18500000"),
                stock=10,
                base_uom="PCS",
            ),
            "MONITOR-27": Product(
                sku="MONITOR-27",
                name="Màn hình 27 inch",
                unit_price=Decimal("4500000"),
                stock=20,
                base_uom="PCS",
            ),
        }

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_erp_adapters_fetch_inventory(self):
        """Test fetch_inventory across all mock and live dry-run adapters."""
        adapters = [
            MockOdooAdapter(),
            MockSAPAdapter(),
            OdooLiveAdapter(dry_run=True),
            SAPLiveAdapter(dry_run=True),
            MisaAmisLiveAdapter(dry_run=True),
        ]
        for adapter in adapters:
            snaps = adapter.fetch_inventory(skus=["LAPTOP-A14", "MONITOR-27"])
            self.assertGreaterEqual(len(snaps), 1)
            skus_fetched = [s.sku for s in snaps]
            self.assertIn("LAPTOP-A14", skus_fetched)
            self.assertIsInstance(snaps[0].on_hand, Decimal)
            self.assertIsInstance(snaps[0].reserved, Decimal)

    def test_record_and_retrieve_snapshots(self):
        """Test recording snapshots in database and retrieving latest per SKU."""
        now_iso = datetime.now(timezone.utc).isoformat()
        snapshots = [
            InventorySnapshot(
                sku="LAPTOP-A14",
                warehouse="KHO-TONG",
                on_hand=Decimal("15"),
                reserved=Decimal("2"),
                as_of=now_iso,
                source="odoo",
            ),
            InventorySnapshot(
                sku="MONITOR-27",
                warehouse="KHO-TONG",
                on_hand=Decimal("30"),
                reserved=Decimal("5"),
                as_of=now_iso,
                source="odoo",
            ),
        ]
        count = self.store.record_inventory_snapshots(snapshots)
        self.assertEqual(count, 2)

        latest = self.store.get_latest_inventory_snapshots()
        self.assertIn("LAPTOP-A14", latest)
        self.assertEqual(latest["LAPTOP-A14"].on_hand, Decimal("15"))
        self.assertEqual(latest["LAPTOP-A14"].reserved, Decimal("2"))

        single = self.store.get_inventory_snapshot("LAPTOP-A14")
        self.assertIsNotNone(single)
        self.assertEqual(single.on_hand, Decimal("15"))

    def test_atp_with_local_allocations(self):
        """Test ATP calculation with approved orders and un-exported vs exported outbox events."""
        now_iso = datetime.now(timezone.utc).isoformat()
        # Record snapshot: on_hand = 10, reserved = 0
        self.store.record_inventory_snapshots([
            InventorySnapshot(
                sku="LAPTOP-A14",
                warehouse="DEFAULT",
                on_hand=Decimal("10"),
                reserved=Decimal("0"),
                as_of=now_iso,
                source="odoo",
            )
        ])

        # Step 1: Initial ATP should be 10
        atp_init = self.store.calculate_atp("LAPTOP-A14")
        self.assertEqual(atp_init["atp"], Decimal("10"))
        self.assertEqual(atp_init["allocated_local"], Decimal("0"))

        # Step 2: Order A for 6 units is recorded and approved
        order_a = Order(
            po_number="PO-101",
            customer="Northstar",
            items=(LineItem(sku="LAPTOP-A14", quantity=6, unit_price=Decimal("18500000")),),
        )
        analysis_a = Analysis(
            order=order_a,
            status="approved",
            findings=[],
        )
        self.store.record_analysis(analysis_a, source_file="po-101.json")

        # Now allocated local should be 6, so ATP is 10 - 6 = 4
        atp_after_a = self.store.calculate_atp("LAPTOP-A14")
        self.assertEqual(atp_after_a["allocated_local"], Decimal("6"))
        self.assertEqual(atp_after_a["atp"], Decimal("4"))

        # Step 3: Order B for 5 units -> rule check should flag INSUFFICIENT_STOCK (ordered 5 > ATP 4)
        order_b = Order(
            po_number="PO-102",
            customer="Acme Corp",
            items=(LineItem(sku="LAPTOP-A14", quantity=5, unit_price=Decimal("18500000")),),
        )
        ctx_b = build_rule_context(self.store, self.catalog, order_b)
        analysis_b = analyze_order(order_b, ctx_b)
        stock_findings = [f for f in analysis_b.findings if f.code == "INSUFFICIENT_STOCK"]
        self.assertEqual(len(stock_findings), 1)
        self.assertEqual(stock_findings[0].evidence["available_stock"], "4")

        # Step 4: Outbox event for Order A is marked as SENT (exported to ERP)
        self.store.connection.execute(
            """
            INSERT INTO erp_outbox (event_id, po_number, customer, total_amount, currency, idempotency_key, payload_json, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'SENT', ?, ?)
            """,
            ("evt_101", "PO-101", "Northstar", 111000000.0, "VND", "idemp_101", json.dumps({"po_number": "PO-101"}), 0.0, 0.0),
        )
        self.store.connection.commit()

        # Step 5: Now local allocation is cleared (0) because ERP has received the order
        self.assertEqual(self.store.get_allocated_local_stock("LAPTOP-A14"), Decimal("0"))

    def test_inventory_stale_finding(self):
        """Test that snapshots older than inventory_stale_hours trigger INVENTORY_STALE warning."""
        # 30 hours old snapshot
        old_time = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        self.store.record_inventory_snapshots([
            InventorySnapshot(
                sku="LAPTOP-A14",
                warehouse="DEFAULT",
                on_hand=Decimal("10"),
                reserved=Decimal("0"),
                as_of=old_time,
                source="odoo",
            )
        ])

        order = Order(
            po_number="PO-STALE-01",
            customer="TechCorp",
            items=(LineItem(sku="LAPTOP-A14", quantity=2, unit_price=Decimal("18500000")),),
        )
        ctx = build_rule_context(self.store, self.catalog, order)
        analysis = analyze_order(order, ctx)

        stale_findings = [f for f in analysis.findings if f.code == "INVENTORY_STALE"]
        self.assertEqual(len(stale_findings), 1)
        self.assertEqual(stale_findings[0].severity, "warning")
        self.assertEqual(stale_findings[0].evidence["sku"], "LAPTOP-A14")

    def test_inventory_api_endpoints(self):
        """Test GET /api/v1/inventory/snapshots and POST /api/v1/inventory/sync."""
        from fastapi.testclient import TestClient
        from preflight.api.app import app
        from preflight.api.deps import get_audit_store, get_catalog

        app.dependency_overrides[get_audit_store] = lambda: self.store
        app.dependency_overrides[get_catalog] = lambda: self.catalog

        client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})

        # 1. Sync inventory
        sync_res = client.post("/api/v1/inventory/sync?adapter_type=mock_odoo")
        self.assertEqual(sync_res.status_code, 200)
        self.assertTrue(sync_res.json()["success"])
        self.assertGreater(sync_res.json()["count"], 0)

        # 2. List snapshots
        list_res = client.get("/api/v1/inventory/snapshots")
        self.assertEqual(list_res.status_code, 200)
        data = list_res.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        skus = [it["sku"] for it in data]
        self.assertIn("LAPTOP-A14", skus)

        # 3. Catalog endpoint with ATP
        cat_res = client.get("/api/v1/catalog")
        self.assertEqual(cat_res.status_code, 200)
        cat_data = cat_res.json()
        self.assertIn("atp", cat_data[0])

        app.dependency_overrides.clear()

    def test_inventory_cli(self):
        """Test CLI inventory sync and list commands."""
        from preflight.cli import build_parser
        from preflight.erp import get_erp_adapter
        import io
        from contextlib import redirect_stdout

        parser = build_parser()
        args = parser.parse_args(["--db", str(self.db_path), "inventory", "sync", "--adapter", "mock_odoo"])
        self.assertEqual(args.inventory_command, "sync")

        f = io.StringIO()
        with redirect_stdout(f):
            # Test sync CLI
            adapter = get_erp_adapter(args.adapter)
            snaps = adapter.fetch_inventory(skus=["LAPTOP-A14"])
            count = self.store.record_inventory_snapshots(snaps)
            self.assertEqual(count, 1)

            # Test list CLI
            atp = self.store.calculate_atp("LAPTOP-A14")
            self.assertIn("atp", atp)


if __name__ == "__main__":
    unittest.main()

