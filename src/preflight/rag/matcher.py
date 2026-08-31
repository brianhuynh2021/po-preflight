from __future__ import annotations

from preflight.models import Product
from preflight.rag.exact import ExactMatcher
from preflight.rag.fuzzy import FuzzyLexicalMatcher
from preflight.rag.llm_fallback import LLMContextResolver
from preflight.rag.schemas import MatchResult
from preflight.rag.vector import VectorSemanticMatcher


class HybridSKUMatcher:
    """Enterprise 4-Tier Waterfall SKU Resolution Engine.
    
    Tier 1 (Exact Hash): < 1ms, 0 tokens
    Tier 2 (Fuzzy Lexical): < 5ms, 0 tokens
    Tier 3 (Semantic Vector): < 15ms, 0 tokens
    Tier 4 (LLM Context Reasoner): Fallback when confidence < 70%
    """

    def __init__(self, catalog: dict[str, Product]):
        self.catalog = catalog
        self.tier1_exact = ExactMatcher(catalog)
        self.tier2_fuzzy = FuzzyLexicalMatcher(catalog, threshold=0.75)
        self.tier3_vector = VectorSemanticMatcher(catalog, threshold=0.35)
        self.tier4_llm = LLMContextResolver(catalog)

    def resolve(self, raw_query: str, customer_id: str | None = None) -> MatchResult:
        if not raw_query or not raw_query.strip():
            return self.tier4_llm.match("", customer_id=customer_id)

        # -------------------------------------------------------------
        # TIER 1: Exact Match (0 tokens, <1ms)
        # -------------------------------------------------------------
        exact_res = self.tier1_exact.match(raw_query)
        if exact_res is not None:
            return exact_res

        # -------------------------------------------------------------
        # TIER 2: Fuzzy Lexical Match via RapidFuzz (0 tokens, <5ms)
        # -------------------------------------------------------------
        fuzzy_res = self.tier2_fuzzy.match(raw_query)
        if fuzzy_res is not None and fuzzy_res.confidence_score >= 0.80:
            return fuzzy_res

        # -------------------------------------------------------------
        # TIER 3: Semantic Vector Match (0 LLM tokens, <15ms)
        # -------------------------------------------------------------
        vector_res = self.tier3_vector.match(raw_query)
        if vector_res is not None and vector_res.confidence_score >= 0.35:
            # If fuzzy also had a candidate, merge them into alternative candidates
            if fuzzy_res and fuzzy_res.candidates:
                merged = vector_res.candidates + fuzzy_res.candidates
                # Deduplicate by SKU
                seen = set()
                deduped = []
                for c in merged:
                    if c.sku not in seen:
                        seen.add(c.sku)
                        deduped.append(c)
                vector_res.candidates = deduped[:3]
            return vector_res

        # If fuzzy had a partial match (e.g. 0.75-0.79) but vector didn't beat it, return fuzzy
        if fuzzy_res is not None:
            return fuzzy_res

        # -------------------------------------------------------------
        # TIER 4: LLM Context Reasoner (Cross-reference customer history)
        # -------------------------------------------------------------
        return self.tier4_llm.match(raw_query, customer_id=customer_id)

    def batch_resolve(self, queries: list[str], customer_id: str | None = None) -> list[MatchResult]:
        return [self.resolve(q, customer_id=customer_id) for q in queries]
