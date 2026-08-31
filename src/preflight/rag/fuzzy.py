from __future__ import annotations

from rapidfuzz import fuzz

from preflight.models import Product
from preflight.rag.schemas import MatchCandidate, MatchResult, ResolutionTier


class FuzzyLexicalMatcher:
    """Tier 2: Lexical Fuzzy matching via RapidFuzz. Cost: 0 tokens, Latency: 2-5ms."""

    def __init__(self, catalog: dict[str, Product], threshold: float = 0.75):
        self.catalog = catalog
        self.threshold = threshold

    def match(self, raw_query: str) -> MatchResult | None:
        query = raw_query.strip().lower()
        if not query:
            return None

        candidates: list[MatchCandidate] = []

        for prod in self.catalog.values():
            sku_lower = prod.sku.lower()
            name_lower = prod.name.lower()

            # Compute multiple fuzzy scoring metrics
            # 1. Token Sort Ratio (handles word reordering: "Cable Cat6 3m" vs "Cat6 3m Cable")
            token_sort_score = fuzz.token_sort_ratio(query, name_lower) / 100.0
            sku_token_sort = fuzz.token_sort_ratio(query, sku_lower) / 100.0

            # 2. Weighted Ratio (handles typos & partial strings)
            w_ratio = fuzz.WRatio(query, name_lower) / 100.0
            sku_w_ratio = fuzz.WRatio(query, sku_lower) / 100.0

            # 3. Partial Ratio (query is substring of name)
            partial_score = fuzz.partial_ratio(query, name_lower) / 100.0

            # Max score across metrics
            best_score = max(token_sort_score, sku_token_sort, w_ratio, sku_w_ratio, partial_score * 0.9)

            if best_score >= self.threshold:
                candidates.append(
                    MatchCandidate(
                        sku=prod.sku,
                        name=prod.name,
                        unit_price=prod.unit_price,
                        stock=prod.stock,
                        active=prod.active,
                        score=round(best_score, 3),
                        tier=ResolutionTier.TIER_2_FUZZY,
                    )
                )

        if not candidates:
            return None

        # Sort descending by score
        candidates.sort(key=lambda c: c.score, reverse=True)
        top = candidates[0]

        is_confident = top.score >= 0.80
        explanation = (
            f"Fuzzy lexical match: '{raw_query}' matches catalog product '{top.name}' "
            f"({top.sku}) with {top.score * 100:.1f}% similarity."
        )

        return MatchResult(
            raw_query=raw_query,
            matched_sku=top.sku,
            name=top.name,
            unit_price=top.unit_price,
            stock=top.stock,
            active=top.active,
            confidence_score=top.score,
            tier_used=ResolutionTier.TIER_2_FUZZY,
            is_confident=is_confident,
            explanation=explanation,
            candidates=candidates[:3],
        )
