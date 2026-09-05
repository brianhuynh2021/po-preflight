"""Regression tests for upgrading databases created by older releases.

New installs get their schema from SQLITE_SCHEMA, so a column added there is
present immediately and every fresh-database test passes. Databases created by
an earlier release keep their original layout, because
`CREATE TABLE IF NOT EXISTS` never alters an existing table. Opening such a
database with newer code used to fail on the first customer insert with:

    OperationalError: table customers has no column named contact_emails

These tests build a genuine pre-upgrade database and reopen it with the current
store, which is the path a pilot deployment takes when it is updated.
"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from preflight.models import CustomerMaster
from preflight.store import AuditStore

# The `customers` table exactly as it shipped before `contact_emails` existed.
LEGACY_CUSTOMERS_TABLE = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    tax_code TEXT,
    tier TEXT NOT NULL DEFAULT 'STANDARD',
    created_at TEXT NOT NULL
);
"""


class TestLegacyDatabaseUpgrade(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "legacy.db"

        # Simulate a database created by an older release: the customers table
        # exists, so executescript() will leave it alone, and it predates the
        # contact_emails column.
        conn = sqlite3.connect(self.db_path)
        conn.executescript(LEGACY_CUSTOMERS_TABLE)
        conn.execute(
            "INSERT INTO customers (code, name, normalized_name, tax_code, tier, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            ("CUST-LEGACY", "Khách Hàng Cũ", "khach hang cu", "0101234567", "STANDARD", "2026-01-01T00:00:00+00:00"),
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_legacy_customers_table_gains_contact_emails_column(self):
        """Opening a pre-upgrade database backfills the missing column."""
        with sqlite3.connect(self.db_path) as conn:
            before = {r[1] for r in conn.execute("PRAGMA table_info(customers)")}
        self.assertNotIn("contact_emails", before, "fixture should start without the column")

        AuditStore(self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            after = {r[1] for r in conn.execute("PRAGMA table_info(customers)")}
        self.assertIn("contact_emails", after)

    def test_create_customer_succeeds_on_upgraded_legacy_database(self):
        """The insert that used to raise OperationalError now works."""
        store = AuditStore(self.db_path)

        created = store.create_customer(
            CustomerMaster(
                code="CUST-NEW",
                name="Công ty TNHH Thử Nghiệm",
                normalized_name="cong ty tnhh thu nghiem",
                contact_emails=["ke.toan@thunghiem.vn"],
            )
        )

        self.assertEqual(created.code, "CUST-NEW")
        fetched = store.get_customer_by_normalized_name("cong ty tnhh thu nghiem")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.contact_emails, ["ke.toan@thunghiem.vn"])

    def test_existing_legacy_rows_are_preserved(self):
        """Backfilling the column must not disturb data already in the table."""
        store = AuditStore(self.db_path)

        legacy = store.get_customer_by_normalized_name("khach hang cu")
        self.assertIsNotNone(legacy)
        self.assertEqual(legacy.code, "CUST-LEGACY")
        self.assertEqual(legacy.tax_code, "0101234567")
        self.assertEqual(legacy.contact_emails, [])


if __name__ == "__main__":
    unittest.main()
