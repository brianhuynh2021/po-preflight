import os
import unittest
from decimal import Decimal
from pathlib import Path

from preflight.api.errors import ConfigurationError
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

    def test_factory_resolves_sqlite_from_path(self):
        """Test factory creates SQLite AuditStore when given path or sqlite:/// URL."""
        store1 = create_audit_store(self.sqlite_db)
        self.assertIsInstance(store1, AuditStore)
        store1.close()

        store2 = create_audit_store(f"sqlite:///{self.sqlite_db}")
        self.assertIsInstance(store2, AuditStore)
        store2.close()

    def test_factory_raises_configuration_error_on_unreachable_postgres(self):
        """Test that PostgresAuditStore fails closed with ConfigurationError instead of falling back to SQLite."""
        pg_url = "postgresql://invalid_user:invalid_pass@127.0.0.1:59999/nonexistent_db"
        with self.assertRaises(ConfigurationError):
            create_audit_store(pg_url)

        with self.assertRaises(ConfigurationError):
            create_outbox_store(pg_url)

    def test_postgres_store_live_when_configured(self):
        """Test PostgresAuditStore live operations only when TEST_DATABASE_URL is provided."""
        pg_url = os.getenv("TEST_DATABASE_URL")
        if not pg_url:
            self.skipTest("TEST_DATABASE_URL not set; skipping live PostgreSQL backend test.")

        pg_store = PostgresAuditStore(pg_url)
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

    def test_postgres_outbox_store_live_when_configured(self):
        """Test PostgresOutboxStore live operations only when TEST_DATABASE_URL is provided."""
        pg_url = os.getenv("TEST_DATABASE_URL")
        if not pg_url:
            self.skipTest("TEST_DATABASE_URL not set; skipping live PostgreSQL outbox test.")

        outbox = PostgresOutboxStore(pg_url)
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

