from __future__ import annotations

import json
import os
import time
import unittest
from datetime import datetime, UTC, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from preflight.api.app import app
from preflight.api.deps import get_store
from preflight.bot.schemas import BotNotificationResult
from preflight.bot.telegram import TelegramBotService, format_telegram_po_card
from preflight.bot.zalo import ZaloBotService, format_zalo_notification
from preflight.jobs.definitions import escalation_check
from preflight.models import Analysis, Finding, LineItem, Order
from preflight.security.rbac import Role, UserPrincipal
from preflight.store import AuditStore


class TestPromptC4ChannelsLive(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.store = AuditStore(":memory:")
        app.dependency_overrides[get_store] = lambda: self.store
        self.client = TestClient(app)

        os.environ["TELEGRAM_WEBHOOK_SECRET"] = "test_tg_secret"
        os.environ["ZALO_SECRET_KEY"] = "secret_xyz"
        os.environ["ZALO_APP_ID"] = "app_123"

        # Seed test order with warning-only for approval
        self.order = Order(
            po_number="PO-C4-001",
            customer="Cong Ty TNHH Minh Phat",
            items=[
                LineItem(sku="SKU-A", quantity=10, unit_price=Decimal("50000"), uom="CAI", description="San pham A"),
                LineItem(sku="SKU-B", quantity=5, unit_price=Decimal("100000"), uom="CAI", description="San pham B"),
            ],
            currency="VND",
        )
        self.findings = [
            Finding(code="PRICE_MISMATCH", message="Gia ban 50,000 VND thap hon gia niem yet", severity="error"),
            Finding(code="INSUFFICIENT_STOCK", message="Ton kho chi con 3 cai", severity="warning"),
            Finding(code="INVALID_PACK_SIZE", message="Quy cach dong goi le", severity="warning"),
        ]
        self.analysis = Analysis(
            order=self.order,
            findings=self.findings,
            status="review_required",
        )
        self.order_id = self.store.record_analysis(self.analysis, source_file="po_c4.pdf")

        # Second order with only warnings (can be approved over warnings with note)
        self.approvable_order = Order(
            po_number="PO-C4-002",
            customer="Cong Ty TNHH Sao Mai",
            items=[
                LineItem(sku="SKU-A", quantity=2, unit_price=Decimal("50000"), uom="CAI", description="San pham A"),
            ],
            currency="VND",
        )
        self.approvable_analysis = Analysis(
            order=self.approvable_order,
            findings=[Finding(code="INSUFFICIENT_STOCK", message="Ton kho chi con 1", severity="warning")],
            status="review_required",
        )
        self.approvable_order_id = self.store.record_analysis(self.approvable_analysis, source_file="po_c4_2.pdf")

    def tearDown(self):
        app.dependency_overrides.clear()
        self.store.close()
        os.environ.pop("TELEGRAM_WEBHOOK_SECRET", None)
        os.environ.pop("ZALO_SECRET_KEY", None)
        os.environ.pop("ZALO_APP_ID", None)

    def test_telegram_rich_po_card_formatting(self):
        """Notification card must show grand_total after tax, severity counts, Vietnamese findings, and deep-link."""
        order_dict = self.store.get_order(self.order_id)
        card_text = format_telegram_po_card(order_dict, web_base_url="https://preflight.company.vn")

        # 1. Total after tax (10% VAT on 1,000,000 = 1,100,000)
        self.assertIn("1,100,000 VND", card_text)
        self.assertIn("Tổng thanh toán (sau thuế)", card_text)

        # 2. Severity breakdown
        self.assertIn("1 lỗi", card_text)
        self.assertIn("2 cảnh báo", card_text)

        # 3. Vietnamese finding title
        self.assertIn("Lệch giá so với bảng giá niêm yết", card_text)

        # 4. Deep link
        self.assertIn("https://preflight.company.vn/orders?search=PO-C4-001", card_text)

    def test_zalo_rich_po_card_formatting(self):
        """Zalo notification card payload must contain VAT amount, severity counts, and Vietnamese findings."""
        order_dict = self.store.get_order(self.order_id)
        zalo_payload = format_zalo_notification(order_dict, web_base_url="https://preflight.company.vn")

        template_data = zalo_payload["template_data"]
        self.assertEqual(template_data["total_amount"], "1,100,000 VND")
        self.assertEqual(template_data["error_count"], "1")
        self.assertEqual(template_data["warning_count"], "2")
        self.assertIn("Lệch giá niêm yết", template_data["findings_vietnamese"])
        self.assertEqual(template_data["action_url"], "https://preflight.company.vn/orders?search=PO-C4-001")

    def test_telegram_callback_answers_query_and_edits_message(self):
        """Clicking action button must call answerCallbackQuery (no infinite spinning) and editMessageText."""
        # Link manager telegram ID first
        self.store.upsert_channel_identity(
            channel="telegram",
            external_id="123456789",
            user_id="nguyen_a",
            display_name="Nguyen A",
            role="MANAGER",
        )

        bot = TelegramBotService(token="12345:dummy_token", store=self.store)

        with patch.object(bot, "answer_callback_query") as mock_answer, \
             patch.object(bot, "edit_message_text") as mock_edit:

            result = bot.handle_callback_action(
                callback_data=f"approve:{self.approvable_order_id}",
                from_user_id="123456789",
                callback_query_id="query_abc_123",
                chat_id="chat_999",
                message_id=456,
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["decision"], "APPROVED")

            # Must invoke answer_callback_query so button doesn't spin
            mock_answer.assert_called_once_with("query_abc_123", text="✅ Đã duyệt đơn thành công!", show_alert=False)

            # Must edit message text to show decision actor and timestamp
            mock_edit.assert_called_once()
            args, kwargs = mock_edit.call_args
            self.assertEqual(args[0], "chat_999")
            self.assertEqual(args[1], 456)
            self.assertIn("Đã duyệt bởi Nguyen A", kwargs["text"])

    def test_account_linking_flow_via_telegram_link_command(self):
        """Self-service linking with 10-min code via POST /link-code and /link <token> Telegram webhook."""
        # 1. Generate linking code for a Sales Manager via X-API-Key
        resp = self.client.post("/api/v1/bot/link-code", headers={"X-API-Key": "pf_dev_mgr_8802"})
        self.assertEqual(resp.status_code, 200)
        code = resp.json()["code"]
        self.assertEqual(len(code), 6)

        # 2. Telegram webhook receives /link <code_generated>
        webhook_payload = {
            "update_id": 10001,
            "message": {
                "message_id": 1,
                "chat": {"id": 8888},
                "from": {"id": 987654, "first_name": "Trịnh B"},
                "text": f"/link {code}",
            },
        }
        res = self.client.post(
            "/api/v1/bot/telegram/webhook",
            json=webhook_payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "test_tg_secret"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("linked"))
        self.assertEqual(data.get("user_id"), "operations_manager")
        self.assertIn("operations_manager", data.get("reply", ""))

        # 3. Verify channel identity was persisted
        identity = self.store.get_channel_identity("telegram", "987654")
        self.assertIsNotNone(identity)
        self.assertEqual(identity["user_id"], "operations_manager")
        self.assertEqual(identity["role"], "MANAGER")

        # 4. Attempting to re-use the same code must fail
        res_reuse = self.client.post(
            "/api/v1/bot/telegram/webhook",
            json=webhook_payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "test_tg_secret"},
        )
        self.assertFalse(res_reuse.json().get("linked"))
        self.assertEqual(res_reuse.json().get("error"), "INVALID_CODE")

    def test_account_linking_expired_code(self):
        """Expired code (> 10 mins) must be rejected with Vietnamese message."""
        # Create an expired code in store directly
        expired_code = self.store.create_channel_link_code(
            user_id="user_test",
            display_name="User Test",
            role="MANAGER",
            expires_in_seconds=-10,  # expired 10 seconds ago
        )
        webhook_payload = {
            "update_id": 10002,
            "message": {
                "message_id": 2,
                "chat": {"id": 8888},
                "from": {"id": 999999},
                "text": f"/link {expired_code}",
            },
        }
        res = self.client.post(
            "/api/v1/bot/telegram/webhook",
            json=webhook_payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "test_tg_secret"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json().get("linked"))
        self.assertEqual(res.json().get("error"), "EXPIRED_CODE")
        self.assertIn("hết hạn", res.json().get("reply", ""))

    def test_zalo_webhook_anti_replay_protection(self):
        """Zalo webhook must reject timestamps > 5 mins off and duplicate event_ids."""
        # 1. Timestamp > 5 minutes in the past
        stale_ts = str(int(time.time() - 400))  # 6.6 minutes ago
        req_body = json.dumps({"event_id": "evt_test_1"}).encode("utf-8")

        with patch.object(ZaloBotService, "verify_webhook_signature", return_value=True):
            # Stale timestamp
            res_stale = self.client.post(
                "/api/v1/bot/zalo/webhook",
                content=req_body,
                headers={"X-Zalo-Signature": "sig", "X-Zalo-Timestamp": stale_ts},
            )
            self.assertEqual(res_stale.status_code, 400)
            self.assertIn("±5 minutes", res_stale.json()["detail"])

            # Fresh timestamp
            fresh_ts = str(int(time.time()))
            res_fresh = self.client.post(
                "/api/v1/bot/zalo/webhook",
                content=req_body,
                headers={"X-Zalo-Signature": "sig", "X-Zalo-Timestamp": fresh_ts},
            )
            self.assertEqual(res_fresh.status_code, 200)

            # Replay with SAME event_id
            res_replay = self.client.post(
                "/api/v1/bot/zalo/webhook",
                content=req_body,
                headers={"X-Zalo-Signature": "sig", "X-Zalo-Timestamp": fresh_ts},
            )
            self.assertEqual(res_replay.status_code, 200)
            self.assertEqual(res_replay.json().get("reason"), "replay_detected")

    async def test_escalation_background_job(self):
        """Orders waiting in review_required > 4h send reminder; > 24h escalate to director."""
        # Setup 2 orders: one 5 hours old, one 26 hours old
        now = datetime.now(UTC)
        time_5h_ago = (now - timedelta(hours=5)).isoformat()
        time_26h_ago = (now - timedelta(hours=26)).isoformat()

        # Update timestamps directly in SQLite analyses table
        with self.store._lock:
            self.store.connection.execute(
                "UPDATE analyses SET created_at = ? WHERE id = ?", (time_5h_ago, self.order_id)
            )
            self.store.connection.commit()

        # Add second order 26h ago
        id_26h = self.store.record_analysis(self.analysis, source_file="old_order.pdf")
        with self.store._lock:
            self.store.connection.execute(
                "UPDATE analyses SET created_at = ? WHERE id = ?", (time_26h_ago, id_26h)
            )
            self.store.connection.commit()

        with patch("preflight.api.events.event_bus.publish") as mock_publish:
            ctx = {"store": self.store}
            res = await escalation_check(ctx)

            self.assertGreaterEqual(res["reminded"], 1)
            self.assertGreaterEqual(res["escalated_director"], 1)

            published_events = [call[0] for call in mock_publish.call_args_list if call[0][0] == "order.escalated"]
            self.assertTrue(any(ev[1].get("level") == "director" for ev in published_events))
            self.assertTrue(any(ev[1].get("level") == "manager_reminder" for ev in published_events))


if __name__ == "__main__":
    unittest.main()
