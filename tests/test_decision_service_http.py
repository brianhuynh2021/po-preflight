from __future__ import annotations

import hashlib
import hmac
import json
import os
import subprocess
import tempfile
import time
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient

from preflight.agent.graph import build_preflight_graph
from preflight.api.app import app
from preflight.api.deps import get_audit_store, get_catalog, get_store
from preflight.bot.telegram import TelegramBotService
from preflight.bot.zalo import ZaloBotService
from preflight.models import (
    CustomerCreditProfile,
    CustomerPriceAgreement,
    Product,
    RulePolicy,
    UOMConversion,
    Analysis,
    Finding,
    LineItem,
    Order,
)
from preflight.security.rbac import Role

from preflight.services.decisions import DecisionError, Principal, decide_order
from preflight.store import AuditStore


class TestDecisionServiceHTTP(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_decisions.db"
        self.store = AuditStore(self.db_path)

        self.catalog = {
            "SKU-001": Product(
                sku="SKU-001",
                name="Product 1",
                unit_price=Decimal("100000"),
                stock=50,
                active=True,
                base_uom="PCS",
            )
        }

        app.dependency_overrides[get_audit_store] = lambda: self.store
        app.dependency_overrides[get_store] = lambda: self.store
        app.dependency_overrides[get_catalog] = lambda: self.catalog
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.store.close()
        self.temp_dir.cleanup()

    def _seed_order(self, po_number: str = "PO-101", status: str = "ready_for_approval", error_count: int = 0) -> int:
        findings = []
        if error_count > 0:
            for i in range(error_count):
                findings.append(
                    Finding(
                        code="ERR_PRICE",
                        severity="error",
                        message=f"Price Error {i+1}",
                    )
                )
        order = Order(
            po_number=po_number,
            customer="Northstar Retail",
            currency="VND",
            items=(
                LineItem(
                    sku="SKU-001",
                    quantity=10,
                    unit_price=Decimal("100000"),
                ),
            ),
        )
        analysis = Analysis(
            order=order,
            status=status,
            findings=findings,
        )
        return self.store.record_analysis(analysis, "test.json")


    def test_criterion_a_viewer_role_forbidden_403(self):
        """(a) /orders/{id}/decide với user VIEWER -> 403 Forbidden."""
        order_id = self._seed_order("PO-VIEWER-TEST", status="ready_for_approval")
        headers = {"X-API-Key": "pf_dev_view_6604"}

        res = self.client.post(
            f"/api/v1/orders/{order_id}/decide",
            json={"decision": "approved", "note": "Approved by viewer"},
            headers=headers,
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("MANAGER", res.json().get("detail", ""))

    def test_criterion_b_actor_ignored_and_deprecated_header(self):
        """(b) /orders/{id}/decide với user MANAGER, gửi actor: 'fake_admin' -> DB ghi actor từ auth, header X-Deprecated-Field."""
        order_id = self._seed_order("PO-ACTOR-TEST", status="ready_for_approval")
        headers = {"X-API-Key": "pf_dev_mgr_8802", "X-Client": "web"}

        res = self.client.post(
            f"/api/v1/orders/{order_id}/decide",
            json={"decision": "approved", "actor": "fake_admin_hacker", "note": "Legit manager approval note"},
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("x-deprecated-field"), "actor")

        data = res.json()
        self.assertTrue(data["success"])
        # Should record web:operations_manager, NOT fake_admin_hacker
        self.assertEqual(data["actor"], "web:operations_manager")

        # Verify in DB
        history = self.store.history("PO-ACTOR-TEST")
        self.assertEqual(len(history["decisions"]), 1)
        self.assertEqual(history["decisions"][0]["actor"], "web:operations_manager")

    def test_criterion_c_blocked_order_cannot_be_approved_409(self):
        """(c) /orders/{id}/decide với PO Blocked, decision='approved' -> 409 Conflict."""
        order_id = self._seed_order("PO-BLOCKED-TEST", status="blocked", error_count=1)
        headers = {"X-API-Key": "pf_dev_mgr_8802"}

        res = self.client.post(
            f"/api/v1/orders/{order_id}/decide",
            json={"decision": "approved", "note": "Trying to force approve blocked PO"},
            headers=headers,
        )
        self.assertEqual(res.status_code, 409)
        self.assertIn("cannot be approved", res.json().get("detail", "").lower())

    def test_criterion_d_telegram_webhook_secret_enforcement(self):
        """(d) Telegram webhook thiếu header secret -> 403; server thiếu TELEGRAM_WEBHOOK_SECRET -> 503."""
        # 1. Server missing secret -> 503
        with patch.dict(os.environ, {"TELEGRAM_WEBHOOK_SECRET": "", "TELEGRAM_SECRET_TOKEN": ""}, clear=False):
            res_no_secret = self.client.post(
                "/api/v1/bot/telegram/webhook",
                json={"callback_query": {"id": "1", "data": "approve:1"}},
            )
            self.assertEqual(res_no_secret.status_code, 503)

        # 2. Server configured with secret, request missing or wrong token -> 403
        with patch.dict(os.environ, {"TELEGRAM_WEBHOOK_SECRET": "tele_sec_999"}, clear=False):
            res_bad_token = self.client.post(
                "/api/v1/bot/telegram/webhook",
                json={"callback_query": {"id": "1", "data": "approve:1"}},
                headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_token"},
            )
            self.assertEqual(res_bad_token.status_code, 403)

    def test_criterion_e_zalo_webhook_signature_and_role_enforcement(self):
        """(e) Zalo webhook không chữ ký -> 401; có chữ ký đúng + identity VIEWER -> 403."""
        app_id = "zalo_test_app"
        secret_key = "zalo_test_secret_key"

        with patch.dict(os.environ, {"ZALO_APP_ID": app_id, "ZALO_SECRET_KEY": secret_key}, clear=False):
            # 1. Missing signature -> 401
            res_no_sig = self.client.post(
                "/api/v1/bot/zalo/webhook",
                json={"message": {"text": "APPROVE:PO-ZALO-1"}},
            )
            self.assertEqual(res_no_sig.status_code, 401)

            # 2. Valid signature, but sender is linked as VIEWER -> 403
            self.store.upsert_channel_identity(
                channel="zalo",
                external_id="zalo_viewer_uid_123",
                user_id="viewer_zalo_user",
                display_name="Zalo Viewer",
                role="VIEWER",
            )
            self._seed_order("PO-ZALO-1", status="ready_for_approval")

            payload = {
                "message": {"text": "APPROVE:PO-ZALO-1"},
                "sender": {"id": "zalo_viewer_uid_123"},
            }
            body_bytes = json.dumps(payload).encode("utf-8")
            ts = str(int(time.time()))
            data_to_sign = f"{app_id}{body_bytes.decode('utf-8')}{ts}{secret_key}".encode("utf-8")
            sig = hashlib.sha256(data_to_sign).hexdigest()

            res_viewer = self.client.post(
                "/api/v1/bot/zalo/webhook",
                content=body_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Zalo-Signature": sig,
                    "X-Zalo-Timestamp": ts,
                },
            )
            self.assertEqual(res_viewer.status_code, 403)
            self.assertIn("MANAGER", res_viewer.json().get("detail", ""))

    def test_criterion_f_unlinked_account_rejected_without_db_write(self):
        """(f) Telegram/Zalo callback từ user chưa link identity -> thông báo chưa liên kết, KHÔNG ghi DB."""
        order_id = self._seed_order("PO-UNLINKED-TEST", status="ready_for_approval")

        # 1. Telegram unlinked
        tele_bot = TelegramBotService(store=self.store)
        res_tele = tele_bot.handle_callback_action(
            callback_data=f"approve:{order_id}",
            from_user_id="999888777",
            from_username="stranger",
        )
        self.assertFalse(res_tele["success"])
        self.assertIn("chưa được liên kết", res_tele["popup_message"])

        # Verify DB is untouched
        history = self.store.history("PO-UNLINKED-TEST")
        self.assertEqual(len(history["decisions"]), 0)

        # 2. Zalo unlinked
        zalo_bot = ZaloBotService(store=self.store, app_id="test", secret_key="sec")
        res_zalo = zalo_bot.process_webhook_event(
            {
                "message": {"text": f"APPROVE:PO-UNLINKED-TEST"},
                "sender": {"id": "unlinked_zalo_uid_999"},
            }
        )
        self.assertEqual(res_zalo["status"], "error")
        self.assertEqual(res_zalo["error"], "UNLINKED_ACCOUNT")

        # Verify DB is still untouched
        history = self.store.history("PO-UNLINKED-TEST")
        self.assertEqual(len(history["decisions"]), 0)

    def test_criterion_g_agent_workflow_blocked_po_approval_rejected(self):
        """(g) Agent workflow với PO Blocked -> human_approval_node không cho approve -> status='decision_rejected', không sang erp_sync."""
        self._seed_order("PO-AGENT-BLOCKED", status="blocked", error_count=1)

        graph = build_preflight_graph(self.catalog, self.store, with_interrupt=True)
        config = {"configurable": {"thread_id": "thread_blocked_test"}}

        # Start workflow
        initial_input = {
            "po_number": "PO-AGENT-BLOCKED",
            "source_file": "blocked.json",
            "status": "blocked",
            "error_count": 1,
            "warning_count": 0,
        }
        res_pause = graph.invoke(initial_input, config=config)
        self.assertEqual(res_pause["status"], "blocked")


        # Resume with Manager approving a blocked PO
        graph.update_state(
            config,
            {
                "decision": "APPROVED",
                "decided_by": "lead_mgr",
                "decision_notes": "Attempting illegal override",
            },
        )
        resumed = graph.invoke(None, config=config)

        self.assertEqual(resumed["status"], "decision_rejected")
        self.assertIsNotNone(resumed.get("decision_error"))
        self.assertFalse(resumed.get("erp_synced", False))

    def test_criterion_h_static_grep_record_decision_single_gate(self):
        """(h) Static check: grep -rn 'record_decision(' src/ CHỈ xuất hiện trong store.py và services/decisions.py."""
        cmd = ["grep", "-rn", "record_decision(", "src/"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        lines = [line.strip() for line in res.stdout.strip().split("\n") if line.strip()]

        for line in lines:
            self.assertTrue(
                "src/preflight/store.py" in line or "src/preflight/services/decisions.py" in line or "def record_decision(" in line,
                f"Forbidden direct call to store.record_decision found in: {line}",
            )


if __name__ == "__main__":
    unittest.main()
