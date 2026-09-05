from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.security.rate_limiter import global_rate_limiter
from preflight.store import AuditStore


class TestRulesDynamicPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp_dir = TemporaryDirectory()
        cls._db_path = Path(cls._tmp_dir.name) / "test_rules.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{cls._db_path}"
        # Trigger DB initialization and seeding
        store = AuditStore(cls._db_path)
        store.close()
        cls.client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})

    @classmethod
    def tearDownClass(cls):
        cls._tmp_dir.cleanup()
        os.environ.pop("DATABASE_URL", None)

    def setUp(self):
        global_rate_limiter.reset()

    def test_01_list_initial_scopes(self):
        res = self.client.get("/api/v1/rules/scopes")
        self.assertEqual(res.status_code, 200)
        scopes = res.json()
        codes = [s["code"] for s in scopes]
        self.assertIn("global", codes)
        self.assertIn("north", codes)
        self.assertIn("south", codes)
        self.assertIn("mt", codes)
        self.assertIn("gt", codes)

    def test_02_create_and_delete_custom_scope(self):
        # Create APAC scope
        payload = {
            "code": "apac",
            "name": "Vùng Châu Á - Thái Bình Dương (APAC)",
            "description": "Chi nhánh Singapore, Tokyo, Sydney",
            "icon": "globe",
            "parent_code": "global",
        }
        res = self.client.post("/api/v1/rules/scopes", json=payload)
        self.assertEqual(res.status_code, 201)
        created = res.json()
        self.assertEqual(created["code"], "apac")
        self.assertEqual(created["name"], payload["name"])

        # Verify it shows in list
        list_res = self.client.get("/api/v1/rules/scopes")
        codes = [s["code"] for s in list_res.json()]
        self.assertIn("apac", codes)

        # Delete APAC scope
        del_res = self.client.delete("/api/v1/rules/scopes/apac")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        # Try to delete global scope (should fail with 400)
        del_global = self.client.delete("/api/v1/rules/scopes/global")
        self.assertEqual(del_global.status_code, 400)

    def test_03_list_initial_rule_definitions(self):
        res = self.client.get("/api/v1/rules/definitions?scope=global")
        self.assertEqual(res.status_code, 200)
        rules = res.json()
        self.assertGreaterEqual(len(rules), 6)
        rule_codes = [r["code"] for r in rules]
        self.assertIn("PRICE_MISMATCH", rule_codes)
        self.assertIn("INSUFFICIENT_STOCK", rule_codes)
        self.assertIn("UNKNOWN_SKU", rule_codes)
        self.assertIn("INACTIVE_SKU", rule_codes)
        self.assertIn("DUPLICATE_PO", rule_codes)
        self.assertIn("UOM_CONVERSION_MISSING", rule_codes)

    def test_04_create_update_and_delete_custom_rule(self):
        # Create custom rule
        payload = {
            "code": "CUTOFF_TIME_LIMIT",
            "name": "Giới hạn thời gian chốt sổ đơn hàng 18h",
            "description": "Chặn các đơn hàng gửi sau 18h hàng ngày không được xử lý trong ngày",
            "category": "document",
            "severity": "warning",
            "owner": "Phòng Vận hành",
            "enabled": True,
            "scope": "north",
            "custom_condition": "order.delivery_hour >= 18",
        }
        create_res = self.client.post("/api/v1/rules/definitions", json=payload)
        self.assertEqual(create_res.status_code, 201)
        created = create_res.json()
        rule_id = created["id"]
        self.assertEqual(created["code"], "CUTOFF_TIME_LIMIT")
        self.assertEqual(created["scope"], "north")

        # Update rule to Fatal Block
        update_res = self.client.put(
            f"/api/v1/rules/definitions/{rule_id}",
            json={"severity": "block", "enabled": False},
        )
        self.assertEqual(update_res.status_code, 200)
        updated = update_res.json()
        self.assertEqual(updated["severity"], "block")
        self.assertFalse(updated["enabled"])

        # Delete rule
        del_res = self.client.delete(f"/api/v1/rules/definitions/{rule_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        # Deleting again should return 404
        del_again = self.client.delete(f"/api/v1/rules/definitions/{rule_id}")
        self.assertEqual(del_again.status_code, 404)
