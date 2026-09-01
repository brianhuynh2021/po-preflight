from __future__ import annotations

import json
import unittest
import uuid
from decimal import Decimal

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.security.rate_limiter import global_rate_limiter


class TestExtractionReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})

    def setUp(self):
        global_rate_limiter.reset()


    def test_upload_staged_review_and_confirm_flow(self):
        """Test full staging flow: upload with staged_review -> confirm extraction with edited values -> rules executed."""
        unique_po = f"PO-STAGE-{uuid.uuid4().hex[:6].upper()}"

        # 1. Upload PO with staged_review=True (Simulating OCR extraction staging)
        po_content = {
            "po_number": unique_po,
            "customer": "Apex Solutions",
            "items": [
                # OCR misread quantity as 600 instead of 6
                {"sku": "LAPTOP-A14", "quantity": 600, "unit_price": 18500000},
            ],
        }
        file_payload = {"file": ("order.json", json.dumps(po_content), "application/json")}
        res_upload = self.client.post("/api/v1/orders/upload?staged_review=true", files=file_payload)
        self.assertEqual(res_upload.status_code, 201)
        upload_data = res_upload.json()

        # Should be in extraction_review with NO findings evaluated yet
        self.assertEqual(upload_data["status"], "extraction_review")
        self.assertEqual(len(upload_data["findings"]), 0)
        order_id = upload_data["id"]

        # 2. User reviews and corrects the quantity from 600 to 2
        confirm_payload = {
            "po_number": unique_po,
            "customer": "Apex Solutions",
            "items": [
                {"sku": "LAPTOP-A14", "quantity": 2, "unit_price": 18500000},
            ],
            "currency": "VND",
        }
        res_confirm = self.client.post(
            f"/api/v1/orders/{order_id}/confirm-extraction",
            json=confirm_payload,
        )
        self.assertEqual(res_confirm.status_code, 200)
        confirmed_data = res_confirm.json()

        # Rules should now be evaluated on the corrected data
        self.assertEqual(confirmed_data["status"], "ready_for_approval")
        self.assertEqual(confirmed_data["risk_level"], "LOW")
        self.assertEqual(confirmed_data["items"][0]["quantity"], 2)


if __name__ == "__main__":
    unittest.main()
