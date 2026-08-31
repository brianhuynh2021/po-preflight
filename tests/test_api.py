from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.api.deps import DEFAULT_CATALOG_PATH, DEFAULT_DB_PATH
from preflight.store import AuditStore


class TestFastAPIGateway(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

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
        sample_path = Path("examples/orders/po-clean.json")
        with sample_path.open("rb") as f:
            response = self.client.post(
                "/api/v1/orders/upload",
                files={"file": ("po-clean-upload-test.json", f, "application/json")},
            )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["po_number"], "PO-2026-1001")
        self.assertIn("items", data)

    def test_record_human_decision(self):
        # Upload a PO to decide on
        sample_path = Path("examples/orders/po-review.json")
        with sample_path.open("rb") as f:
            upload_res = self.client.post(
                "/api/v1/orders/upload",
                files={"file": ("po-review-decision-test.json", f, "application/json")},
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
        self.assertTrue(data["success"])
        self.assertEqual(data["decision"], "approved")
        self.assertEqual(data["actor"], "lead_reviewer@company.com")


if __name__ == "__main__":
    unittest.main()
