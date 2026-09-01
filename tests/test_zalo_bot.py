from __future__ import annotations

import hashlib
import hmac
import json
import tempfile
import unittest
from decimal import Decimal

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.bot.zalo import ZaloBotService, format_zalo_notification
from preflight.models import Analysis, LineItem, Order
from preflight.security.rate_limiter import global_rate_limiter
from preflight.store import AuditStore


class TestZaloBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})

    def setUp(self):
        global_rate_limiter.reset()


    def test_format_zalo_notification(self):
        """Test formatting Zalo OA rich interactive card."""
        order_dict = {
            "po_number": "PO-ZALO-9988",
            "customer": "Vingroup Infrastructure",
            "status": "review_required",
            "risk_level": "HIGH",
            "total_value": 108440000,
            "currency": "VND",
            "findings": [{"code": "UNKNOWN_SKU"}],
        }
        card = format_zalo_notification(order_dict, web_base_url="https://portal.enterprise.vn")
        msg = card["message"]["attachment"]["payload"]
        self.assertIn("PO-ZALO-9988", msg["title"])
        self.assertIn("Vingroup Infrastructure", msg["subtitle"])
        self.assertEqual(len(msg["buttons"]), 3)
        self.assertEqual(msg["buttons"][0]["payload"], "APPROVE:PO-ZALO-9988")

    def test_zalo_service_dry_run_dispatch(self):
        """Test ZaloBotService dry run dispatch."""
        service = ZaloBotService(dry_run=True)
        res = service.send_order_alert({"po_number": "PO-ZALO-1122"})
        self.assertTrue(res.success)
        self.assertEqual(res.channel, "zalo")
        self.assertTrue(res.dry_run)

    def test_zalo_webhook_signature_and_event_processing(self):
        """Test Zalo HMAC-SHA256 signature verification and order approval processing."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tf:
            store = AuditStore(tf.name)
            order = Order(
                po_number="PO-ZALO-5566",
                customer="Test Customer",
                items=(LineItem(sku="LAPTOP-A14", quantity=1, unit_price=Decimal("18500000")),),
            )
            analysis = Analysis(order=order, findings=[], status="review_required")
            store.record_analysis(analysis, "test.json")

            secret_key = "zalo_test_secret_key_123"
            app_id = "123456789"
            service = ZaloBotService(app_id=app_id, secret_key=secret_key, store=store)

            raw_body = json.dumps({"event_name": "user_send_text", "message": {"text": "APPROVE:PO-ZALO-5566"}}).encode("utf-8")
            timestamp = "1725200000"

            # Compute valid signature
            data_to_sign = f"{app_id}{raw_body.decode('utf-8')}{timestamp}{secret_key}".encode("utf-8")
            valid_sig = hashlib.sha256(data_to_sign).hexdigest()

            # Verify signature
            self.assertTrue(service.verify_webhook_signature(raw_body, timestamp, valid_sig))
            self.assertFalse(service.verify_webhook_signature(raw_body, timestamp, "invalid_sig_123"))

            # Process event
            event_data = json.loads(raw_body.decode("utf-8"))
            result = service.process_webhook_event(event_data)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["action"], "approved")

            # Check decision in store
            history = store.history("PO-ZALO-5566")
            self.assertEqual(len(history["decisions"]), 1)
            self.assertEqual(history["decisions"][0]["decision"], "approved")

    def test_zalo_webhook_endpoint(self):
        """Test POST /api/v1/bot/zalo/webhook HTTP endpoint."""
        payload = {"event_name": "user_click_button", "message": {"text": "APPROVE:PO-2026-1002"}}
        res = self.client.post("/api/v1/bot/zalo/webhook", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])


if __name__ == "__main__":
    unittest.main()
