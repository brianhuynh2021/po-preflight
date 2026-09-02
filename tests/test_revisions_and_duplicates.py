from decimal import Decimal
import io
import json
import unittest

from fastapi.testclient import TestClient

from preflight.api.app import app
from preflight.models import LineItem, Order, Product
from preflight.rules import analyze_order
from preflight.rules_context import RuleContext
from preflight.store import AuditStore
from preflight.utils.order_diff import compute_order_diff


class TestRevisionsAndDuplicates(unittest.TestCase):
    def setUp(self):
        self.store = AuditStore(":memory:")
        self.catalog = {
            "LAPTOP-A14": Product(
                sku="LAPTOP-A14",
                name="A14 Business Laptop",
                unit_price=Decimal("18500000"),
                stock=50,
            ),
            "MONITOR-27": Product(
                sku="MONITOR-27",
                name="27-inch Monitor",
                unit_price=Decimal("6200000"),
                stock=30,
            ),
            "CAB-CAT6-3M": Product(
                sku="CAB-CAT6-3M",
                name="Ethernet Cable 3M",
                unit_price=Decimal("75000"),
                stock=100,
            ),
        }
        self.client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})

    def test_compute_order_diff(self):
        old_order = Order(
            po_number="PO-REV-01",
            customer="Acme Corp",
            items=(
                LineItem(sku="LAPTOP-A14", quantity=10, unit_price=Decimal("18500000")),
                LineItem(sku="MONITOR-27", quantity=5, unit_price=Decimal("6200000")),
            ),
        )
        new_order = Order(
            po_number="PO-REV-01",
            customer="Acme Corp",
            items=(
                LineItem(sku="LAPTOP-A14", quantity=8, unit_price=Decimal("18500000")),
                LineItem(sku="CAB-CAT6-3M", quantity=2, unit_price=Decimal("75000")),
            ),
        )
        diff = compute_order_diff(old_order, new_order)
        self.assertIn("LAPTOP-A14: 10 → 8", diff["summary"])
        self.assertIn("- MONITOR-27: đã xóa", diff["summary"])
        self.assertIn("+ CAB-CAT6-3M: thêm mới", diff["summary"])

    def test_reupload_after_needs_changes_creates_revision_and_supersedes(self):
        # 1. First upload
        po_payload_1 = {
            "po_number": "PO-10428-TEST",
            "customer": "Alpha Corp",
            "items": [
                {"sku": "LAPTOP-A14", "quantity": 10, "unit_price": "18500000"},
            ],
        }
        file_1 = io.BytesIO(json.dumps(po_payload_1).encode("utf-8"))
        res_1 = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order-1.json", file_1, "application/json")},
        )
        self.assertEqual(res_1.status_code, 201)
        order_1_id = res_1.json()["id"]

        # 2. Manager requests changes
        res_dec = self.client.post(
            f"/api/v1/orders/{order_1_id}/decide",
            json={"decision": "needs_changes", "note": "Vui lòng giảm số lượng Laptop xuống 8 cái do hết ngân sách."},
        )
        self.assertEqual(res_dec.status_code, 200)

        # 3. Customer uploads revised PO with quantity 8
        po_payload_2 = {
            "po_number": "PO-10428-TEST",
            "customer": "Alpha Corp",
            "items": [
                {"sku": "LAPTOP-A14", "quantity": 8, "unit_price": "18500000"},
            ],
        }
        file_2 = io.BytesIO(json.dumps(po_payload_2).encode("utf-8"))
        res_2 = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order-2.json", file_2, "application/json")},
        )
        self.assertEqual(res_2.status_code, 201)
        data_2 = res_2.json()
        self.assertEqual(data_2["revision"], 2)
        self.assertEqual(data_2["supersedes_order_id"], order_1_id)

        findings_codes = [f["code"] for f in data_2["findings"]]
        self.assertNotIn("DUPLICATE_PO", findings_codes)
        self.assertIn("REVISED_ORDER", findings_codes)

        # 4. Old order status is superseded and not in default queue
        res_list = self.client.get("/api/v1/orders")
        self.assertEqual(res_list.status_code, 200)
        listed_ids = [o["id"] for o in res_list.json()]
        self.assertIn(data_2["id"], listed_ids)
        self.assertNotIn(order_1_id, listed_ids)

    def test_reupload_after_approved_triggers_duplicate_po_error(self):
        po_payload = {
            "po_number": "PO-APPROVED-DUP",
            "customer": "Beta Corp",
            "items": [
                {"sku": "LAPTOP-A14", "quantity": 2, "unit_price": "18500000"},
            ],
        }
        # First upload
        file_1 = io.BytesIO(json.dumps(po_payload).encode("utf-8"))
        res_1 = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order-1.json", file_1, "application/json")},
        )
        self.assertEqual(res_1.status_code, 201)
        order_id = res_1.json()["id"]

        # Approve
        self.client.post(
            f"/api/v1/orders/{order_id}/decide",
            json={"decision": "approved", "note": "Approved order for customer."},
        )

        # Second upload with same PO number
        file_2 = io.BytesIO(json.dumps(po_payload).encode("utf-8"))
        res_2 = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order-2.json", file_2, "application/json")},
        )
        self.assertEqual(res_2.status_code, 201)
        data_2 = res_2.json()
        self.assertEqual(data_2["status"], "blocked")
        findings_codes = [f["code"] for f in data_2["findings"]]
        self.assertIn("DUPLICATE_PO", findings_codes)

    def test_reupload_pending_order_conflict_reject_and_revise(self):
        po_payload = {
            "po_number": "PO-PENDING-CONFLICT",
            "customer": "Gamma Corp",
            "items": [
                {"sku": "LAPTOP-A14", "quantity": 3, "unit_price": "18500000"},
            ],
        }
        # First upload
        file_1 = io.BytesIO(json.dumps(po_payload).encode("utf-8"))
        res_1 = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order-1.json", file_1, "application/json")},
        )
        self.assertEqual(res_1.status_code, 201)
        order_1_id = res_1.json()["id"]

        # 2. Upload without on_conflict -> default reject -> 409 DUPLICATE_PENDING
        file_2 = io.BytesIO(json.dumps(po_payload).encode("utf-8"))
        res_conflict = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order-2.json", file_2, "application/json")},
        )
        self.assertEqual(res_conflict.status_code, 409)
        err_body = res_conflict.json()
        self.assertEqual(err_body["code"], "DUPLICATE_PENDING")
        self.assertEqual(err_body["existing_order_id"], order_1_id)

        # 3. Upload with on_conflict=revise -> revision 2
        file_3 = io.BytesIO(json.dumps(po_payload).encode("utf-8"))
        res_revise = self.client.post(
            "/api/v1/orders/upload?on_conflict=revise",
            files={"file": ("order-3.json", file_3, "application/json")},
        )
        self.assertEqual(res_revise.status_code, 201)
        data_rev = res_revise.json()
        self.assertEqual(data_rev["revision"], 2)
        self.assertEqual(data_rev["supersedes_order_id"], order_1_id)

    def test_different_customers_same_po_number_independent(self):
        po_1 = {
            "po_number": "PO-SHARED-001",
            "customer": "Customer Alpha",
            "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": "18500000"}],
        }
        po_2 = {
            "po_number": "PO-SHARED-001",
            "customer": "Customer Beta",
            "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": "18500000"}],
        }
        res_1 = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order-1.json", io.BytesIO(json.dumps(po_1).encode("utf-8")), "application/json")},
        )
        self.assertEqual(res_1.status_code, 201)

        res_2 = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("order-2.json", io.BytesIO(json.dumps(po_2).encode("utf-8")), "application/json")},
        )
        self.assertEqual(res_2.status_code, 201)
        data_2 = res_2.json()
        # Customer Beta PO-SHARED-001 is completely independent
        self.assertEqual(data_2["revision"], 1)
        self.assertIsNone(data_2["supersedes_order_id"])
        self.assertNotIn("DUPLICATE_PO", [f["code"] for f in data_2["findings"]])

    def test_near_duplicate_detection(self):
        # Candidate order placed 2 days ago
        cand_order = Order(
            po_number="PO-CANDIDATE-01",
            customer="Delta Corp",
            order_date="2026-08-30",
            items=(
                LineItem(sku="LAPTOP-A14", quantity=5, unit_price=Decimal("18500000")),
                LineItem(sku="MONITOR-27", quantity=2, unit_price=Decimal("6200000")),
                LineItem(sku="CAB-CAT6-3M", quantity=10, unit_price=Decimal("75000")),
            ),
        )
        # New order from same customer with different PO number and identical items
        new_order = Order(
            po_number="PO-NEW-02",
            customer="Delta Corp",
            order_date="2026-09-01",
            items=(
                LineItem(sku="LAPTOP-A14", quantity=5, unit_price=Decimal("18500000")),
                LineItem(sku="MONITOR-27", quantity=2, unit_price=Decimal("6200000")),
                LineItem(sku="CAB-CAT6-3M", quantity=10, unit_price=Decimal("75000")),
            ),
        )
        ctx = RuleContext(
            catalog=self.catalog,
            recent_customer_orders=(cand_order,),
            order_date="2026-09-01",
        )
        analysis = analyze_order(new_order, ctx)
        codes = [f.code for f in analysis.findings]
        self.assertIn("POSSIBLE_DUPLICATE", codes)

        dup_finding = next(f for f in analysis.findings if f.code == "POSSIBLE_DUPLICATE")
        self.assertIsInstance(dup_finding.evidence, dict)
        self.assertEqual(dup_finding.evidence["matched_po"], "PO-CANDIDATE-01")


if __name__ == "__main__":
    unittest.main()
