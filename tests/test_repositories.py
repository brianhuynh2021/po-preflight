import unittest
from decimal import Decimal
from sqlalchemy import create_engine
from preflight.db.models import metadata, organizations
from preflight.models import LineItem, Order, OrderAnalysis, OrderFinding
from preflight.repositories import (
    CustomerRepository,
    ProductRepository,
    OrderRepository,
    DecisionRepository,
    AuditRepository,
    OutboxRepository,
    LeadRepository,
)
from preflight.security.audit_chain import AuditBlock, calculate_hash


class TestRepositories(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", future=True)
        with self.engine.begin() as conn:
            metadata.create_all(conn)
            # Create default organization
            conn.execute(organizations.insert().values(id=1, code="org1", name="Công ty Test 1"))
            conn.execute(organizations.insert().values(id=2, code="org2", name="Công ty Test 2"))

    def tearDown(self):
        with self.engine.begin() as conn:
            metadata.drop_all(conn)

    def test_customer_and_product_repositories(self):
        with self.engine.begin() as conn:
            cust_repo = CustomerRepository(conn)
            c1 = cust_repo.get_or_create(org_id=1, name="Công ty ABC")
            c1_dup = cust_repo.get_or_create(org_id=1, name="công ty abc")
            self.assertEqual(c1["id"], c1_dup["id"])

            prod_repo = ProductRepository(conn)
            p1 = prod_repo.upsert_product(
                org_id=1,
                sku="SKU-001",
                name="Sản phẩm 1",
                unit_price=Decimal("150000"),
                stock=50,
            )
            self.assertEqual(p1["sku"], "SKU-001")
            self.assertEqual(len(prod_repo.list_all(org_id=1)), 1)

    def test_order_repository_and_sql_dashboard_stats(self):
        with self.engine.begin() as conn:
            order_repo = OrderRepository(conn)
            dec_repo = DecisionRepository(conn)

            # Order 1: Clean
            order1 = Order(
                po_number="PO-001",
                customer="Khách Hàng 1",
                items=(LineItem(sku="SKU-001", quantity=2, unit_price=Decimal("100000")),),
            )
            analysis1 = OrderAnalysis(order=order1, status="ready_for_approval", findings=[])
            id1 = order_repo.record_analysis(analysis1, source_file="po1.json", org_id=1)

            # Order 2: With findings
            order2 = Order(
                po_number="PO-002",
                customer="Khách Hàng 2",
                items=(LineItem(sku="SKU-999", quantity=10, unit_price=Decimal("50000")),),
            )
            findings2 = [
                OrderFinding(code="UNKNOWN_SKU", severity="error", message="Unknown SKU"),
                OrderFinding(code="INSUFFICIENT_STOCK", severity="warning", message="No stock"),
            ]
            analysis2 = OrderAnalysis(order=order2, status="review_required", findings=findings2)
            id2 = order_repo.record_analysis(analysis2, source_file="po2.json", org_id=1)

            # Record decision on order 1
            dec_repo.record_decision(id1, decision="approved", actor="admin", note="Approved by test")

            # Check stats via pure SQL aggregations
            stats = order_repo.get_dashboard_stats(org_id=1)
            self.assertEqual(stats["total_orders"], 2)
            self.assertEqual(stats["ready_for_approval"], 1)
            self.assertEqual(stats["review_required"], 1)
            self.assertEqual(stats["approved"], 1)
            self.assertEqual(stats["total_violations"], 2)
            self.assertEqual(stats["violation_breakdown"]["UNKNOWN_SKU"], 1)
            self.assertEqual(stats["violation_breakdown"]["INSUFFICIENT_STOCK"], 1)

    def test_same_po_number_across_different_customers(self):
        """Test that Customer A and Customer B with same PO number 'PO-SAME-01' are distinct records."""
        with self.engine.begin() as conn:
            order_repo = OrderRepository(conn)

            order_a = Order(
                po_number="PO-SAME-01",
                customer="Customer Alpha",
                items=(LineItem(sku="SKU-001", quantity=1, unit_price=Decimal("10000")),),
            )
            analysis_a = OrderAnalysis(order=order_a, status="ready_for_approval", findings=[])
            id_a = order_repo.record_analysis(analysis_a, org_id=1)

            order_b = Order(
                po_number="PO-SAME-01",
                customer="Customer Beta",
                items=(LineItem(sku="SKU-001", quantity=5, unit_price=Decimal("10000")),),
            )
            analysis_b = OrderAnalysis(order=order_b, status="ready_for_approval", findings=[])
            id_b = order_repo.record_analysis(analysis_b, org_id=1)

            self.assertNotEqual(id_a, id_b)
            ord_a = order_repo.get_by_id(id_a)
            ord_b = order_repo.get_by_id(id_b)
            self.assertEqual(ord_a["customer_name"], "Customer Alpha")
            self.assertEqual(ord_b["customer_name"], "Customer Beta")

    def test_audit_outbox_and_lead_repositories(self):
        with self.engine.begin() as conn:
            audit_repo = AuditRepository(conn)
            h = calculate_hash(
                index=1,
                timestamp=1000.0,
                po_number="PO-001",
                action="CREATE",
                actor="test_user",
                payload_hash="hash123",
                previous_hash="0" * 64,
            )
            block = AuditBlock(
                index=1,
                timestamp=1000.0,
                po_number="PO-001",
                action="CREATE",
                actor="test_user",
                payload_hash="hash123",
                previous_hash="0" * 64,
                block_hash=h,
            )
            b_id = audit_repo.append_block(block)
            self.assertGreater(b_id, 0)
            self.assertEqual(audit_repo.count_blocks(), 1)

            outbox_repo = OutboxRepository(conn)
            out_id = outbox_repo.enqueue("idem-001", {"order_id": 1, "amount": 1000})
            self.assertGreater(out_id, 0)
            pending = outbox_repo.fetch_pending(limit=5)
            self.assertEqual(len(pending), 1)
            outbox_repo.mark_processed(out_id, status="DELIVERED")
            self.assertEqual(len(outbox_repo.fetch_pending(limit=5)), 0)

            lead_repo = LeadRepository(conn)
            l_id = lead_repo.create_lead(
                company_name="Công ty Dược Hậu Giang",
                contact_person="Nguyễn Văn A",
                phone="0901234567",
                email="a@dhg.vn",
                daily_volume="100-500",
                current_erp="Fast",
            )
            self.assertGreater(l_id, 0)
            leads = lead_repo.list_leads()
            self.assertEqual(len(leads), 1)
            self.assertEqual(leads[0]["company_name"], "Công ty Dược Hậu Giang")


if __name__ == "__main__":
    unittest.main()
