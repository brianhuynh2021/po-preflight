from __future__ import annotations

import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from preflight.models import Product
from preflight.rag.llm_fallback import LLMContextResolver
from preflight.rag.schemas import ResolutionTier


class TestGeminiRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = {
            "LAPTOP-A14": Product(sku="LAPTOP-A14", name="A14 Business Laptop", unit_price=Decimal("18500000"), stock=50),
            "MONITOR-27": Product(sku="MONITOR-27", name="27-inch 4K Monitor", unit_price=Decimal("8900000"), stock=20),
            "CAB-CAT6-3M": Product(sku="CAB-CAT6-3M", name="Cat6 Ethernet Patch Cable 3m", unit_price=Decimal("72000"), stock=500),
        }

    def test_customer_historical_context_resolution(self):
        """Test customer memory matching prior purchase nicknames."""
        resolver = LLMContextResolver(self.catalog)
        res = resolver.match("máy tính xách tay", customer_id="Northstar Distribution")
        self.assertEqual(res.matched_sku, "LAPTOP-A14")
        self.assertEqual(res.tier_used, ResolutionTier.TIER_4_LLM_CONTEXT)
        self.assertTrue(res.is_confident)

    def test_unresolved_zero_hallucination(self):
        """Test unresolvable query returns ResolutionTier.UNRESOLVED with 0 confidence."""
        resolver = LLMContextResolver(self.catalog)
        res = resolver.match("sản phẩm hoàn toàn không tồn tại 999", customer_id="UnknownCustomer")
        self.assertIsNone(res.matched_sku)
        self.assertEqual(res.confidence_score, 0.0)
        self.assertEqual(res.tier_used, ResolutionTier.UNRESOLVED)
        self.assertFalse(res.is_confident)

    @patch.object(LLMContextResolver, "_call_gemini_reasoning")
    def test_gemini_fallback_valid_catalog_match(self, mock_gemini):
        """Test Gemini 2.0 Flash structured reasoning successfully matching catalog product."""
        mock_gemini.return_value = ("MONITOR-27", "Matched 4k screen query to 27-inch 4K Monitor based on specs.")
        resolver = LLMContextResolver(self.catalog, api_key="mock_gemini_key")
        res = resolver.match("màn hình 4k siêu nét cho thiết kế đồ họa", customer_id="NewClient")
        self.assertEqual(res.matched_sku, "MONITOR-27")
        self.assertEqual(res.tier_used, ResolutionTier.TIER_4_LLM_CONTEXT)
        self.assertIn("Gemini 2.0 Flash", res.explanation)

    @patch.object(LLMContextResolver, "_call_gemini_reasoning")
    def test_gemini_hallucination_rejected_by_zero_hallucination_guard(self, mock_gemini):
        """Test Gemini proposing a non-existent hallucinated SKU is strictly rejected."""
        mock_gemini.return_value = ("NON_EXISTENT_SKU_999", "Hallucinated SKU suggestion.")
        resolver = LLMContextResolver(self.catalog, api_key="mock_gemini_key")
        res = resolver.match("màn hình siêu mỏng", customer_id="NewClient")
        self.assertIsNone(res.matched_sku)
        self.assertEqual(res.confidence_score, 0.0)
        self.assertEqual(res.tier_used, ResolutionTier.UNRESOLVED)


if __name__ == "__main__":
    unittest.main()
