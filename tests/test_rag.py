from __future__ import annotations

import unittest
from decimal import Decimal

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.models import Product
from preflight.rag.matcher import HybridSKUMatcher
from preflight.rag.schemas import ResolutionTier


class TestHybridSKUMatcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = {
            "LAPTOP-A14": Product(
                sku="LAPTOP-A14",
                name="A14 Business Laptop",
                unit_price=Decimal("18500000"),
                stock=25,
                active=True,
            ),
            "MONITOR-27": Product(
                sku="MONITOR-27",
                name="27-inch 4K Monitor",
                unit_price=Decimal("6200000"),
                stock=12,
                active=True,
            ),
            "DOCK-USBC": Product(
                sku="DOCK-USBC",
                name="USB-C Multiport Docking Station",
                unit_price=Decimal("2800000"),
                stock=8,
                active=True,
            ),
            "CAB-CAT6-3M": Product(
                sku="CAB-CAT6-3M",
                name="Cat6 Ethernet Patch Cable 3m",
                unit_price=Decimal("72000"),
                stock=150,
                active=True,
            ),
            "HEADSET-PRO": Product(
                sku="HEADSET-PRO",
                name="Wireless Noise Cancelling Headset",
                unit_price=Decimal("1450000"),
                stock=0,
                active=True,
            ),
        }
        cls.matcher = HybridSKUMatcher(cls.catalog)
        cls.client = TestClient(app)

    def test_tier1_exact_match(self):
        # Exact SKU
        res = self.matcher.resolve("LAPTOP-A14")
        self.assertEqual(res.tier_used, ResolutionTier.TIER_1_EXACT)
        self.assertEqual(res.matched_sku, "LAPTOP-A14")
        self.assertEqual(res.confidence_score, 1.0)
        self.assertTrue(res.is_confident)

        # Lowercase & stripped hyphens
        res_norm = self.matcher.resolve("laptop-a14")
        self.assertEqual(res_norm.matched_sku, "LAPTOP-A14")
        self.assertIn(res_norm.tier_used, [ResolutionTier.TIER_1_EXACT, ResolutionTier.TIER_2_FUZZY])

    def test_tier2_fuzzy_lexical(self):
        # Slight typo / word order difference
        res = self.matcher.resolve("A14 Laptop Business 14")
        self.assertEqual(res.matched_sku, "LAPTOP-A14")
        self.assertGreaterEqual(res.confidence_score, 0.75)
        self.assertTrue(res.is_confident)

        # Minor typo in name
        res_monitor = self.matcher.resolve("27-inch 4K Monitr")
        self.assertEqual(res_monitor.matched_sku, "MONITOR-27")
        self.assertGreaterEqual(res_monitor.confidence_score, 0.80)

    def test_tier3_semantic_vector_with_synonyms(self):
        # Vietnamese domain synonym: "dây mạng 3m" -> "CAB-CAT6-3M"
        res_cable = self.matcher.resolve("Dây mạng 3m bấm sẵn")
        self.assertEqual(res_cable.matched_sku, "CAB-CAT6-3M")
        self.assertGreaterEqual(res_cable.confidence_score, 0.50)

        # Vietnamese alias: "đế cắm usb-c" -> "DOCK-USBC"
        res_dock = self.matcher.resolve("Đế cắm cổng USB-C")
        self.assertEqual(res_dock.matched_sku, "DOCK-USBC")

    def test_tier4_llm_context_customer_history(self):
        # Customer Northstar using nickname "máy tính xách tay"
        res = self.matcher.resolve("máy tính xách tay", customer_id="Northstar Distribution")
        self.assertEqual(res.matched_sku, "LAPTOP-A14")
        self.assertEqual(res.tier_used, ResolutionTier.TIER_4_LLM_CONTEXT)
        self.assertIn("Customer 'Northstar Distribution' previously purchased", res.explanation)

    def test_batch_resolve(self):
        queries = ["LAPTOP-A14", "Dây mạng 3m", "27-inch Monitor"]
        results = self.matcher.batch_resolve(queries)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].matched_sku, "LAPTOP-A14")
        self.assertEqual(results[1].matched_sku, "CAB-CAT6-3M")
        self.assertEqual(results[2].matched_sku, "MONITOR-27")

    def test_api_sku_resolve_endpoint(self):
        payload = {"raw_text": "Cat6 Patch Cable 3m", "customer_id": "Northstar"}
        response = self.client.post("/api/v1/sku/resolve", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["matched_sku"], "CAB-CAT6-3M")
        self.assertIn("confidence_score", data)
        self.assertIn("tier_used", data)
        self.assertIn("explanation", data)


if __name__ == "__main__":
    unittest.main()
