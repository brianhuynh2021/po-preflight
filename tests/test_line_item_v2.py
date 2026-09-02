from decimal import Decimal
import unittest

from preflight.ingestion.schemas import ExtractedLineItem, ExtractedOrderHeader
from preflight.ingestion.verifier import SelfReflectionVerifier
from preflight.models import LineItem, Order, Product, RulePolicy
from preflight.parsers import _decimal, parse_csv, parse_json
from preflight.rules import analyze_order
from preflight.rules_context import RuleContext


class TestLineItemV2(unittest.TestCase):
    def setUp(self):
        self.catalog = {
            "LAPTOP-A14": Product(
                sku="LAPTOP-A14",
                name="A14 Business Laptop",
                unit_price=Decimal("18500000"),
                stock=20,
            ),
            "MONITOR-27": Product(
                sku="MONITOR-27",
                name="27-inch Monitor",
                unit_price=Decimal("6200000"),
                stock=15,
            ),
            "CAB-CAT6-3M": Product(
                sku="CAB-CAT6-3M",
                name="Cat6 Ethernet Cable",
                unit_price=Decimal("72000"),
                stock=100,
            ),
        }

    def test_line_item_and_order_calculations(self):
        item1 = LineItem(
            sku="LAPTOP-A14",
            quantity=2,
            unit_price=Decimal("18500000"),
            discount_percent=Decimal("5"),  # 5% of 37,000,000 = 1,850,000 -> net = 35,150,000
            tax_rate=Decimal("10"),  # 10% of 35,150,000 = 3,515,000 -> total = 38,665,000
        )
        self.assertEqual(item1.line_net, Decimal("35150000"))
        self.assertEqual(item1.line_tax, Decimal("3515000"))
        self.assertEqual(item1.line_total, Decimal("38665000"))

        item_promo = LineItem(
            sku="CAB-CAT6-3M",
            quantity=5,
            unit_price=Decimal("0"),
            is_promo=True,
            tax_rate=Decimal("0"),
        )
        self.assertEqual(item_promo.line_net, Decimal("0"))
        self.assertEqual(item_promo.line_tax, Decimal("0"))
        self.assertEqual(item_promo.line_total, Decimal("0"))

        order = Order(
            po_number="PO-TEST-001",
            customer="Acme Corp",
            items=(item1, item_promo),
            header_discount_amount=Decimal("150000"),
            shipping_fee=Decimal("50000"),
        )
        self.assertEqual(order.subtotal, Decimal("35000000"))  # 35,150,000 - 150,000
        self.assertEqual(order.tax_amount, Decimal("3515000"))
        self.assertEqual(order.grand_total, Decimal("38565000"))  # 35,000,000 + 3,515,000 + 50,000

    def test_vietnamese_number_parsing(self):
        self.assertEqual(_decimal("1.250.000"), Decimal("1250000"))
        self.assertEqual(_decimal("1,250,000"), Decimal("1250000"))
        self.assertEqual(_decimal("1.250.000,50"), Decimal("1250000.50"))
        self.assertEqual(_decimal("1 250 000"), Decimal("1250000"))
        self.assertEqual(_decimal("1,250,000.50"), Decimal("1250000.50"))
        self.assertEqual(_decimal("18.500.000 đ"), Decimal("18500000"))
        self.assertEqual(_decimal("450000"), Decimal("450000"))

    def test_promo_line_skips_price_mismatch(self):
        order = Order(
            po_number="PO-PROMO-01",
            customer="Test Customer",
            items=(
                LineItem(
                    sku="LAPTOP-A14",
                    quantity=1,
                    unit_price=Decimal("18500000"),
                    tax_rate=Decimal("10"),
                ),
                LineItem(
                    sku="CAB-CAT6-3M",
                    quantity=2,
                    unit_price=Decimal("0"),
                    is_promo=True,
                    description="Hàng tặng kèm",
                ),
            ),
        )
        analysis = analyze_order(order, self.catalog)
        self.assertEqual(analysis.status, "ready_for_approval")
        promo_findings = [f for f in analysis.findings if f.code == "PROMO_LINE"]
        self.assertEqual(len(promo_findings), 1)
        self.assertEqual(promo_findings[0].severity, "info")
        self.assertEqual(promo_findings[0].sku, "CAB-CAT6-3M")
        # Ensure no PRICE_MISMATCH was generated for promo line
        price_findings = [f for f in analysis.findings if f.code == "PRICE_MISMATCH"]
        self.assertEqual(len(price_findings), 0)

    def test_discount_exceeds_policy(self):
        order = Order(
            po_number="PO-DISC-01",
            customer="Test Customer",
            items=(
                LineItem(
                    sku="LAPTOP-A14",
                    quantity=1,
                    unit_price=Decimal("18500000"),
                    discount_percent=Decimal("25"),  # Exceeds default 15%
                    tax_rate=Decimal("10"),
                ),
            ),
        )
        ctx = RuleContext(catalog=self.catalog, max_discount_percent=Decimal("15"))
        analysis = analyze_order(order, ctx)
        self.assertEqual(analysis.status, "review_required")
        disc_findings = [f for f in analysis.findings if f.code == "DISCOUNT_EXCEEDS_POLICY"]
        self.assertEqual(len(disc_findings), 1)
        self.assertEqual(disc_findings[0].severity, "warning")

    def test_invalid_tax_rate_blocks_order(self):
        order = Order(
            po_number="PO-TAX-01",
            customer="Test Customer",
            items=(
                LineItem(
                    sku="LAPTOP-A14",
                    quantity=1,
                    unit_price=Decimal("18500000"),
                    tax_rate=Decimal("7"),  # Invalid tax rate in Vietnam
                ),
            ),
        )
        analysis = analyze_order(order, self.catalog)
        self.assertEqual(analysis.status, "blocked")
        tax_findings = [f for f in analysis.findings if f.code == "TAX_RATE_INVALID"]
        self.assertEqual(len(tax_findings), 1)
        self.assertEqual(tax_findings[0].severity, "error")

    def test_total_mismatch_warning(self):
        order = Order(
            po_number="PO-MISMATCH-01",
            customer="Test Customer",
            declared_total=Decimal("25000000"),  # Actual grand total is 18.5M * 1.1 = 20.35M
            items=(
                LineItem(
                    sku="LAPTOP-A14",
                    quantity=1,
                    unit_price=Decimal("18500000"),
                    tax_rate=Decimal("10"),
                ),
            ),
        )
        analysis = analyze_order(order, self.catalog)
        self.assertEqual(analysis.status, "review_required")
        mismatch_findings = [f for f in analysis.findings if f.code == "TOTAL_MISMATCH"]
        self.assertEqual(len(mismatch_findings), 1)
        self.assertEqual(mismatch_findings[0].severity, "warning")
        self.assertIn("4,650,000 VND", mismatch_findings[0].message)

    def test_multi_currency_message_formatting(self):
        order_usd = Order(
            po_number="PO-USD-01",
            customer="Global Client",
            currency="USD",
            declared_total=Decimal("1000.00"),
            items=(
                LineItem(
                    sku="LAPTOP-A14",
                    quantity=1,
                    unit_price=Decimal("800.00"),
                    tax_rate=Decimal("0"),
                ),
            ),
        )
        analysis = analyze_order(order_usd, self.catalog)
        mismatch_findings = [f for f in analysis.findings if f.code == "TOTAL_MISMATCH"]
        self.assertEqual(len(mismatch_findings), 1)
        self.assertIn("USD", mismatch_findings[0].message)

    def test_self_reflection_verifier_math(self):
        verifier = SelfReflectionVerifier()
        header = ExtractedOrderHeader(
            po_number="PO-001",
            customer="Test",
            currency="VND",
            subtotal=Decimal("20350000"),
            tax_amount=Decimal("0"),
            grand_total=Decimal("20350000"),
        )
        items = [
            ExtractedLineItem(
                sku="LAPTOP-A14",
                description="Laptop",
                quantity=1,
                unit_price=Decimal("18500000"),
                amount=Decimal("20350000"),  # including tax
            )
        ]
        result = verifier.verify(header, items)
        self.assertTrue(result.is_valid)
        self.assertFalse(result.discrepancy_detected)


if __name__ == "__main__":
    unittest.main()
