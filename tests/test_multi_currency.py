from __future__ import annotations

import json
import unittest
from decimal import Decimal

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.bot.telegram import format_currency, format_telegram_po_card
from preflight.parsers import parse_order_content


class TestMultiCurrencySupport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_currency_formatter(self):
        """Test formatting standards for different currencies."""
        self.assertEqual(format_currency(18500000, "VND"), "18,500,000 VND")
        self.assertEqual(format_currency(850.50, "USD"), "$850.50")
        self.assertEqual(format_currency(120.00, "EUR"), "€120.00")
        self.assertEqual(format_currency(95.00, "GBP"), "£95.00")

    def test_telegram_card_multi_currency(self):
        """Test Telegram card displays dynamic currency symbol."""
        usd_order = {
            "po_number": "PO-10433",
            "customer": "Silicon Valley Tech",
            "status": "ready_for_approval",
            "risk_level": "LOW",
            "total_value": 2550.00,
            "currency": "USD",
            "findings": [],
            "line_items": [
                {"sku": "LAPTOP-A14", "quantity": 3, "unit_price": 850.00},
            ],
        }
        card_text = format_telegram_po_card(usd_order)
        self.assertIn("$2,550.00", card_text)
        self.assertIn("$850.00", card_text)

    def test_parser_preserves_currency(self):
        """Test parser accurately extracts and preserves currency code."""
        json_str = json.dumps(
            {
                "po_number": "PO-EUR-01",
                "customer": "Berlin Logistics GmbH",
                "currency": "EUR",
                "items": [
                    {"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 750},
                ],
            }
        )
        order = parse_order_content(json_str, suffix=".json")
        self.assertEqual(order.currency, "EUR")
        self.assertEqual(order.total, Decimal("750"))


if __name__ == "__main__":
    unittest.main()
