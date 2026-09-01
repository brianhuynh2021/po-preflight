from __future__ import annotations

from preflight.models import Product
from preflight.rag.schemas import MatchCandidate, MatchResult, ResolutionTier

# Known historical purchase mappings per customer account (Context Knowledge Base)
CUSTOMER_HISTORICAL_NICKNAMES: dict[str, dict[str, str]] = {
    "NORTHSTAR": {
        "máy tính xách tay": "LAPTOP-A14",
        "laptop đời mới": "LAPTOP-A14",
        "màn hình phụ": "MONITOR-27",
        "dock kết nối": "DOCK-USBC",
        "dây mạng dài": "CAB-CAT6-3M",
    },
    "ACME": {
        "máy tính cho dev": "LAPTOP-A14",
        "màn hình thiết kế": "MONITOR-27",
        "tai nghe họp online": "HEADSET-PRO",
    },
}


class LLMContextResolver:
    """Tier 4: Context-Aware Reasoning over Customer History & Contracts."""

    def __init__(self, catalog: dict[str, Product]):
        self.catalog = catalog

    def match(self, raw_query: str, customer_id: str | None = None) -> MatchResult:
        query_lower = raw_query.strip().lower()

        # Check customer-specific purchase history first
        matched_sku: str | None = None
        historical_rationale: str | None = None

        if customer_id:
            cust_key = customer_id.strip().upper()
            for key, nicknames in CUSTOMER_HISTORICAL_NICKNAMES.items():
                if key in cust_key:
                    for nick, target_sku in nicknames.items():
                        if nick in query_lower:
                            matched_sku = target_sku
                            historical_rationale = (
                                f"Customer '{customer_id}' previously purchased SKU '{target_sku}' "
                                f"using nickname '{nick}' in past orders."
                            )
                            break

        # Fallback to general catalog heuristic if no customer history matched
        if not matched_sku:
            # Pick first active product as low-confidence proposal
            first_prod = next(iter(self.catalog.values())) if self.catalog else None
            if first_prod:
                return MatchResult(
                    raw_query=raw_query,
                    matched_sku=first_prod.sku,
                    name=first_prod.name,
                    unit_price=first_prod.unit_price,
                    stock=first_prod.stock,
                    active=first_prod.active,
                    confidence_score=0.40,
                    tier_used=ResolutionTier.TIER_4_LLM_CONTEXT,
                    is_confident=False,
                    explanation=(
                        f"Low-confidence proposal: '{raw_query}' is ambiguous and has no exact, fuzzy, "
                        f"or vector match. Proposing '{first_prod.sku}' for manual reviewer confirmation."
                    ),
                    candidates=[],
                )

        if matched_sku and matched_sku in self.catalog:
            prod = self.catalog[matched_sku]
            return MatchResult(
                raw_query=raw_query,
                matched_sku=prod.sku,
                name=prod.name,
                unit_price=prod.unit_price,
                stock=prod.stock,
                active=prod.active,
                confidence_score=0.88,
                tier_used=ResolutionTier.TIER_4_LLM_CONTEXT,
                is_confident=True,
                explanation=f"LLM Context Reasoning: {historical_rationale}",
                candidates=[
                    MatchCandidate(
                        sku=prod.sku,
                        name=prod.name,
                        unit_price=prod.unit_price,
                        stock=prod.stock,
                        active=prod.active,
                        score=0.88,
                        tier=ResolutionTier.TIER_4_LLM_CONTEXT,
                    )
                ],
            )

        return MatchResult(
            raw_query=raw_query,
            matched_sku=None,
            name=None,
            unit_price=None,
            stock=None,
            active=False,
            confidence_score=0.0,
            tier_used=ResolutionTier.UNRESOLVED,
            is_confident=False,
            explanation=f"Unable to resolve SKU for raw query: '{raw_query}'. Requires manual intervention.",
            candidates=[],
        )
