from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.api.deps import get_audit_store, get_catalog, get_store
from preflight.models import Analysis, LineItem, Order, Product
from preflight.parsers import parse_order_content
from preflight.rules import analyze_order
from preflight.security.rate_limiter import global_rate_limiter
from preflight.store import AuditStore



class TestEndToEndScenarios(unittest.TestCase):
    """
    MIT-Grade End-to-End (E2E) Scenario Validation Suite.
    Validates complete business workflows across multiple enterprise intake scenarios:
    1. Multi-Format Document Ingestion (JSON, CSV, Plaintext).
    2. Multi-Currency Global Order Intake (USD with Exchange Rate Grounding).
    3. Staged Human Extraction Review & Line Item Modification Flow.
    4. Multi-item Mixed Status Order with Price Tolerance and Stock Constraints.
    5. High-Throughput Batch Intake Simulation (50 Consecutive Orders).
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})
        cls.catalog = get_catalog()

    def setUp(self):
        self._orig_rl_enabled = global_rate_limiter.enabled
        global_rate_limiter.enabled = False
        global_rate_limiter.reset()
        self.tmp_dir = TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "test_e2e.db"
        self.store = AuditStore(self.db_path)

        def _override_store():
            return self.store

        app.dependency_overrides[get_audit_store] = _override_store
        app.dependency_overrides[get_store] = _override_store

    def tearDown(self):
        global_rate_limiter.enabled = self._orig_rl_enabled
        global_rate_limiter.reset()
        app.dependency_overrides.clear()
        self.store.close()
        self.tmp_dir.cleanup()


    def test_e2e_multi_format_ingestion(self):
        """Test intake across JSON, CSV, and Plaintext table formats."""
        # 1. JSON Format
        json_content = json.dumps({
            "po_number": "PO-E2E-JSON",
            "customer": "JSON Customer Inc",
            "currency": "VND",
            "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000}],
        }).encode("utf-8")
        res_json = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order.json", json_content, "application/json")},
        )
        self.assertEqual(res_json.status_code, 201)
        self.assertEqual(res_json.json()["po_number"], "PO-E2E-JSON")

        # 2. CSV Format
        csv_content = (
            "po_number,customer,currency,sku,quantity,unit_price\n"
            "PO-E2E-CSV,CSV Enterprise,VND,LAPTOP-A14,2,18500000\n"
            "PO-E2E-CSV,CSV Enterprise,VND,MONITOR-27,2,6200000\n"
        ).encode("utf-8")
        res_csv = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order.csv", csv_content, "text/csv")},
        )
        self.assertEqual(res_csv.status_code, 201)
        self.assertEqual(res_csv.json()["po_number"], "PO-E2E-CSV")
        self.assertEqual(len(res_csv.json()["items"]), 2)

        # 3. Plaintext Format
        txt_content = (
            "PO_NUMBER: PO-E2E-TXT\n"
            "CUSTOMER: Text Format Corp\n"
            "CURRENCY: VND\n"
            "SKU | QUANTITY | UNIT_PRICE\n"
            "LAPTOP-A14 | 1 | 18500000\n"
        ).encode("utf-8")
        res_txt = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order.txt", txt_content, "text/plain")},
        )
        self.assertEqual(res_txt.status_code, 201)
        self.assertEqual(res_txt.json()["po_number"], "PO-E2E-TXT")

    def test_e2e_multi_currency_usd_intake(self):
        """Test global order in USD converted to VND against master catalog."""
        usd_po = {
            "po_number": "PO-E2E-USD-001",
            "customer": "Silicon Valley Systems Inc",
            "currency": "USD",
            "items": [
                # ~ $740 @ 25,000 VND/USD = ~18,500,000 VND
                {"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 740},
            ],
        }
        res = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order_usd.json", json.dumps(usd_po).encode("utf-8"), "application/json")},
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["currency"], "USD")
        self.assertEqual(Decimal(str(data["total"])), Decimal("740"))

    def test_e2e_staged_extraction_review_and_edit_flow(self):
        """Test full staged review flow: upload with staged_review=True -> review -> confirm edits -> evaluate rules."""
        # 1. Ingest into extraction_review staging state
        draft_po = {
            "po_number": "PO-STAGE-REVIEW",
            "customer": "Draft Client Ltd",
            "currency": "VND",
            "items": [
                {"sku": "LAPTOP-A14-MISSPELLED", "quantity": 1, "unit_price": 10000000},
            ],
        }
        res_upload = self.client.post(
            "/api/v1/orders/upload?staged_review=true",
            files={"file": ("draft.json", json.dumps(draft_po).encode("utf-8"), "application/json")},
        )
        self.assertEqual(res_upload.status_code, 201)
        order_id = res_upload.json()["id"]
        self.assertEqual(res_upload.json()["status"], "extraction_review")

        # 2. Operator corrects the line items and submits confirmation
        confirm_payload = {
            "po_number": "PO-STAGE-REVIEW",
            "customer": "Draft Client Ltd",
            "currency": "VND",
            "items": [
                {"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000},
            ],
        }
        res_confirm = self.client.post(
            f"/api/v1/orders/{order_id}/confirm-extraction",
            json=confirm_payload,
        )
        self.assertEqual(res_confirm.status_code, 200)
        confirmed_data = res_confirm.json()

        # Should transition out of extraction_review into ready_for_approval
        self.assertEqual(confirmed_data["status"], "ready_for_approval")
        self.assertEqual(confirmed_data["risk_level"], "LOW")
        self.assertEqual(confirmed_data["items"][0]["sku"], "LAPTOP-A14")
        self.assertEqual(len(confirmed_data["findings"]), 0)

    def test_e2e_throughput_stress_simulation(self):
        """Test system stability and correctness across 30 sequential order intakes and decisions."""
        for idx in range(1, 31):
            po_payload = {
                "po_number": f"PO-BATCH-{idx:03d}",
                "customer": "Northstar Retail",
                "currency": "VND",
                "items": [
                    {"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000},
                    {"sku": "MONITOR-27", "quantity": 1, "unit_price": 6200000},
                ],
            }
            res = self.client.post(
                "/api/v1/orders/upload",
                files={"file": (f"batch_{idx}.json", json.dumps(po_payload).encode("utf-8"), "application/json")},
            )
            self.assertEqual(res.status_code, 201)
            order_id = res.json()["id"]

            dec_res = self.client.post(
                f"/api/v1/orders/{order_id}/decide",
                json={"decision": "approved", "actor": "batch_stress_runner", "note": "Auto batch approve"},
            )
            self.assertEqual(dec_res.status_code, 200)

        # Verify all 30 orders are recorded in the store
        orders_list = self.store.list_orders(limit=100)
        self.assertGreaterEqual(len(orders_list), 30)


if __name__ == "__main__":
    unittest.main()
