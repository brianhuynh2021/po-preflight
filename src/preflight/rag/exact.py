from __future__ import annotations

import re
from preflight.models import Product
from preflight.rag.schemas import MatchCandidate, MatchResult, ResolutionTier


class ExactMatcher:
    """Tier 1: O(1) Exact Hash / Direct lookup. Cost: 0 tokens, Latency: < 1ms."""

    def __init__(self, catalog: dict[str, Product]):
        self.catalog = catalog
        # Build normalized index: strip hyphens, spaces, uppercase
        self._normalized_index: dict[str, Product] = {}
        for sku, prod in catalog.items():
            norm_key = self._normalize_key(sku)
            self._normalized_index[norm_key] = prod

    @staticmethod
    def _normalize_key(text: str) -> str:
        return re.sub(r"[^A-Za-z0-9]", "", text).upper()

    def match(self, raw_query: str) -> MatchResult | None:
        cleaned = raw_query.strip().upper()

        # 1. Exact key match
        if cleaned in self.catalog:
            prod = self.catalog[cleaned]
            return MatchResult(
                raw_query=raw_query,
                matched_sku=prod.sku,
                name=prod.name,
                unit_price=prod.unit_price,
                stock=prod.stock,
                active=prod.active,
                confidence_score=1.0,
                tier_used=ResolutionTier.TIER_1_EXACT,
                is_confident=True,
                explanation=f"Exact match found in catalog for SKU '{prod.sku}'.",
                candidates=[
                    MatchCandidate(
                        sku=prod.sku,
                        name=prod.name,
                        unit_price=prod.unit_price,
                        stock=prod.stock,
                        active=prod.active,
                        score=1.0,
                        tier=ResolutionTier.TIER_1_EXACT,
                    )
                ],
            )

        # 2. Normalized key match (e.g. LAPTOPA14 -> LAPTOP-A14)
        norm_query = self._normalize_key(raw_query)
        if norm_query and norm_query in self._normalized_index:
            prod = self._normalized_index[norm_query]
            return MatchResult(
                raw_query=raw_query,
                matched_sku=prod.sku,
                name=prod.name,
                unit_price=prod.unit_price,
                stock=prod.stock,
                active=prod.active,
                confidence_score=0.99,
                tier_used=ResolutionTier.TIER_1_EXACT,
                is_confident=True,
                explanation=f"Exact normalized match for SKU '{prod.sku}'.",
                candidates=[
                    MatchCandidate(
                        sku=prod.sku,
                        name=prod.name,
                        unit_price=prod.unit_price,
                        stock=prod.stock,
                        active=prod.active,
                        score=0.99,
                        tier=ResolutionTier.TIER_1_EXACT,
                    )
                ],
            )

        return None
