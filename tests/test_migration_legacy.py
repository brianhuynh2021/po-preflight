import os
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import create_engine, select, func
from preflight.db.models import metadata, orders, order_lines, findings, customers, organizations


class TestMigrationLegacy(unittest.TestCase):
    def test_fresh_sqlite_migration(self):
        """Test running Alembic upgrade head on a brand new SQLite database."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "fresh.db"
            env = os.environ.copy()
            env["DATABASE_URL"] = f"sqlite:///{db_path}"

            res = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, f"Alembic migration failed: {res.stderr}")

            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                from sqlalchemy import inspect
                insp = inspect(conn)
                tables = insp.get_table_names()
                self.assertIn("orders", tables)
                self.assertIn("order_lines", tables)
                self.assertIn("customers", tables)
                self.assertIn("findings", tables)
                self.assertIn("organizations", tables)

    def test_legacy_database_upgrade(self):
        """Test upgrading a database containing legacy analyses schema."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "legacy.db"

            # Create legacy analyses table and insert records
            raw_conn = sqlite3.connect(str(db_path))
            cur = raw_conn.cursor()
            cur.execute("""
                CREATE TABLE analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_number TEXT NOT NULL,
                    customer TEXT NOT NULL,
                    status TEXT NOT NULL,
                    findings_json TEXT NOT NULL,
                    order_json TEXT NOT NULL,
                    raw_file TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                INSERT INTO analyses (po_number, customer, status, findings_json, order_json, raw_file, created_at)
                VALUES (
                    'PO-LEGACY-01',
                    'Công ty ABC',
                    'ready_for_approval',
                    '[]',
                    '{"po_number": "PO-LEGACY-01", "customer": "Công ty ABC", "currency": "VND", "items": [{"sku": "LAPTOP-A14", "quantity": 2, "unit_price": 18500000}]}',
                    'legacy.json',
                    '2026-09-01T10:00:00Z'
                )
            """)
            raw_conn.commit()
            raw_conn.close()

            env = os.environ.copy()
            env["DATABASE_URL"] = f"sqlite:///{db_path}"

            res = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, f"Migration of legacy DB failed: {res.stderr}")

            # Verify migrated data in relational tables
            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                ord_count = conn.execute(select(func.count(orders.c.id))).scalar()
                self.assertEqual(ord_count, 1)

                ord_row = conn.execute(select(orders).where(orders.c.po_number == "PO-LEGACY-01")).fetchone()
                self.assertIsNotNone(ord_row)
                self.assertEqual(ord_row._mapping["rule_status"], "ready_for_approval")

                lines_count = conn.execute(select(func.count(order_lines.c.id))).scalar()
                self.assertEqual(lines_count, 1)

                cust_row = conn.execute(select(customers).where(customers.c.id == ord_row._mapping["customer_id"])).fetchone()
                self.assertIsNotNone(cust_row)
                self.assertEqual(cust_row._mapping["name"], "Công ty ABC")


if __name__ == "__main__":
    unittest.main()
