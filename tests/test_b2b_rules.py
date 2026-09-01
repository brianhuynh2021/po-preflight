from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.models import (
    CustomerCreditProfile,
    CustomerPriceAgreement,
    LineItem,
    Order,
    Product,
    UOMConversion,
)
from preflight.rules import analyze_order
from preflight.store import AuditStore


class TestB2BRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = {
            "LAPTOP-A14": Product(
                sku="LAPTOP-A14",
                name="A14 Business Laptop",
                unit_price=Decimal("18500000"),
                stock=50,
                active=True,
                base_uom="PCS",
                moq=2,
                pack_size=1,
            ),
            "CAB-CAT6-3M": Product(
                sku="CAB-CAT6-3M",
                name="Cat6 Ethernet Patch Cable 3m",
                unit_price=Decimal("72000"),
                stock=100,
                active=True,
                base_uom="PCS",
                moq=10,
                pack_size=5,
            ),
        }
        cls.client = TestClient(app)

    # -----------------------------------------------------------------
    # Issue #72: Contract Price Lists & Volume Tier Discounts
    # -----------------------------------------------------------------

    def test_customer_contract_price_agreement_avoids_mismatch(self):
        """VIP customer with special contracted price of 17,000,000 VND does not trigger price mismatch."""
        order = Order(
            po_number="PO-VIP-01",
            customer="VIP Northstar Retail",
            items=(LineItem(sku="LAPTOP-A14", quantity=5, unit_price=Decimal("17000000")),),
        )
        agreement = CustomerPriceAgreement(
            customer_id="VIP Northstar Retail",
            sku="LAPTOP-A14",
            contract_price=Decimal("17000000"),
            min_quantity=1,
        )
        # Without agreement: triggers PRICE_MISMATCH against 18,500,000 VND
        analysis_std = analyze_order(order, self.catalog)
        self.assertTrue(any(f.code == "PRICE_MISMATCH" for f in analysis_std.findings))

        # With agreement: passes cleanly
        analysis_vip = analyze_order(order, self.catalog, pricing_agreements=[agreement])
        self.assertFalse(any(f.code == "PRICE_MISMATCH" for f in analysis_vip.findings))

    def test_customer_volume_discount_tier_calculation(self):
        """Buying >= 10 units unlocks a 5% volume discount (18,500,000 * 0.95 = 17,575,000 VND)."""
        agreement = CustomerPriceAgreement(
            customer_id="Vingroup Retail",
            sku="LAPTOP-A14",
            contract_price=Decimal("18500000"),
            min_quantity=10,
            discount_percent=Decimal("5"),
        )
        # Order 10 laptops at 17,575,000 VND
        order = Order(
            po_number="PO-VOL-01",
            customer="Vingroup Retail",
            items=(LineItem(sku="LAPTOP-A14", quantity=10, unit_price=Decimal("17575000")),),
        )
        analysis = analyze_order(order, self.catalog, pricing_agreements=[agreement])
        self.assertFalse(any(f.code == "PRICE_MISMATCH" for f in analysis.findings))

    # -----------------------------------------------------------------
    # Issue #73: UOM Conversion Matrix & MOQ / Pack Multiplier
    # -----------------------------------------------------------------

    def test_uom_conversion_multiplies_base_quantity_for_stock(self):
        """Ordering 6 CARTON of cables (1 CARTON = 20 PCS -> 120 PCS) when stock is 100 flags INSUFFICIENT_STOCK."""
        order = Order(
            po_number="PO-UOM-01",
            customer="Telecom Corp",
            items=(LineItem(sku="CAB-CAT6-3M", quantity=6, unit_price=Decimal("1440000"), uom="CARTON"),),
        )
        uom_conv = UOMConversion(
            sku="CAB-CAT6-3M",
            uom_code="CARTON",
            base_uom="PCS",
            conversion_factor=Decimal("20"),
        )
        analysis = analyze_order(order, self.catalog, uom_conversions=[uom_conv])
        stock_findings = [f for f in analysis.findings if f.code == "INSUFFICIENT_STOCK"]
        self.assertEqual(len(stock_findings), 1)
        self.assertIn("120 PCS", stock_findings[0].message)

    def test_moq_and_pack_size_violations(self):
        """Ordering below MOQ or uneven pack sizing raises specific warnings."""
        # 1. Below MOQ (ordered 1 PCS, MOQ is 10)
        order_moq = Order(
            po_number="PO-MOQ-01",
            customer="Retail Shop",
            items=(LineItem(sku="CAB-CAT6-3M", quantity=1, unit_price=Decimal("72000"), uom="PCS"),),
        )
        analysis_moq = analyze_order(order_moq, self.catalog)
        self.assertTrue(any(f.code == "BELOW_MOQ" for f in analysis_moq.findings))

        # 2. Uneven Pack Size (ordered 12 PCS, pack_size is 5)
        order_pack = Order(
            po_number="PO-PACK-01",
            customer="Retail Shop",
            items=(LineItem(sku="CAB-CAT6-3M", quantity=12, unit_price=Decimal("72000"), uom="PCS"),),
        )
        analysis_pack = analyze_order(order_pack, self.catalog)
        self.assertTrue(any(f.code == "INVALID_PACK_SIZE" for f in analysis_pack.findings))

    # -----------------------------------------------------------------
    # Issue #74: Customer Credit Limit, Balance & Overdue Debt
    # -----------------------------------------------------------------

    def test_blocked_customer_status_blocks_order(self):
        """Customer with BLOCKED credit status is immediately rejected."""
        credit = CustomerCreditProfile(
            customer_id="Delinquent Corp",
            credit_limit=Decimal("50000000"),
            outstanding_balance=Decimal("10000000"),
            overdue_balance=Decimal("0"),
            status="BLOCKED",
        )
        order = Order(
            po_number="PO-BLK-01",
            customer="Delinquent Corp",
            items=(LineItem(sku="LAPTOP-A14", quantity=2, unit_price=Decimal("18500000")),),
        )
        analysis = analyze_order(order, self.catalog, customer_credit=credit)
        self.assertEqual(analysis.status, "blocked")
        self.assertTrue(any(f.code == "CUSTOMER_BLOCKED" for f in analysis.findings))

    def test_overdue_debt_aging_blocks_order(self):
        """Customer with overdue debt aged > 30 days is blocked."""
        credit = CustomerCreditProfile(
            customer_id="Slow Payer Co",
            credit_limit=Decimal("100000000"),
            outstanding_balance=Decimal("40000000"),
            overdue_balance=Decimal("15000000"),
            oldest_overdue_days=45,
            status="ACTIVE",
        )
        order = Order(
            po_number="PO-DEBT-01",
            customer="Slow Payer Co",
            items=(LineItem(sku="LAPTOP-A14", quantity=2, unit_price=Decimal("18500000")),),
        )
        analysis = analyze_order(order, self.catalog, customer_credit=credit)
        self.assertEqual(analysis.status, "blocked")
        self.assertTrue(any(f.code == "OVERDUE_DEBT_BLOCKED" for f in analysis.findings))

    def test_credit_limit_exceeded_exposure(self):
        """Order pushing total exposure over credit limit raises CREDIT_LIMIT_EXCEEDED."""
        credit = CustomerCreditProfile(
            customer_id="Small Business",
            credit_limit=Decimal("30000000"),
            outstanding_balance=Decimal("20000000"),
            overdue_balance=Decimal("0"),
            oldest_overdue_days=0,
            status="ACTIVE",
        )
        # Order value 37,000,000 VND + 20,000,000 outstanding = 57,000,000 exposure (limit 30M -> deficit 27M)
        order = Order(
            po_number="PO-EXCEED-01",
            customer="Small Business",
            items=(LineItem(sku="LAPTOP-A14", quantity=2, unit_price=Decimal("18500000")),),
        )
        analysis = analyze_order(order, self.catalog, customer_credit=credit)
        credit_findings = [f for f in analysis.findings if f.code == "CREDIT_LIMIT_EXCEEDED"]
        self.assertEqual(len(credit_findings), 1)
        self.assertIn("57,000,000 VND", credit_findings[0].message)

    # -----------------------------------------------------------------
    # B2B Store Persistence & REST API Endpoints
    # -----------------------------------------------------------------

    def test_b2b_store_persistence(self):
        """Test storing and querying pricing, UOM, and credit in AuditStore."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tf:
            store = AuditStore(tf.name)

            # 1. Pricing
            pa = CustomerPriceAgreement(
                customer_id="CUST-001",
                sku="LAPTOP-A14",
                contract_price=Decimal("17200000"),
                min_quantity=5,
                discount_percent=Decimal("3.5"),
            )
            store.set_customer_pricing(pa)
            prices = store.get_customer_pricing("CUST-001")
            self.assertEqual(len(prices), 1)
            self.assertEqual(prices[0].contract_price, Decimal("17200000"))

            # 2. UOM
            uom = UOMConversion(
                sku="CAB-CAT6-3M",
                uom_code="BOX",
                base_uom="PCS",
                conversion_factor=Decimal("10"),
            )
            store.set_uom_conversion(uom)
            uoms = store.get_uom_conversions("CAB-CAT6-3M")
            self.assertEqual(len(uoms), 1)
            self.assertEqual(uoms[0].conversion_factor, Decimal("10"))

            # 3. Credit
            credit = CustomerCreditProfile(
                customer_id="CUST-001",
                credit_limit=Decimal("500000000"),
                outstanding_balance=Decimal("120000000"),
                overdue_balance=Decimal("0"),
                oldest_overdue_days=0,
                status="ACTIVE",
            )
            store.set_customer_credit(credit)
            fetched_credit = store.get_customer_credit("CUST-001")
            self.assertIsNotNone(fetched_credit)
            self.assertEqual(fetched_credit.credit_limit, Decimal("500000000"))
            self.assertEqual(fetched_credit.available_credit, Decimal("380000000"))

    def test_b2b_api_endpoints(self):
        """Test REST API endpoints for customer pricing, credit, and UOM."""
        # 1. POST /api/v1/customers/CUST-API-1/prices
        price_payload = {
            "sku": "LAPTOP-A14",
            "contract_price": "16800000",
            "min_quantity": 2,
            "discount_percent": "2.0",
        }
        res = self.client.post(
            "/api/v1/customers/CUST-API-1/prices",
            json=price_payload,
            headers={"X-API-Key": "pf_dev_mgr_8802"},
        )
        self.assertEqual(res.status_code, 201)

        # 2. GET /api/v1/customers/CUST-API-1/prices
        res_get_price = self.client.get(
            "/api/v1/customers/CUST-API-1/prices",
            headers={"X-API-Key": "pf_dev_view_6604"},
        )
        self.assertEqual(res_get_price.status_code, 200)
        self.assertEqual(len(res_get_price.json()), 1)

        # 3. POST /api/v1/customers/CUST-API-1/credit
        credit_payload = {
            "credit_limit": "200000000",
            "outstanding_balance": "50000000",
            "overdue_balance": "0",
            "oldest_overdue_days": 0,
            "status": "ACTIVE",
        }
        res_credit = self.client.post(
            "/api/v1/customers/CUST-API-1/credit",
            json=credit_payload,
            headers={"X-API-Key": "pf_dev_mgr_8802"},
        )
        self.assertEqual(res_credit.status_code, 200)

        # 4. GET /api/v1/customers/CUST-API-1/credit
        res_get_credit = self.client.get(
            "/api/v1/customers/CUST-API-1/credit",
            headers={"X-API-Key": "pf_dev_view_6604"},
        )
        self.assertEqual(res_get_credit.status_code, 200)
        self.assertEqual(res_get_credit.json()["available_credit"], "150000000")

        # 5. POST /api/v1/uom/conversions
        uom_payload = {
            "sku": "CAB-CAT6-3M",
            "uom_code": "PACK",
            "base_uom": "PCS",
            "conversion_factor": "5",
        }
        res_uom = self.client.post(
            "/api/v1/uom/conversions",
            json=uom_payload,
            headers={"X-API-Key": "pf_dev_mgr_8802"},
        )
        self.assertEqual(res_uom.status_code, 201)



if __name__ == "__main__":
    unittest.main()
