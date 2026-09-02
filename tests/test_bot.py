import os
import tempfile
import unittest
from decimal import Decimal
from unittest.mock import patch

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.api.deps import get_audit_store, get_store
from preflight.bot.telegram import TelegramBotService, build_approval_inline_keyboard, format_telegram_po_card
from preflight.bot.zalo import format_zalo_notification
from preflight.models import Analysis, LineItem, Order
from preflight.security.rate_limiter import global_rate_limiter
from preflight.store import AuditStore


class TestBotServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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

    def setUp(self):
        global_rate_limiter.reset()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = AuditStore(f"{self.temp_dir.name}/test_bot.db")
        order = Order(
            po_number="PO-TEST-99",
            customer="Apex Global",
            items=(LineItem(sku="LAPTOP-A14", quantity=2, unit_price=Decimal("17500000")),),
        )

        self.store.record_analysis(Analysis(order=order, findings=[], status="review_required"), "test.json")
        app.dependency_overrides[get_store] = lambda: self.store
        app.dependency_overrides[get_audit_store] = lambda: self.store
        self.client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})

    def tearDown(self):
        app.dependency_overrides.clear()
        self.store.close()
        self.temp_dir.cleanup()



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
        bot = TelegramBotService(token=None, chat_id=None, dry_run=True)
        res = bot.send_order_alert(self.sample_order)
        self.assertTrue(res.success)
        self.assertTrue(res.dry_run)
        self.assertEqual(res.channel, "telegram")
        self.assertEqual(res.order_id, 1)

    def test_telegram_callback_handler_decision(self):
        store = AuditStore(":memory:")
        order = Order(
            po_number="PO-TEST-001",
            customer="Apex Global",
            items=(LineItem(sku="SKU-1", quantity=1, unit_price=Decimal("100")),),
        )

        store.record_analysis(Analysis(order=order, findings=[], status="review_required"), "test.json")
        store.upsert_channel_identity("telegram", "1001", "brianhuynh", "Brian Huynh", "MANAGER")
        bot = TelegramBotService(store=store)

        res = bot.handle_callback_action("approve:1", from_user_id="1001", from_username="brianhuynh")
        self.assertTrue(res["success"])
        self.assertEqual(res["decision"], "APPROVED")
        self.assertEqual(res["decided_by"], "telegram:brianhuynh")

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
        self.store.upsert_channel_identity("telegram", "1001", "chief_buyer", "Chief Buyer", "MANAGER")
        payload = {
            "update_id": 998877,
            "callback_query": {
                "id": "cq_12345",
                "from": {"id": 1001, "username": "chief_buyer"},
                "data": "approve:1",
            },
        }
        with patch.dict(os.environ, {"TELEGRAM_WEBHOOK_SECRET": "test_secret_123"}, clear=False):
            response = self.client.post(
                "/api/v1/bot/telegram/webhook",
                json=payload,
                headers={"X-Telegram-Bot-Api-Secret-Token": "test_secret_123"},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["ok"])
            self.assertEqual(data["handled_event"], "callback_query")
            self.assertEqual(data["result"]["decision"], "APPROVED")

    def test_api_telegram_notify_order_endpoint(self):
        with patch.dict(os.environ, {"TELEGRAM_DRY_RUN": "true"}):
            response = self.client.post(
                "/api/v1/bot/telegram/notify/1",
                headers={"X-API-Key": "pf_dev_mgr_8802"},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["channel"], "telegram")



if __name__ == "__main__":
    unittest.main()
