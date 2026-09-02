import os
import unittest
from decimal import Decimal
from pathlib import Path

from preflight.erp.outbox import (
    OutboxStore,
    PostgresOutboxStore,
    create_outbox_store,
)
from preflight.models import Analysis, LineItem, Order, Product
from preflight.rules import analyze_order
from preflight.store import (
    AuditStore,
    PostgresAuditStore,
    create_audit_store,
)


class TestDualBackendDatabase(unittest.TestCase):
    def setUp(self):
        self.sqlite_db = "runtime/test_dual_backend.db"
        Path(self.sqlite_db).unlink(missing_ok=True)
        self.catalog = {
            "LAPTOP-A14": Product(
                sku="LAPTOP-A14",
                name="A14 Laptop",
                unit_price=Decimal("18500000"),
                stock=10,
                active=True,
            )
        }

    def tearDown(self):
        Path(self.sqlite_db).unlink(missing_ok=True)
        Path("runtime/pg_fallback.db").unlink(missing_ok=True)
        Path("runtime/pg_fallback_outbox.db").unlink(missing_ok=True)

    def test_factory_resolves_sqlite_from_path(self):
        """Test factory creates SQLite AuditStore when given path or sqlite:/// URL."""
        store1 = create_audit_store(self.sqlite_db)
        self.assertIsInstance(store1, AuditStore)
        store1.close()

        store2 = create_audit_store(f"sqlite:///{self.sqlite_db}")
        self.assertIsInstance(store2, AuditStore)
        store2.close()

    def test_factory_resolves_postgres_from_url(self):
        """Test factory creates PostgresAuditStore and PostgresOutboxStore from postgresql:// URL."""
        pg_url = "postgresql://user:pass@localhost:5432/preflight_db"
        store = create_audit_store(pg_url)
        self.assertIsInstance(store, PostgresAuditStore)
        self.assertEqual(store.database_url, pg_url)
        self.assertEqual(store.pool_size, 20)
        self.assertEqual(store.max_overflow, 10)
        store.close()

        outbox = create_outbox_store(pg_url)
        self.assertIsInstance(outbox, PostgresOutboxStore)
        self.assertEqual(outbox.database_url, pg_url)
        outbox.close()

    def test_postgres_store_interface_and_emulation(self):
        """Test PostgresAuditStore conforms to BaseAuditStore and performs CRUD operations."""
        pg_store = PostgresAuditStore("postgresql://test:test@localhost:5432/testdb")
        order = Order(
            po_number="PO-PG-TEST-001",
            customer="Enterprise Corp",
            items=(LineItem(sku="LAPTOP-A14", quantity=1, unit_price=Decimal("18500000")),),
            currency="VND",
        )
        analysis = analyze_order(order, self.catalog)
        order_id = pg_store.record_analysis(analysis, "test_pg.json")
        self.assertGreaterEqual(order_id, 1)

        # Has PO
        self.assertTrue(pg_store.has_po("PO-PG-TEST-001"))

        # Record Decision
        d_id = pg_store.record_decision(
            po_number="PO-PG-TEST-001",
            decision="approved",
            actor="pg_admin",
            note="Approved via Enterprise Postgres Store",
        )
        self.assertGreaterEqual(d_id, 1)

        # Retrieve Order and History
        order_data = pg_store.get_order(order_id)
        self.assertIsNotNone(order_data)
        self.assertEqual(order_data["po_number"], "PO-PG-TEST-001")
        self.assertEqual(len(order_data["decisions"]), 1)

        # Active Learning Alias
        pg_store.learn_alias("Enterprise Corp", "laptop sieu mong", "LAPTOP-A14")
        alias = pg_store.get_customer_alias("Enterprise Corp", "laptop sieu mong")
        self.assertEqual(alias, "LAPTOP-A14")

        # Dashboard stats
        stats = pg_store.get_dashboard_stats()
        self.assertGreaterEqual(stats["total_orders"], 1)

        pg_store.close()

    def test_postgres_outbox_store_interface_and_emulation(self):
        """Test PostgresOutboxStore conforms to BaseOutboxStore and manages ERP outbox queue."""
        outbox = PostgresOutboxStore("postgresql://test:test@localhost:5432/testdb")
        payload = outbox.enqueue_order(
            po_number="PO-PG-OUTBOX-1",
            customer="Enterprise Corp",
            items=[{"sku": "LAPTOP-A14", "quantity": 1}],
            total_amount=Decimal("18500000"),
            currency="VND",
        )
        self.assertIsNotNone(payload.idempotency_key)
        self.assertEqual(payload.po_number, "PO-PG-OUTBOX-1")

        # Pending fetch
        pending = outbox.fetch_pending(limit=5)
        self.assertTrue(any(p.po_number == "PO-PG-OUTBOX-1" for p in pending))

        # Stats (fetch_pending moved event to PROCESSING status)
        stats = outbox.get_stats()
        self.assertGreaterEqual(stats.processing_count, 1)

        outbox.close()


if __name__ == "__main__":
    unittest.main()
