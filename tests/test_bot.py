from __future__ import annotations

import unittest
from decimal import Decimal

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.bot.telegram import TelegramBotService, build_approval_inline_keyboard, format_telegram_po_card
from preflight.bot.zalo import format_zalo_notification
from preflight.store import AuditStore


class TestBotServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.sample_order = {
            "id": 1,
            "po_number": "PO-TEST-99",
            "customer": "Apex Global",
            "status": "review_required",
            "risk_level": "MEDIUM",
            "total_value": 35000000,
            "currency": "VND",
            "line_items": [
                {"sku": "LAPTOP-A14", "quantity": 2, "unit_price": 17500000},
            ],
            "findings": [
                {
                    "severity": "warning",
                    "code": "PRICE_MISMATCH",
                    "message": "SKU LAPTOP-A14: PO price 17,500,000 vs Catalog 18,500,000",
                }
            ],
        }

    def test_telegram_card_formatting(self):
        card = format_telegram_po_card(self.sample_order)
        self.assertIn("PO PREFLIGHT ALERT", card)
        self.assertIn("PO-TEST-99", card)
        self.assertIn("Apex Global", card)
        self.assertIn("35,000,000 VND", card)
        self.assertIn("PRICE_MISMATCH", card)
        self.assertIn("LAPTOP-A14", card)

    def test_inline_keyboard_builder(self):
        kb = build_approval_inline_keyboard(1)
        self.assertIn("inline_keyboard", kb)
        buttons = kb["inline_keyboard"]
        self.assertEqual(len(buttons), 2)
        # Row 1
        self.assertEqual(buttons[0][0]["callback_data"], "approve:1")
        self.assertEqual(buttons[0][1]["callback_data"], "reject:1")
        # Row 2
        self.assertEqual(buttons[1][0]["callback_data"], "request_changes:1")

    def test_telegram_bot_service_dry_run(self):
        bot = TelegramBotService(token=None, chat_id=None)
        res = bot.send_order_alert(self.sample_order)
        self.assertTrue(res.success)
        self.assertTrue(res.dry_run)
        self.assertEqual(res.channel, "telegram")
        self.assertEqual(res.order_id, 1)

    def test_telegram_callback_handler_decision(self):
        store = AuditStore(":memory:")
        bot = TelegramBotService(store=store)

        res = bot.handle_callback_action("approve:1", from_username="brianhuynh")
        self.assertTrue(res["success"])
        self.assertEqual(res["decision"], "APPROVED")
        self.assertEqual(res["decided_by"], "Telegram:@brianhuynh")

    def test_zalo_notification_formatter(self):
        payload = format_zalo_notification(self.sample_order)
        self.assertEqual(payload["template_id"], "PO_PREFLIGHT_ALERT_TEMPLATE")
        self.assertEqual(payload["template_data"]["order_code"], "PO-TEST-99")
        self.assertEqual(payload["template_data"]["customer_name"], "Apex Global")

    def test_api_bot_status_endpoint(self):
        response = self.client.get("/api/v1/bot/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("telegram_enabled", data)
        self.assertIn("webhook_url", data)

    def test_api_telegram_webhook_callback(self):
        payload = {
            "update_id": 998877,
            "callback_query": {
                "id": "cq_12345",
                "from": {"id": 1001, "username": "chief_buyer"},
                "data": "approve:1",
            },
        }
        response = self.client.post("/api/v1/bot/telegram/webhook", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["handled_event"], "callback_query")
        self.assertEqual(data["result"]["decision"], "APPROVED")

    def test_api_telegram_notify_order_endpoint(self):
        response = self.client.post("/api/v1/bot/telegram/notify/1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["channel"], "telegram")


if __name__ == "__main__":
    unittest.main()
