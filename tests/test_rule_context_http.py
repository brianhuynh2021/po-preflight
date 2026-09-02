from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.api.deps import get_audit_store, get_catalog
from preflight.models import (
    CustomerCreditProfile,
    CustomerPriceAgreement,
    Product,
    RulePolicy,
    UOMConversion,
)
from preflight.store import AuditStore


class TestRuleContextHTTP(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_rule_context.db"
        self.store = AuditStore(self.db_path)

        self.catalog = {
            "LAPTOP-A14": Product(
                sku="LAPTOP-A14",
                name="Laptop Pro A14",
                unit_price=Decimal("18500000"),
                stock=10,
                active=True,
                base_uom="PCS",
                moq=1,
                pack_size=1,
            ),
            "CAB-CAT6-3M": Product(
                sku="CAB-CAT6-3M",
                name="Cáp Mạng Cat6 3m",
                unit_price=Decimal("45000"),
                stock=30,  # 30 PCS in stock
                active=True,
                base_uom="PCS",
                moq=1,
                pack_size=1,
            ),
            "OLD-SKU": Product(
                sku="OLD-SKU",
                name="Old Product",
                unit_price=Decimal("100000"),
                stock=50,
                active=False,
                base_uom="PCS",
            ),
        }

        self.app = app

        def override_store():
            yield self.store

        def override_catalog():
            return self.catalog

        self.app.dependency_overrides[get_audit_store] = override_store
        self.app.dependency_overrides[get_catalog] = override_catalog
        self.client = TestClient(self.app)
        self.headers = {"X-API-Key": "pf_dev_adm_9901"}


    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()
        self.store.close()
        self.temp_dir.cleanup()

    def test_customer_credit_blocked_intake(self) -> None:
        """a) set credit BLOCKED -> upload -> status 'blocked', contains CUSTOMER_BLOCKED."""
        self.store.set_customer_credit(
            CustomerCreditProfile(
                customer_id="CONG TY TNHH AN PHAT",
                credit_limit=Decimal("50000000"),
                outstanding_balance=Decimal("10000000"),
                overdue_balance=Decimal("0"),
                status="BLOCKED",
            )
        )


        po_content = json.dumps(
            {
                "po_number": "PO-CREDIT-01",
                "customer": "Công ty TNHH An Phát",
                "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000}],
            }
        ).encode("utf-8")

        response = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("po-credit.json", io.BytesIO(po_content), "application/json")},
            headers=self.headers,
        )
        self.assertIn(response.status_code, [200, 201])
        data = response.json()
        self.assertEqual(data["status"], "blocked")
        codes = [f["code"] for f in data["findings"]]
        self.assertIn("CUSTOMER_BLOCKED", codes)


    def test_customer_contract_pricing_agreement(self) -> None:
        """b) set contract price 17.000.000 for LAPTOP-A14 -> upload at 17.000.000 -> no PRICE_MISMATCH."""
        self.store.set_customer_pricing(
            CustomerPriceAgreement(
                customer_id="CONG TY TNHH VIET TIEN",
                sku="LAPTOP-A14",
                contract_price=Decimal("17000000"),
                min_quantity=1,
            )
        )

        po_content = json.dumps(
            {
                "po_number": "PO-PRICE-01",
                "customer": "Công ty TNHH Việt Tiến",
                "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 17000000}],
            }
        ).encode("utf-8")

        response = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("po-price.json", io.BytesIO(po_content), "application/json")},
            headers=self.headers,
        )
        self.assertIn(response.status_code, [200, 201])
        data = response.json()
        codes = [f["code"] for f in data["findings"]]
        self.assertNotIn("PRICE_MISMATCH", codes)

    def test_policy_price_tolerance_put_and_evaluate(self) -> None:
        """c) PUT /rules tolerance=10 -> upload variance 2.7% -> no PRICE_MISMATCH; tolerance=0 -> yes."""
        # 1. Default tolerance=0 -> variance 18.000.000 vs 18.500.000 (2.7%) flags PRICE_MISMATCH
        po_content = json.dumps(
            {
                "po_number": "PO-TOL-01",
                "customer": "Khách Vãng Lai",
                "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18000000}],
            }
        ).encode("utf-8")

        res1 = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("po-tol1.json", io.BytesIO(po_content), "application/json")},
            headers=self.headers,
        )
        self.assertIn(res1.status_code, [200, 201])
        codes1 = [f["code"] for f in res1.json()["findings"]]
        self.assertIn("PRICE_MISMATCH", codes1)

        # 2. Update policy to tolerance=10%
        put_res = self.client.put(
            "/api/v1/rules",
            json={"price_tolerance_percent": 10.0},
            headers=self.headers,
        )
        self.assertEqual(put_res.status_code, 200)

        # 3. Re-upload same price with new PO number -> within tolerance, no PRICE_MISMATCH
        po_content2 = json.dumps(
            {
                "po_number": "PO-TOL-02",
                "customer": "Khách Vãng Lai",
                "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18000000}],
            }
        ).encode("utf-8")

        res2 = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("po-tol2.json", io.BytesIO(po_content2), "application/json")},
            headers=self.headers,
        )
        self.assertIn(res2.status_code, [200, 201])
        codes2 = [f["code"] for f in res2.json()["findings"]]
        self.assertNotIn("PRICE_MISMATCH", codes2)

    def test_uom_conversion_stock_evaluation(self) -> None:
        """d) set uom CARTON=20 PCS for CAB-CAT6-3M -> upload qty 2 CARTON (40 PCS) -> stock=30 PCS -> INSUFFICIENT_STOCK."""
        self.store.set_uom_conversion(
            UOMConversion(
                sku="CAB-CAT6-3M",
                uom_code="CARTON",
                base_uom="PCS",
                conversion_factor=Decimal("20"),
            )
        )

        po_content = json.dumps(
            {
                "po_number": "PO-UOM-01",
                "customer": "Công ty Thiết Bị Mạng",
                "items": [{"sku": "CAB-CAT6-3M", "quantity": 2, "unit_price": 900000, "uom": "CARTON"}],
            }
        ).encode("utf-8")

        response = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("po-uom.json", io.BytesIO(po_content), "application/json")},
            headers=self.headers,
        )
        self.assertIn(response.status_code, [200, 201])
        data = response.json()
        codes = [f["code"] for f in data["findings"]]
        self.assertIn("INSUFFICIENT_STOCK", codes)
        stock_finding = next(f for f in data["findings"] if f["code"] == "INSUFFICIENT_STOCK")
        self.assertIn("40 PCS", stock_finding["message"])

    def test_policy_persists_across_store_reopen(self) -> None:
        """e) restart store (close/reopen) -> policy remains persisted."""
        self.store.set_policy(
            RulePolicy(
                price_tolerance_percent=Decimal("7.5"),
                stock_safety_margin=5,
                allow_inactive_sku=True,
            )
        )
        self.store.close()

        # Re-open from disk
        reopened_store = AuditStore(self.db_path)
        policy = reopened_store.get_policy()
        reopened_store.close()

        self.assertEqual(policy.price_tolerance_percent, Decimal("7.5"))
        self.assertEqual(policy.stock_safety_margin, 5)
        self.assertTrue(policy.allow_inactive_sku)

    def test_agent_run_inherits_credit_risk(self) -> None:
        """f) POST /agent/run with blocked customer -> risk_level HIGH, CUSTOMER_BLOCKED finding."""
        self.store.set_customer_credit(
            CustomerCreditProfile(
                customer_id="CONG TY NGUYEN PHAT",
                credit_limit=Decimal("100000000"),
                outstanding_balance=Decimal("20000000"),
                overdue_balance=Decimal("0"),
                status="BLOCKED",
            )
        )


        agent_req = {
            "po_number": "PO-AGENT-CREDIT",
            "customer": "Công ty Nguyễn Phát",
            "line_items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000}],
        }
        res = self.client.post("/api/v1/agent/run", json=agent_req, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["risk_level"], "HIGH")
        self.assertEqual(data["status"], "blocked")
        codes = [f["code"] for f in data["findings"]]
        self.assertIn("CUSTOMER_BLOCKED", codes)

    def test_fx_static_source_note_in_price_mismatch(self) -> None:
        """g) USD order with PREFLIGHT_FX_LIVE=false -> PRICE_MISMATCH contains 'tỷ giá tĩnh'."""
        os.environ["PREFLIGHT_FX_LIVE"] = "false"
        # LAPTOP-A14 target is 18.500.000 VND. Upload at 100 USD (= 2.540.000 VND at static 25.400)
        po_content = json.dumps(
            {
                "po_number": "PO-USD-STATIC",
                "customer": "US Global Client",
                "currency": "USD",
                "items": [{"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 100.0}],
            }
        ).encode("utf-8")

        response = self.client.post(
            "/api/v1/orders/upload",
            files={"file": ("po-usd.json", io.BytesIO(po_content), "application/json")},
            headers=self.headers,
        )
        self.assertIn(response.status_code, [200, 201])
        data = response.json()
        codes = [f["code"] for f in data["findings"]]
        self.assertIn("PRICE_MISMATCH", codes)
        fx_finding = next(f for f in data["findings"] if f["code"] == "PRICE_MISMATCH")
        self.assertIn("tỷ giá tĩnh", fx_finding["message"])



if __name__ == "__main__":
    unittest.main()
