from __future__ import annotations

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from preflight.catalog import load_catalog
from preflight.models import LineItem, Order, Product
from preflight.parsers import OrderParseError, parse_order, parse_text
from preflight.rules import analyze_order
from preflight.store import AuditStore


class ParserTests(unittest.TestCase):
    def test_parse_json_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "order.json"
            path.write_text(
                json.dumps(
                    {
                        "po_number": "PO-1",
                        "customer": "Acme",
                        "items": [
                            {"sku": "abc", "quantity": 2, "unit_price": 100}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            order = parse_order(path)
        self.assertEqual(order.po_number, "PO-1")
        self.assertEqual(order.items[0].sku, "ABC")
        self.assertEqual(order.total, Decimal("200"))

    def test_parse_text_order(self) -> None:
        order = parse_text(
            """
            PO_NUMBER: PO-2
            CUSTOMER: Contoso
            CURRENCY: USD
            SKU | QTY | UNIT_PRICE
            SKU-1 | 3 | 12.50
            """
        )
        self.assertEqual(order.currency, "USD")
        self.assertEqual(order.total, Decimal("37.50"))

    def test_reject_empty_order(self) -> None:
        with self.assertRaises(OrderParseError):
            parse_text("PO_NUMBER: PO-3\nCUSTOMER: Acme")


class RuleEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = {
            "SKU-1": Product("SKU-1", "Product", Decimal("100"), 5, True),
            "SKU-2": Product("SKU-2", "Inactive", Decimal("50"), 10, False),
        }

    def test_clean_order_is_ready(self) -> None:
        order = Order(
            "PO-CLEAN",
            "Acme",
            (LineItem("SKU-1", 2, Decimal("100")),),
        )
        analysis = analyze_order(order, self.catalog)
        self.assertEqual(analysis.status, "ready_for_approval")
        self.assertEqual(analysis.findings, [])

    def test_price_stock_and_unknown_sku(self) -> None:
        order = Order(
            "PO-BAD",
            "Acme",
            (
                LineItem("SKU-1", 8, Decimal("90")),
                LineItem("MISSING", 1, Decimal("10")),
            ),
        )
        analysis = analyze_order(order, self.catalog)
        codes = {finding.code for finding in analysis.findings}
        self.assertEqual(analysis.status, "blocked")
        self.assertEqual(
            codes, {"INSUFFICIENT_STOCK", "PRICE_MISMATCH", "UNKNOWN_SKU"}
        )


class AuditStoreTests(unittest.TestCase):
    def test_analysis_duplicate_and_decision_history(self) -> None:
        order = Order(
            "PO-AUDIT",
            "Acme",
            (LineItem("SKU-1", 1, Decimal("100")),),
        )
        catalog = {
            "SKU-1": Product("SKU-1", "Product", Decimal("100"), 5, True)
        }
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "audit.db"
            with AuditStore(db) as store:
                first = analyze_order(order, catalog, duplicate=store.has_po(order.po_number))
                store.record_analysis(first, "order.json")
                self.assertTrue(store.has_po(order.po_number))

                second = analyze_order(order, catalog, duplicate=store.has_po(order.po_number))
                self.assertEqual(second.status, "blocked")
                self.assertIn("DUPLICATE_PO", {f.code for f in second.findings})

                store.record_decision(
                    order.po_number, "approved", "U123", "Reviewed in test"
                )
                history = store.history(order.po_number)
                self.assertEqual(len(history["analyses"]), 1)
                self.assertEqual(history["decisions"][0]["decision"], "approved")


class CatalogTests(unittest.TestCase):
    def test_load_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.csv"
            path.write_text(
                "sku,name,unit_price,stock,active\nSKU-1,Item,100,5,true\n",
                encoding="utf-8",
            )
            catalog = load_catalog(path)
        self.assertEqual(catalog["SKU-1"].stock, 5)


if __name__ == "__main__":
    unittest.main()
