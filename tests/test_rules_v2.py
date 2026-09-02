from datetime import datetime, timezone
from decimal import Decimal
import unittest

from preflight.findings_registry import FINDING_SPECS, registry
from preflight.models import (
    CustomerCreditProfile,
    CustomerPriceAgreement,
    LineItem,
    Order,
    Product,
    RulePolicy,
)
from preflight.rules import analyze_order
from preflight.rules_context import RuleContext


class TestRulesV2(unittest.TestCase):
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
        }

    def test_contract_price_expired_triggers_warning_and_catalog_fallback(self):
        # Contract price expired yesterday
        agreement = CustomerPriceAgreement(
            customer_id="Acme Corp",
            sku="LAPTOP-A14",
            contract_price=Decimal("17000000"),
            min_quantity=1,
            valid_from="2026-01-01",
            valid_to="2026-08-31",
        )
        order = Order(
            po_number="PO-AGR-01",
            customer="Acme Corp",
            order_date="2026-09-01",  # After valid_to
            items=(
                LineItem(
                    sku="LAPTOP-A14",
                    quantity=1,
                    unit_price=Decimal("17000000"),  # Expecting catalog price 18.5M
                ),
            ),
        )
        ctx = RuleContext(
            catalog=self.catalog,
            pricing_agreements=(agreement,),
            order_date="2026-09-01",
        )
        analysis = analyze_order(order, ctx)
        self.assertEqual(analysis.status, "review_required")
        codes = [f.code for f in analysis.findings]
        self.assertIn("CONTRACT_PRICE_EXPIRED", codes)
        self.assertIn("PRICE_MISMATCH", codes)

        exp_finding = next(f for f in analysis.findings if f.code == "CONTRACT_PRICE_EXPIRED")
        self.assertIsInstance(exp_finding.evidence, dict)
        self.assertGreaterEqual(len(exp_finding.evidence), 2)
        self.assertEqual(exp_finding.evidence["valid_to"], "2026-08-31")

    def test_contract_price_valid_and_volume_tiered(self):
        tier1 = CustomerPriceAgreement(
            customer_id="Acme Corp",
            sku="LAPTOP-A14",
            contract_price=Decimal("18000000"),
            min_quantity=1,
            valid_from="2026-01-01",
            valid_to="2026-12-31",
        )
        tier2 = CustomerPriceAgreement(
            customer_id="Acme Corp",
            sku="LAPTOP-A14",
            contract_price=Decimal("17000000"),
            min_quantity=5,
            valid_from="2026-01-01",
            valid_to="2026-12-31",
        )
        order = Order(
            po_number="PO-AGR-02",
            customer="Acme Corp",
            order_date="2026-09-01",
            items=(
                LineItem(
                    sku="LAPTOP-A14",
                    quantity=5,
                    unit_price=Decimal("17000000"),
                ),
            ),
        )
        ctx = RuleContext(
            catalog=self.catalog,
            pricing_agreements=(tier1, tier2),
            order_date="2026-09-01",
        )
        analysis = analyze_order(order, ctx)
        self.assertEqual(analysis.status, "ready_for_approval")
        price_findings = [f for f in analysis.findings if f.code == "PRICE_MISMATCH"]
        self.assertEqual(len(price_findings), 0)

    def test_credit_policy_overdue_grace_days_configuration(self):
        credit = CustomerCreditProfile(
            customer_id="Acme Corp",
            credit_limit=Decimal("100000000"),
            outstanding_balance=Decimal("20000000"),
            overdue_balance=Decimal("5000000"),
            oldest_overdue_days=40,
            status="ACTIVE",
        )
        order = Order(
            po_number="PO-CREDIT-01",
            customer="Acme Corp",
            items=(
                LineItem(
                    sku="LAPTOP-A14",
                    quantity=1,
                    unit_price=Decimal("18500000"),
                ),
            ),
        )

        # 1. Grace = 45 days -> 40 days overdue does not trigger OVERDUE_DEBT_BLOCKED
        ctx_45 = RuleContext(
            catalog=self.catalog,
            customer_credit=credit,
            overdue_grace_days=45,
        )
        analysis_45 = analyze_order(order, ctx_45)
        codes_45 = [f.code for f in analysis_45.findings]
        self.assertNotIn("OVERDUE_DEBT_BLOCKED", codes_45)

        # 2. Grace = 30 days -> 40 days overdue triggers OVERDUE_DEBT_BLOCKED (error)
        ctx_30 = RuleContext(
            catalog=self.catalog,
            customer_credit=credit,
            overdue_grace_days=30,
        )
        analysis_30 = analyze_order(order, ctx_30)
        codes_30 = [f.code for f in analysis_30.findings]
        self.assertIn("OVERDUE_DEBT_BLOCKED", codes_30)
        self.assertEqual(analysis_30.status, "blocked")

    def test_credit_hold_behaviour(self):
        credit = CustomerCreditProfile(
            customer_id="Acme Corp",
            credit_limit=Decimal("100000000"),
            status="ON_HOLD",
        )
        order = Order(
            po_number="PO-HOLD-01",
            customer="Acme Corp",
            items=(
                LineItem(
                    sku="LAPTOP-A14",
                    quantity=1,
                    unit_price=Decimal("18500000"),
                ),
            ),
        )

        # 1. Default credit_hold_behaviour = "review" -> Warning -> review_required
        ctx_review = RuleContext(
            catalog=self.catalog,
            customer_credit=credit,
            credit_hold_behaviour="review",
        )
        analysis_review = analyze_order(order, ctx_review)
        self.assertEqual(analysis_review.status, "review_required")
        hold_findings = [f for f in analysis_review.findings if f.code == "CUSTOMER_ON_HOLD"]
        self.assertEqual(len(hold_findings), 1)
        self.assertEqual(hold_findings[0].severity, "warning")

        # 2. credit_hold_behaviour = "block" -> Error -> blocked
        ctx_block = RuleContext(
            catalog=self.catalog,
            customer_credit=credit,
            credit_hold_behaviour="block",
        )
        analysis_block = analyze_order(order, ctx_block)
        self.assertEqual(analysis_block.status, "blocked")
        hold_findings_block = [f for f in analysis_block.findings if f.code == "CUSTOMER_ON_HOLD"]
        self.assertEqual(len(hold_findings_block), 1)
        self.assertEqual(hold_findings_block[0].severity, "error")

    def test_all_findings_have_structured_evidence(self):
        order = Order(
            po_number="PO-EVID-01",
            customer="Unknown Cust",
            items=(
                LineItem(sku="NON-EXISTENT", quantity=1, unit_price=Decimal("100")),
                LineItem(sku="LAPTOP-A14", quantity=0, unit_price=Decimal("-10")),
            ),
        )
        analysis = analyze_order(order, self.catalog)
        self.assertGreater(len(analysis.findings), 0)
        for f in analysis.findings:
            self.assertIsInstance(f.evidence, dict, f"Finding {f.code} evidence is not a dict")
            self.assertGreaterEqual(len(f.evidence), 2, f"Finding {f.code} evidence has < 2 keys")
            self.assertIn("rule_version", f.evidence)


if __name__ == "__main__":
    unittest.main()
