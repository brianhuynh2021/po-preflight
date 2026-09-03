from typing import Any
from preflight.models import Product

from preflight.rag.calibration import get_calibrated_thresholds
from preflight.rag.exact import ExactMatcher
from preflight.rag.fuzzy import FuzzyLexicalMatcher
from preflight.rag.llm_fallback import LLMContextResolver
from preflight.rag.schemas import MatchCandidate, MatchResult
from preflight.rag.vector import VectorSemanticMatcher
from preflight.observability.tracing import trace_span
from preflight.observability.metrics import metrics_registry


class HybridSKUMatcher:
    """Enterprise 4-Tier Waterfall SKU Resolution Engine.
    
    Tier 0 (Active Learning Alias Store): < 0.5ms, 0 tokens
    Tier 1 (Exact Hash): < 1ms, 0 tokens
    Tier 2 (Fuzzy Lexical): < 5ms, 0 tokens
    Tier 3 (Local Multilingual Semantic Vector): < 15ms, 0 tokens
    Tier 4 (Constrained LLM Context Reasoner): Fallback when confidence < threshold
    """

    def __init__(self, catalog: dict[str, Product], store: Any | None = None):
        self.catalog = catalog
        self.store = store
        self._in_memory_aliases: dict[tuple[str, str], str] = {}
        calibrated = get_calibrated_thresholds()
        self.tier1_exact = ExactMatcher(catalog)
        self.tier2_fuzzy = FuzzyLexicalMatcher(catalog, threshold=calibrated["fuzzy_threshold"])
        self.tier3_vector = VectorSemanticMatcher(catalog, store=store, threshold=calibrated["vector_threshold"])
        self.tier4_llm = LLMContextResolver(catalog, store=store)

    def learn_alias(self, customer_id: str, raw_query: str, target_sku: str) -> None:
        """Learn and persist a customer-specific nickname/alias mapping."""
        key = (customer_id.strip().lower(), raw_query.strip().lower())
        self._in_memory_aliases[key] = target_sku.strip().upper()
        if self.store and hasattr(self.store, "learn_alias"):
            self.store.learn_alias(customer_id, raw_query, target_sku)

    def resolve(self, raw_query: str, customer_id: str | None = None) -> MatchResult:
        with trace_span("sku_resolution", {"raw_query": raw_query, "customer_id": str(customer_id)}):
            res = self._do_resolve(raw_query, customer_id)
            try:
                tier_val = str(res.tier_used.value if hasattr(res.tier_used, "value") else res.tier_used)
                metrics_registry.record_sku_resolution(tier_val)
            except Exception:
                pass
            return res

    def _do_resolve(self, raw_query: str, customer_id: str | None = None) -> MatchResult:
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
        fuzzy_res = self.tier2_fuzzy.match(clean_query)
        if fuzzy_res is not None and fuzzy_res.confidence_score >= 0.85:
            return fuzzy_res

        # Gather candidates across tiers
        all_candidates: list[MatchCandidate] = []
        if fuzzy_res and fuzzy_res.candidates:
            all_candidates.extend(fuzzy_res.candidates)

        # -------------------------------------------------------------
        # TIER 3: Local Multilingual Semantic Vector Match (<15ms, 0 tokens)
        # -------------------------------------------------------------
        vector_res = self.tier3_vector.match(clean_query)
        if vector_res and vector_res.candidates:
            all_candidates = vector_res.candidates + all_candidates

        # Deduplicate candidates
        seen_skus = set()
        deduped_candidates: list[MatchCandidate] = []
        for c in all_candidates:
            if c.sku not in seen_skus:
                seen_skus.add(c.sku)
                deduped_candidates.append(c)

        # Tier 3: Confident if score >= threshold AND margin between top-1 and top-2 >= 0.05
        has_margin = True
        if vector_res and len(vector_res.candidates) > 1:
            margin = vector_res.candidates[0].score - vector_res.candidates[1].score
            has_margin = margin >= 0.05

        if vector_res is not None and vector_res.confidence_score >= 0.50 and has_margin:
            vector_res.candidates = deduped_candidates[:5]
            return vector_res

        if fuzzy_res is not None and fuzzy_res.confidence_score >= 0.70:
            fuzzy_res.candidates = deduped_candidates[:5]
            return fuzzy_res

        # -------------------------------------------------------------
        # TIER 4: LLM Context Reasoner (Constrained to top 20 candidates)
        # -------------------------------------------------------------
        return self.tier4_llm.match(clean_query, customer_id=customer_id, candidates=deduped_candidates[:20])

    def batch_resolve(self, queries: list[str], customer_id: str | None = None) -> list[MatchResult]:
        return [self.resolve(q, customer_id=customer_id) for q in queries]
