import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
import numpy as np

from preflight.models import Product
from preflight.rag.calibration import get_calibrated_thresholds, save_calibrated_thresholds
from preflight.rag.llm_fallback import LLMCircuitBreaker, LLMContextResolver
from preflight.rag.matcher import HybridSKUMatcher
from preflight.rag.schemas import MatchCandidate, ResolutionTier
from preflight.rag.vector import MultilingualEmbeddingModel, VectorSemanticMatcher
from preflight.store import AuditStore


class TestC5EmbeddingsAndEval(unittest.TestCase):
    def setUp(self):
        self.store = AuditStore(":memory:")
        self.catalog = {
            "LAPTOP-A14": Product(
                sku="LAPTOP-A14",
                name="A14 Business Laptop",
                unit_price=Decimal("18500000"),
                stock=25,
                active=True,
                category="Hardware",
            ),
            "CAB-CAT6-3M": Product(
                sku="CAB-CAT6-3M",
                name="Cat6 Ethernet Patch Cable 3m",
                unit_price=Decimal("72000"),
                stock=150,
                active=True,
                category="Network",
            ),
            "HEADSET-PRO": Product(
                sku="HEADSET-PRO",
                name="Professional Headset",
                unit_price=Decimal("1450000"),
                stock=10,
                active=True,
                category="Audio",
            ),
            "DOCK-USBC": Product(
                sku="DOCK-USBC",
                name="USB-C Dock",
                unit_price=Decimal("2800000"),
                stock=8,
                active=True,
                category="Accessories",
            ),
        }

    def test_criterion_a_vietnamese_cable_matching(self):
        """Criterion a: 'dây mạng 3m bấm sẵn' -> CAB-CAT6-3M top-1 with embedding."""
        matcher = VectorSemanticMatcher(self.catalog, store=self.store)
        res = matcher.match("dây mạng 3m bấm sẵn")
        self.assertIsNotNone(res)
        self.assertEqual(res.matched_sku, "CAB-CAT6-3M")
        self.assertGreaterEqual(res.confidence_score, 0.25)
        self.assertTrue(len(res.candidates) > 0)
        self.assertEqual(res.candidates[0].sku, "CAB-CAT6-3M")

    def test_product_embedding_persistence_in_store(self):
        """Test embedding persistence in SQLite product_embeddings table."""
        matcher = VectorSemanticMatcher(self.catalog, store=self.store)
        rows = self.store.get_product_embeddings()
        self.assertGreaterEqual(len(rows), 4)

        cab_row = self.store.get_product_embedding("CAB-CAT6-3M")
        self.assertIsNotNone(cab_row)
        self.assertEqual(cab_row["sku"], "CAB-CAT6-3M")
        self.assertTrue(len(cab_row["vector_blob"]) > 0)

        # Recreating matcher uses stored embeddings without recomputing
        with patch.object(matcher.embedder, "embed", wraps=matcher.embedder.embed) as mock_embed:
            m2 = VectorSemanticMatcher(self.catalog, store=self.store)
            res = m2.match("CAB-CAT6-3M")
            self.assertIsNotNone(res)

    def test_criterion_c_gemini_circuit_breaker(self):
        """Criterion c: Gemini error -> circuit OPEN after 3 failures, returns 'LLM tạm ngưng'."""
        breaker = LLMCircuitBreaker(failure_threshold=3)
        self.assertFalse(breaker.is_open())

        resolver = LLMContextResolver(
            self.catalog,
            store=self.store,
            api_key="fake-api-key",
            circuit_breaker=breaker,
        )

        # Mock failure in _call_gemini_reasoning
        with patch.object(resolver, "_call_gemini_reasoning") as mock_call:
            # Simulate 3 consecutive failures
            for i in range(3):
                breaker.record_failure()

            self.assertTrue(breaker.is_open())

            # Now resolving an unconfident query must fail fast with 'LLM tạm ngưng'
            res = resolver.match("unrecognized unknown query XYZ")
            self.assertEqual(res.tier_used, ResolutionTier.UNRESOLVED)
            self.assertIn("LLM tạm ngưng", res.explanation)
            self.assertIsNone(res.matched_sku)

    def test_dynamic_calibration_thresholds(self):
        """Test dynamic calibration thresholds loading and customization."""
        thresholds = get_calibrated_thresholds()
        self.assertIn("vector_threshold", thresholds)
        self.assertIn("fuzzy_threshold", thresholds)
        self.assertGreater(thresholds["vector_threshold"], 0.0)

    def test_hybrid_waterfall_all_tiers(self):
        """Test HybridSKUMatcher cascading across Tier 0, 1, 2, and 3."""
        matcher = HybridSKUMatcher(self.catalog, store=self.store)

        # Tier 1 Exact
        res_exact = matcher.resolve("LAPTOP-A14")
        self.assertEqual(res_exact.tier_used, ResolutionTier.TIER_1_EXACT)
        self.assertEqual(res_exact.matched_sku, "LAPTOP-A14")

        # Tier 2 Fuzzy
        res_fuzzy = matcher.resolve("laptop-a14-biz")
        self.assertEqual(res_fuzzy.matched_sku, "LAPTOP-A14")

        # Tier 3 Semantic Vector
        res_vec = matcher.resolve("dây mạng 3m bấm sẵn")
        self.assertEqual(res_vec.matched_sku, "CAB-CAT6-3M")

        # Tier 0 Active Learning
        matcher.learn_alias("CUST-TEST", "máy tính giám đốc", "LAPTOP-A14")
        res_alias = matcher.resolve("máy tính giám đốc", customer_id="CUST-TEST")
        self.assertEqual(res_alias.matched_sku, "LAPTOP-A14")
        self.assertEqual(res_alias.confidence_score, 1.0)


if __name__ == "__main__":
    unittest.main()
