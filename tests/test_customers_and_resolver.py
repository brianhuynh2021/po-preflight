import io
import json
import os
import subprocess
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from preflight.api.app import app
from preflight.api.deps import get_audit_store
from preflight.models import CustomerMaster, LineItem, Order, Product
from preflight.rag.matcher import HybridSKUMatcher
from preflight.services.customer_resolver import (
    CUSTOMER_FUZZY_MATCHED,
    CUSTOMER_UNRESOLVED,
    normalize_vietnamese_name,
    resolve_customer,
)
from preflight.store import AuditStore


class TestCustomerMasterAndResolver(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_customers.db"
        self.store = AuditStore(self.db_path)

        app.dependency_overrides[get_audit_store] = lambda: self.store
        self.client = TestClient(app)
        self.auth_headers = {"X-API-Key": "pf_dev_mgr_8802"}

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()
        app.dependency_overrides.clear()

    def test_vietnamese_name_normalization(self):
        # Legal prefixes and diacritics stripped
        n1 = normalize_vietnamese_name("Công ty TNHH A.B.C")
        n2 = normalize_vietnamese_name("CTY TNHH ABC")
        self.assertEqual(n1.replace(" ", ""), n2.replace(" ", ""))

        n3 = normalize_vietnamese_name("CÔNG TY CỔ PHẦN ĐẦU TƯ VÀ PHÁT TRIỂN XYZ (JSC)")
        self.assertTrue("dau tu" in n3 and "phat trien xyz" in n3)

    def test_exact_and_fuzzy_customer_resolution(self):
        cust = CustomerMaster(
            code="CUST-ABC-99",
            name="Công ty TNHH Giải pháp Phần mềm ABC",
            tax_code="0123456789",
            tier="VIP",
            aliases=["ABC Software", "Phần mềm ABC"],
        )
        self.store.create_customer(cust)

        # 1. Tax code match
        res, finding = resolve_customer("Unknown Name", tax_code="0123456789", store=self.store)
        self.assertIsNotNone(res)
        self.assertEqual(res.code, "CUST-ABC-99")
        self.assertIsNone(finding)

        # 2. Exact name match
        res, finding = resolve_customer("Công ty TNHH Giải pháp Phần mềm ABC", store=self.store)
        self.assertIsNotNone(res)
        self.assertEqual(res.code, "CUST-ABC-99")
        self.assertIsNone(finding)

        # 3. Alias match
        res, finding = resolve_customer("ABC Software", store=self.store)
        self.assertIsNotNone(res)
        self.assertEqual(res.code, "CUST-ABC-99")
        self.assertIsNone(finding)

        # 4. Normalized match
        res, finding = resolve_customer("Cty Tnhh Giai Phap Phan Mem Abc", store=self.store)
        self.assertIsNotNone(res)
        self.assertEqual(res.code, "CUST-ABC-99")
        self.assertIsNone(finding)

        # 5. Fuzzy match (>= 90 ratio)
        res, finding = resolve_customer("Công ty Giải pháp Phần mềm ABC Việt Nam", store=self.store)
        self.assertIsNotNone(res)
        self.assertEqual(res.code, "CUST-ABC-99")
        self.assertIsNotNone(finding)
        self.assertEqual(finding.code, CUSTOMER_FUZZY_MATCHED)
        self.assertEqual(finding.severity, "warning")

        # 6. Unresolved (< 90 ratio)
        res, finding = resolve_customer("Công ty Cổ phần Thép Xây Dựng Miền Trung 999", store=self.store)
        self.assertIsNone(res)
        self.assertIsNotNone(finding)
        self.assertEqual(finding.code, CUSTOMER_UNRESOLVED)
        self.assertEqual(finding.severity, "error")

    def test_order_upload_and_alias_learning(self):
        # Register a master customer
        cust = CustomerMaster(
            code="CUST-KHACH-1",
            name="Công ty TNHH Sao Mai Vàng Bến Tre",
            tax_code="0999888777",
            tier="STANDARD",
            aliases=["Sao Mai Vàng Bến Tre"],
        )
        self.store.create_customer(cust)

        # Upload order with completely unknown customer name
        raw_cust_name = "Tập đoàn Bất động sản Mặt Trời Mọc 999"
        po_payload = {
            "po_number": "PO-TEST-UNRESOLVED-01",
            "customer": raw_cust_name,
            "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000}],
            "currency": "VND",
        }
        resp = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order.json", json.dumps(po_payload).encode("utf-8"), "application/json")},
            headers=self.auth_headers,
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["status"], "extraction_review")
        finding_codes = [f["code"] for f in data["findings"]]
        self.assertIn(CUSTOMER_UNRESOLVED, finding_codes)

        order_id = data["id"]

        # Human operator confirms extraction and maps it to CUST-KHACH-1
        confirm_resp = self.client.post(
            f"/api/v1/orders/{order_id}/confirm-extraction",
            json={
                "customer": "CUST-KHACH-1",
                "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000}],
            },
            headers=self.auth_headers,
        )
        self.assertEqual(confirm_resp.status_code, 200)

        # Next upload with that same unknown raw name now resolves at Tier-0
        resolved, finding = resolve_customer(raw_cust_name, store=self.store)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.code, "CUST-KHACH-1")
        self.assertIsNone(finding)

    def test_per_customer_sku_alias_learning(self):
        catalog = {
            "CAB-CAT6-3M": Product(
                sku="CAB-CAT6-3M",
                name="Cáp mạng Cat6 3m",
                unit_price=Decimal("45000"),
                stock=500,
                active=True,
            )
        }
        matcher = HybridSKUMatcher(catalog, store=self.store)

        # Learn alias for Customer A
        self.store.learn_alias(customer_id="CUST-AAA", raw_query="dây mạng 3m xanh", target_sku="CAB-CAT6-3M")

        # Customer A resolves at Tier-0
        res_a = matcher.resolve("dây mạng 3m xanh", customer_id="CUST-AAA")
        self.assertEqual(res_a.matched_sku, "CAB-CAT6-3M")
        self.assertEqual(res_a.confidence_score, 1.0)
        self.assertTrue("Active Learning" in res_a.explanation)

        # Customer B does not match Tier-0
        res_b = matcher.resolve("dây mạng 3m xanh", customer_id="CUST-BBB")
        self.assertFalse("Active Learning" in res_b.explanation)

    def test_customer_crud_api(self):
        # 1. Create
        create_payload = {
            "code": "CUST-CRUD-01",
            "name": "Công ty TNHH Phát Triển Công Nghệ Việt",
            "tax_code": "0108889999",
            "tier": "VIP",
            "aliases": ["Công nghệ Việt", "Việt Tech"],
        }
        res = self.client.post("/api/v1/customers", json=create_payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["code"], "CUST-CRUD-01")
        self.assertEqual(len(data["aliases"]), 2)

        # 2. List
        list_res = self.client.get("/api/v1/customers?search=Việt", headers=self.auth_headers)
        self.assertEqual(list_res.status_code, 200)
        items = list_res.json()
        self.assertTrue(any(it["code"] == "CUST-CRUD-01" for it in items))

        # 3. Get Detail
        get_res = self.client.get("/api/v1/customers/CUST-CRUD-01", headers=self.auth_headers)
        self.assertEqual(get_res.status_code, 200)
        detail = get_res.json()
        self.assertEqual(detail["name"], "Công ty TNHH Phát Triển Công Nghệ Việt")

        # 4. Update
        update_res = self.client.put(
            "/api/v1/customers/CUST-CRUD-01",
            json={"name": "Công ty CP Công Nghệ Việt Nam", "tier": "PLATINUM"},
            headers=self.auth_headers,
        )
        self.assertEqual(update_res.status_code, 200)
        updated = update_res.json()
        self.assertEqual(updated["tier"], "PLATINUM")
        self.assertEqual(updated["name"], "Công ty CP Công Nghệ Việt Nam")

        # 5. Delete
        del_res = self.client.delete("/api/v1/customers/CUST-CRUD-01", headers=self.auth_headers)
        self.assertEqual(del_res.status_code, 204)

        get_again = self.client.get("/api/v1/customers/CUST-CRUD-01", headers=self.auth_headers)
        self.assertEqual(get_again.status_code, 404)

    def test_customer_csv_import_export(self):
        csv_data = "code,name,tax_code,tier,aliases\nCUST-CSV-1,Cty CSV One,0111222333,VIP,One;CSV1\nCUST-CSV-2,Cty CSV Two,0222333444,STANDARD,Two;CSV2\n"
        imp_res = self.client.post(
            "/api/v1/customers/import-csv",
            files={"file": ("customers.csv", csv_data.encode("utf-8"), "text/csv")},
            headers=self.auth_headers,
        )
        self.assertEqual(imp_res.status_code, 200)
        self.assertEqual(imp_res.json()["imported_count"], 2)

        exp_res = self.client.get("/api/v1/customers/export-csv", headers=self.auth_headers)
        self.assertEqual(exp_res.status_code, 200)
        self.assertIn("CUST-CSV-1", exp_res.text)
        self.assertIn("CUST-CSV-2", exp_res.text)

    def test_no_hardcoded_customer_brands_in_src(self):
        # Verify that grep in src/ does not contain NORTHSTAR, VINGROUP, ACME
        forbidden_keywords = ["NORTHSTAR", "VINGROUP", "ACME"]
        src_path = Path("src")
        for root, _, files in os.walk(src_path):
            for file in files:
                if file.endswith((".py", ".json", ".md")):
                    fpath = Path(root) / file
                    content = fpath.read_text(encoding="utf-8")
                    for kw in forbidden_keywords:
                        self.assertNotIn(
                            kw,
                            content,
                            f"Hardcoded keyword '{kw}' found in source code file {fpath}",
                        )


if __name__ == "__main__":
    unittest.main()
