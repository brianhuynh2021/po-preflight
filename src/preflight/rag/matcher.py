from typing import Any
from preflight.models import Product

from preflight.rag.exact import ExactMatcher
from preflight.rag.fuzzy import FuzzyLexicalMatcher
from preflight.rag.llm_fallback import LLMContextResolver
from preflight.rag.schemas import MatchResult
from preflight.rag.vector import VectorSemanticMatcher


class HybridSKUMatcher:
    """Enterprise 4-Tier Waterfall SKU Resolution Engine.
    
    Tier 0 (Active Learning Alias Store): < 0.5ms, 0 tokens
    Tier 1 (Exact Hash): < 1ms, 0 tokens
    Tier 2 (Fuzzy Lexical): < 5ms, 0 tokens
    Tier 3 (Semantic Vector): < 15ms, 0 tokens
    Tier 4 (LLM Context Reasoner): Fallback when confidence < 70%
    """

    def __init__(self, catalog: dict[str, Product], store: Any | None = None):
        self.catalog = catalog
        self.store = store
        self._in_memory_aliases: dict[tuple[str, str], str] = {}
        self.tier1_exact = ExactMatcher(catalog)
        self.tier2_fuzzy = FuzzyLexicalMatcher(catalog, threshold=0.75)
        self.tier3_vector = VectorSemanticMatcher(catalog, threshold=0.35)
        self.tier4_llm = LLMContextResolver(catalog, store=store)

    def learn_alias(self, customer_id: str, raw_query: str, target_sku: str) -> None:
        """Learn and persist a customer-specific nickname/alias mapping."""
        key = (customer_id.strip().lower(), raw_query.strip().lower())
        self._in_memory_aliases[key] = target_sku.strip().upper()
        if self.store and hasattr(self.store, "learn_alias"):
            self.store.learn_alias(customer_id, raw_query, target_sku)

    def resolve(self, raw_query: str, customer_id: str | None = None) -> MatchResult:
        if not raw_query or not raw_query.strip():
            return self.tier4_llm.match("", customer_id=customer_id)

        clean_query = raw_query.strip()

        # -------------------------------------------------------------
        # TIER 0: Customer-Specific Active Learning Alias Memory
        # -------------------------------------------------------------
        if customer_id:
            c_key = (customer_id.strip().lower(), clean_query.lower())
            learned_sku = self._in_memory_aliases.get(c_key)
            if not learned_sku and self.store and hasattr(self.store, "get_customer_alias"):
                learned_sku = self.store.get_customer_alias(customer_id, clean_query)
            if learned_sku and learned_sku in self.catalog:
                product = self.catalog[learned_sku]
                from preflight.rag.schemas import MatchCandidate, ResolutionTier
                return MatchResult(
                    raw_query=clean_query,
                    matched_sku=product.sku,
                    name=product.name,
                    unit_price=product.unit_price,
                    stock=product.stock,
                    active=product.active,
                    confidence_score=1.0,
                    tier_used=ResolutionTier.TIER_1_EXACT,
                    is_confident=True,
                    explanation=f"Matched via Customer Active Learning Alias Store for customer '{customer_id}'",
                    candidates=[
                        MatchCandidate(
                            sku=product.sku,
                            name=product.name,
                            unit_price=product.unit_price,
                            stock=product.stock,
                            active=product.active,
                            score=1.0,
                            tier=ResolutionTier.TIER_1_EXACT,
                        )
                    ],
                )

        # -------------------------------------------------------------
        # TIER 1: Exact Match (0 tokens, <1ms)
        # -------------------------------------------------------------
        exact_res = self.tier1_exact.match(clean_query)
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
