from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.api.deps import get_audit_store, get_catalog
from preflight.models import Analysis, Finding, LineItem, Order, Product
from preflight.store import AuditStore


class TestErrorTaxonomy(unittest.TestCase):
    """Test suite for Prompt A4 (RFC 7807 Error Taxonomy & Exception Safety)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_errors.db"
        self.store = AuditStore(self.db_path)
        self.catalog = {
            "SKU-001": Product(
                sku="SKU-001",
                name="Product 1",
                unit_price=Decimal("100000"),
                stock=50,
            )
        }
        app.dependency_overrides[get_audit_store] = lambda: self.store
        app.dependency_overrides[get_catalog] = lambda: self.catalog

        self.client = TestClient(app, raise_server_exceptions=False)
        self.manager_headers = {"X-API-Key": "pf_dev_mgr_8802", "X-Client": "web"}
        self.viewer_headers = {"X-API-Key": "pf_dev_view_6604", "X-Client": "web"}

    def tearDown(self):
        app.dependency_overrides.clear()
        self.store.close()
        self.temp_dir.cleanup()

    def test_a_upload_file_too_large_413(self):
        """(a) upload 11MB -> 413, body.code == 'PAYLOAD_TOO_LARGE', has request_id, no NameError."""
        large_content = b"x" * (11 * 1024 * 1024)
        files = {"file": ("large_order.json", io.BytesIO(large_content), "application/json")}

        resp = self.client.post("/api/v1/orders/upload", files=files, headers=self.viewer_headers)
        self.assertEqual(resp.status_code, 413)
        self.assertEqual(resp.headers.get("content-type"), "application/problem+json")
        data = resp.json()
        self.assertEqual(data["code"], "PAYLOAD_TOO_LARGE")
        self.assertEqual(data["status"], 413)
        self.assertTrue(bool(data.get("request_id")))
        self.assertNotIn("NameError", str(data))
        self.assertNotIn("traceback", str(data).lower())

    def test_b_upload_unsupported_format_415(self):
        """(b) upload .docx -> 415 UNSUPPORTED_FORMAT."""
        docx_content = b"PK\x03\x04fake docx content"
        files = {"file": ("sample_order.docx", io.BytesIO(docx_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}

        resp = self.client.post("/api/v1/orders/upload", files=files, headers=self.viewer_headers)
        self.assertEqual(resp.status_code, 415)
        self.assertEqual(resp.headers.get("content-type"), "application/problem+json")
        data = resp.json()
        self.assertEqual(data["code"], "UNSUPPORTED_FORMAT")
        self.assertEqual(data["status"], 415)
        self.assertIn("không được hỗ trợ", data["detail"])

    def test_c_upload_malformed_json_400(self):
        """(c) upload JSON with invalid structure -> 400 PARSE_ERROR, detail in Vietnamese, no traceback."""
        invalid_json = b"{'invalid': 'json', not_valid_json}"
        files = {"file": ("broken_order.json", io.BytesIO(invalid_json), "application/json")}

        resp = self.client.post("/api/v1/orders/upload", files=files, headers=self.viewer_headers)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.headers.get("content-type"), "application/problem+json")
        data = resp.json()
        self.assertEqual(data["code"], "PARSE_ERROR")
        self.assertIn("Không thể đọc hoặc phân tích", data["detail"])
        self.assertNotIn("Traceback", str(data))

    def test_d_get_nonexistent_order_404(self):
        """(d) GET /orders/999999 -> 404 NOT_FOUND format problem+json."""
        resp = self.client.get("/api/v1/orders/999999", headers=self.viewer_headers)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.headers.get("content-type"), "application/problem+json")
        data = resp.json()
        self.assertEqual(data["code"], "NOT_FOUND")
        self.assertEqual(data["status"], 404)
        self.assertIn("Không tìm thấy", data["detail"])

    def test_e_decide_invalid_schema_or_note_validation_failed_422(self):
        """(e) decide with schema violation or governance violation -> 422 VALIDATION_FAILED with problem+json."""
        # 1. Pydantic validation error
        resp = self.client.post(
            "/api/v1/orders/1/decide",
            json={"decision": "invalid_choice", "note": "Valid note 123"},
            headers=self.manager_headers,
        )
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.headers.get("content-type"), "application/problem+json")
        data = resp.json()
        self.assertEqual(data["code"], "VALIDATION_FAILED")
        self.assertIn("errors", data)

        # 2. Domain decision governance validation error (approving order with warnings requires note >= 10 chars)
        order = Order(
            po_number="PO-WARN-1",
            customer="Warn Corp",
            items=(LineItem(sku="SKU-001", quantity=1, unit_price=Decimal("100000")),),
            currency="VND",
        )
        analysis = Analysis(
            order=order,
            findings=[Finding(code="WARN_STOCK", severity="warning", message="Stock low")],
            status="review_required",
        )
        order_id = self.store.record_analysis(analysis, "warn.json")

        resp2 = self.client.post(
            f"/api/v1/orders/{order_id}/decide",
            json={"decision": "approved", "note": "short"},  # note too short for warning override
            headers=self.manager_headers,
        )
        self.assertEqual(resp2.status_code, 422)
        self.assertEqual(resp2.headers.get("content-type"), "application/problem+json")
        data2 = resp2.json()
        self.assertEqual(data2["code"], "VALIDATION_FAILED")

    def test_f_internal_error_does_not_leak_secrets_500(self):
        """(f) Monkeypatch to raise RuntimeError('secret-db-password-123') -> 500 INTERNAL_ERROR, no leak."""
        with patch.object(self.store, "get_order", side_effect=RuntimeError("secret-db-password-123")):
            resp = self.client.get("/api/v1/orders/1", headers=self.viewer_headers)
            self.assertEqual(resp.status_code, 500)
            self.assertEqual(resp.headers.get("content-type"), "application/problem+json")
            data = resp.json()
            self.assertEqual(data["code"], "INTERNAL_ERROR")
            self.assertNotIn("secret-db-password-123", str(data))
            self.assertIn("Lỗi hệ thống. Mã tham chiếu:", data["detail"])

    def test_g_cleanup_temp_files_after_upload_error(self):
        """(g) No leftover temp files in runtime/uploads after upload error."""
        upload_dir = Path("runtime/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        before_files = set(upload_dir.glob("tmp_*"))

        malformed_bytes = b"bad json content"
        files = {"file": ("malformed_order.json", io.BytesIO(malformed_bytes), "application/json")}
        resp = self.client.post("/api/v1/orders/upload", files=files, headers=self.viewer_headers)
        self.assertEqual(resp.status_code, 400)

        after_files = set(upload_dir.glob("tmp_*"))
        new_temp_files = after_files - before_files
        self.assertEqual(len(new_temp_files), 0, f"Found leftover temp files: {new_temp_files}")


if __name__ == "__main__":
    unittest.main()
