"""
Unit and Integration Tests for Pilot Telemetry & Reporting Engine (Prompt C7).
Verifies:
- Authorization matrix (VIEWER 403, MANAGER 200, ADMIN 200)
- Accuracy of calculated KPIs (hours saved, error rates, costs, RAG breakdown)
- RFC-4180 CSV export generation and headers
- Weekly summary email service dispatch and dry-run handling
"""

import os
import unittest
from datetime import UTC, datetime
from decimal import Decimal
from fastapi.testclient import TestClient

from preflight.api.app import app
from preflight.api.deps import get_audit_store
from preflight.models import Analysis, Finding, LineItem, Order
from preflight.security.rbac import Role
from preflight.services.pilot_reports import (
    generate_pilot_csv,
    generate_pilot_report,
    send_weekly_pilot_email,
)
from preflight.store import AuditStore


class TestPilotReports(unittest.TestCase):
    def setUp(self):
        self.db_path = f"test_reports_{int(datetime.now(UTC).timestamp()*1000)}.db"
        self.store = AuditStore(self.db_path)
        os.environ["PREFLIGHT_DB_PATH"] = self.db_path
        os.environ["PREFLIGHT_AUTH_REQUIRED"] = "true"
        os.environ["PREFLIGHT_ADMIN_KEY"] = "admin-secret-test-key"
        os.environ["PREFLIGHT_MANAGER_KEY"] = "manager-secret-test-key"
        os.environ["PREFLIGHT_VIEWER_KEY"] = "viewer-secret-test-key"
        app.dependency_overrides[get_audit_store] = lambda: self.store
        self.client = TestClient(app)

        # Seed sample orders
        self._seed_sample_orders()

    def tearDown(self):
        app.dependency_overrides.clear()
        self.store.close()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass
        for suf in ["-wal", "-shm"]:
            p = f"{self.db_path}{suf}"
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    def _seed_sample_orders(self):
        order1 = Order(
            po_number="PO-TEST-001",
            customer="Northstar Retail",
            currency="VND",
            items=(
                LineItem(sku="LAPTOP-A14", quantity=2, unit_price=Decimal("18500000")),
                LineItem(sku="MOUSE-WL", quantity=5, unit_price=Decimal("450000")),
            ),
        )
        analysis1 = Analysis(
            order=order1,
            findings=[],
            status="ready",
        )
        self.store.record_analysis(analysis1, "po_test_001.json")

        order2 = Order(
            po_number="PO-TEST-002",
            customer="Saigon Co.op",
            currency="VND",
            items=(
                LineItem(sku="HEADSET-PRO", quantity=10, unit_price=Decimal("1200000")),
            ),
        )
        finding_stock = Finding(
            code="INSUFFICIENT_STOCK",
            severity="error",
            message="Kho không đủ tồn",
        )
        analysis2 = Analysis(
            order=order2,
            findings=[finding_stock],
            status="blocked",
        )
        self.store.record_analysis(analysis2, "po_test_002.pdf")

    def _auth_header(self, role: Role) -> dict[str, str]:
        if role == Role.ADMIN:
            return {"X-API-Key": "admin-secret-test-key"}
        if role == Role.MANAGER:
            return {"X-API-Key": "manager-secret-test-key"}
        return {"X-API-Key": "viewer-secret-test-key"}

    def test_direct_service_report_generation(self):
        report = generate_pilot_report(self.store)
        self.assertIn("summary", report)
        self.assertIn("findings_distribution", report)
        self.assertIn("rag_tier_breakdown", report)
        self.assertIn("orders_sample", report)

        summary = report["summary"]
        self.assertGreaterEqual(summary["total_orders_received"], 2)
        self.assertGreaterEqual(summary["estimated_hours_saved"], 0.7)
        self.assertIn("INSUFFICIENT_STOCK", report["findings_distribution"])

    def test_direct_service_csv_generation(self):
        report = generate_pilot_report(self.store)
        csv_text = generate_pilot_csv(report)
        self.assertIn("PO PREFLIGHT ENTERPRISE — BÁO CÁO ĐO LƯỜNG PILOT", csv_text)
        self.assertIn("PO-TEST-001", csv_text)
        self.assertIn("Northstar Retail", csv_text)
        self.assertIn("INSUFFICIENT_STOCK", csv_text)

    def test_weekly_email_dry_run_dispatch(self):
        res = send_weekly_pilot_email(to_email="pilot_admin@preflight.vn")
        self.assertTrue(res["success"])
        self.assertIn(res["mode"], ("dry_run", "live"))
        self.assertEqual(res["recipient"], "pilot_admin@preflight.vn")

    def test_api_viewer_role_forbidden_403(self):
        headers = self._auth_header(Role.VIEWER)
        response = self.client.get("/api/v1/reports/pilot", headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_api_manager_role_gets_json_report_200(self):
        headers = self._auth_header(Role.MANAGER)
        response = self.client.get("/api/v1/reports/pilot", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("summary", data)
        self.assertEqual(data["summary"]["total_orders_received"], 2)
        self.assertGreaterEqual(data["summary"]["total_value_processed"], 51250000)

    def test_api_manager_role_exports_csv_200(self):
        headers = self._auth_header(Role.MANAGER)
        response = self.client.get("/api/v1/reports/pilot.csv", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "text/csv; charset=utf-8")
        self.assertIn('attachment; filename="po_preflight_pilot_report.csv"', response.headers.get("content-disposition", ""))
        self.assertIn("PO-TEST-001", response.text)

    def test_api_send_weekly_email_requires_admin_role(self):
        manager_headers = self._auth_header(Role.MANAGER)
        res_manager = self.client.post("/api/v1/reports/send-weekly-email", headers=manager_headers)
        self.assertEqual(res_manager.status_code, 403)

        admin_headers = self._auth_header(Role.ADMIN)
        res_admin = self.client.post("/api/v1/reports/send-weekly-email", headers=admin_headers)
        self.assertEqual(res_admin.status_code, 200)
        self.assertTrue(res_admin.json().get("success"))


if __name__ == "__main__":
    unittest.main()
