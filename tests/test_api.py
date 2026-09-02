from __future__ import annotations

import json
import os
import unittest
import uuid
from pathlib import Path

from tempfile import TemporaryDirectory

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.api.deps import DEFAULT_CATALOG_PATH, DEFAULT_DB_PATH
from preflight.security.rate_limiter import global_rate_limiter
from preflight.store import AuditStore


class TestFastAPIGateway(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp_dir = TemporaryDirectory()
        cls._db_path = Path(cls._tmp_dir.name) / "test_api.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{cls._db_path}"
        cls.client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})

    @classmethod
    def tearDownClass(cls):
        cls._tmp_dir.cleanup()
        os.environ.pop("DATABASE_URL", None)

    def setUp(self):
        global_rate_limiter.reset()


    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "0.1.0")
        self.assertTrue(data["database"]["connected"])
        self.assertTrue(data["catalog"]["loaded"])
        self.assertGreater(data["catalog"]["total_skus"], 0)
        self.assertGreaterEqual(data["uptime_seconds"], 0)

    def test_openapi_json(self):
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("PO Preflight", data["info"]["title"])
        self.assertIn("/health", data["paths"])
        self.assertIn("/api/v1/orders", data["paths"])
        self.assertIn("/api/v1/orders/upload", data["paths"])
        self.assertIn("/api/v1/dashboard/stats", data["paths"])
        self.assertIn("/api/v1/catalog", data["paths"])
        self.assertIn("/api/v1/rules", data["paths"])

    def test_swagger_docs_html(self):
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("swagger", response.text.lower())

    def test_list_orders(self):
        response = self.client.get("/api/v1/orders")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        first = data[0]
        self.assertIn("po_number", first)
        self.assertIn("customer", first)
        self.assertIn("risk_level", first)
        self.assertIn("status", first)

    def test_get_order_detail(self):
        # First get list to find an ID
        list_res = self.client.get("/api/v1/orders")
        self.assertEqual(list_res.status_code, 200)
        first_id = list_res.json()[0]["id"]

        detail_res = self.client.get(f"/api/v1/orders/{first_id}")
        self.assertEqual(detail_res.status_code, 200)
        data = detail_res.json()
        self.assertEqual(data["id"], first_id)
        self.assertIn("items", data)
        self.assertIn("findings", data)
        self.assertIn("decisions", data)

    def test_dashboard_stats(self):
        response = self.client.get("/api/v1/dashboard/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_orders", data)
        self.assertIn("pass_rate_percent", data)
        self.assertIn("violations_breakdown", data)
        self.assertIn("total_pipeline_value", data)

    def test_catalog_endpoint(self):
        response = self.client.get("/api/v1/catalog")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIn("sku", data[0])
        self.assertIn("unit_price", data[0])

    def test_rules_endpoint(self):
        response = self.client.get("/api/v1/rules")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("price_tolerance_percent", data)

    def test_upload_order_file(self):
        uid = uuid.uuid4().hex[:6]
        po_payload = {
            "po_number": f"PO-TEST-{uid}",
            "customer": "Clean Enterprise",
            "currency": "VND",
            "total": 18500000,
            "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000}],
        }
        response = self.client.post(
            "/api/v1/orders/upload",
            files={"file": (f"po-clean-{uid}.json", json.dumps(po_payload).encode("utf-8"), "application/json")},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["po_number"], f"PO-TEST-{uid}")
        self.assertIn("items", data)

    def test_record_human_decision(self):
        uid = uuid.uuid4().hex[:6]
        po_payload = {
            "po_number": f"PO-REV-{uid}",
            "customer": "Review Customer",
            "currency": "VND",
            "total": 20000000,
            "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 20000000}],
        }
        upload_res = self.client.post(
            "/api/v1/orders/upload",
            files={"file": (f"po-rev-{uid}.json", json.dumps(po_payload).encode("utf-8"), "application/json")},
        )
        self.assertEqual(upload_res.status_code, 201)
        order_id = upload_res.json()["id"]

        decision_payload = {
            "decision": "approved",
            "actor": "lead_reviewer@company.com",
            "note": "Approved exception based on sales director sign-off.",
        }
        res = self.client.post(f"/api/v1/orders/{order_id}/decide", json=decision_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["decision"], "approved")
        self.assertEqual(data["actor"], "api:system_administrator")
        self.assertEqual(res.headers.get("x-deprecated-field"), "actor")


    def test_cannot_approve_blocked_order_returns_409(self):
        uid = uuid.uuid4().hex[:6]
        po_payload = {
            "po_number": f"PO-BLOCK-{uid}",
            "customer": "Blocked Customer",
            "currency": "VND",
            "total": 1000000,
            "items": [{"sku": "NON-EXISTENT-SKU-9999", "quantity": 1, "unit_price": 1000000}],
        }
        upload_res = self.client.post(
            "/api/v1/orders/upload",
            files={"file": (f"po-block-{uid}.json", json.dumps(po_payload).encode("utf-8"), "application/json")},
        )
        self.assertEqual(upload_res.status_code, 201)
        order_id = upload_res.json()["id"]
        self.assertEqual(upload_res.json()["status"], "blocked")

        # Attempt to approve a blocked order
        res = self.client.post(
            f"/api/v1/orders/{order_id}/decide",
            json={"decision": "approved", "actor": "attacker", "note": "Bypassing checks"},
        )
        self.assertEqual(res.status_code, 409)
        self.assertIn("blocked order", res.json()["detail"].lower())

    def test_review_required_note_enforcement_returns_422(self):
        uid = uuid.uuid4().hex[:6]
        po_payload = {
            "po_number": f"PO-WARN-{uid}",
            "customer": "Warning Customer",
            "currency": "VND",
            "total": 25000000,
            "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 25000000}],
        }
        upload_res = self.client.post(
            "/api/v1/orders/upload",
            files={"file": (f"po-warn-{uid}.json", json.dumps(po_payload).encode("utf-8"), "application/json")},
        )
        self.assertEqual(upload_res.status_code, 201)
        order_id = upload_res.json()["id"]
        self.assertEqual(upload_res.json()["status"], "review_required")

        # Note empty -> 422
        res_empty = self.client.post(
            f"/api/v1/orders/{order_id}/decide",
            json={"decision": "approved", "actor": "manager", "note": ""},
        )
        self.assertEqual(res_empty.status_code, 422)

        # Note too short (<10 chars) -> 422
        res_short = self.client.post(
            f"/api/v1/orders/{order_id}/decide",
            json={"decision": "approved", "actor": "manager", "note": "ok"},
        )
        self.assertEqual(res_short.status_code, 422)

    def test_redecision_on_decided_order_returns_409(self):
        uid = uuid.uuid4().hex[:6]
        po_payload = {
            "po_number": f"PO-REDEC-{uid}",
            "customer": "Clean Customer",
            "currency": "VND",
            "total": 18500000,
            "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000}],
        }
        upload_res = self.client.post(
            "/api/v1/orders/upload",
            files={"file": (f"po-redec-{uid}.json", json.dumps(po_payload).encode("utf-8"), "application/json")},
        )
        order_id = upload_res.json()["id"]

        # First approval
        res1 = self.client.post(
            f"/api/v1/orders/{order_id}/decide",
            json={"decision": "approved", "actor": "manager", "note": "Legitimate approval"},
        )
        self.assertEqual(res1.status_code, 200)

        # Second approval on already approved order -> 409
        res2 = self.client.post(
            f"/api/v1/orders/{order_id}/decide",
            json={"decision": "approved", "actor": "manager2", "note": "Duplicate approval attempt"},
        )
        self.assertEqual(res2.status_code, 409)


if __name__ == "__main__":
    unittest.main()


