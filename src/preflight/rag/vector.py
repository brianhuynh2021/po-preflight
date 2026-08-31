from __future__ import annotations

import math
import re
from collections import Counter

from preflight.models import Product
from preflight.rag.schemas import MatchCandidate, MatchResult, ResolutionTier

# Domain synonyms & Vietnamese alias expansions for B2B tech/office products
SYNONYM_MAP: dict[str, list[str]] = {
    "dây mạng": ["cáp", "mạng", "cable", "cat6", "ethernet", "lan", "patch"],
    "cáp mạng": ["cáp", "mạng", "cable", "cat6", "ethernet", "lan", "patch"],
    "dây cáp": ["cable", "cáp", "dây", "patch"],
    "máy tính": ["laptop", "vi", "tính", "notebook", "pc", "computer"],
    "màn hình": ["monitor", "display", "screen", "lcd", "4k"],
    "củ sạc": ["dock", "docking", "adapter", "charger", "nguồn", "typec", "usb"],
    "đế cắm": ["dock", "docking", "usbc", "hub", "station"],
    "tai nghe": ["headset", "earphone", "headphone", "audio", "wireless"],
    "bàn phím": ["keyboard", "phím", "cơ"],
    "chuột": ["mouse", "chuột", "quang", "wireless"],
}


def _tokenize(text: str) -> list[str]:
    # Lowercase, expand domain synonyms, extract word tokens
    words = re.findall(r"\w+", text.lower())
    expanded = list(words)
    full_text = " ".join(words)

    for phrase, syns in SYNONYM_MAP.items():
        if phrase in full_text:
            expanded.extend(syns)

    return expanded


def _cosine_similarity(vec1: Counter[str], vec2: Counter[str]) -> float:
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum(vec1[x] * vec2[x] for x in intersection)

    sum1 = sum(v**2 for v in vec1.values())
    sum2 = sum(v**2 for v in vec2.values())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    return float(numerator / denominator)


class VectorSemanticMatcher:
    """Tier 3: Semantic Vector & Synonym Matching. Cost: 0 tokens, Latency: 5-15ms."""

    def __init__(self, catalog: dict[str, Product], threshold: float = 0.35):
        self.catalog = catalog
        self.threshold = threshold
        self._doc_vectors: dict[str, Counter[str]] = {}

        # Pre-compute token vectors for catalog items
        for sku, prod in catalog.items():
            corpus_text = f"{prod.sku} {prod.name}"
            tokens = _tokenize(corpus_text)
            self._doc_vectors[sku] = Counter(tokens)

    def match(self, raw_query: str) -> MatchResult | None:
        query_tokens = _tokenize(raw_query)
        if not query_tokens:
            return None

        query_vec = Counter(query_tokens)
        candidates: list[MatchCandidate] = []

        for sku, doc_vec in self._doc_vectors.items():
            sim = _cosine_similarity(query_vec, doc_vec)
            if sim >= self.threshold:
                prod = self.catalog[sku]
                candidates.append(
                    MatchCandidate(
                        sku=prod.sku,
                        name=prod.name,
                        unit_price=prod.unit_price,
                        stock=prod.stock,
                        active=prod.active,
                        score=round(sim, 3),
                        tier=ResolutionTier.TIER_3_SEMANTIC_VECTOR,
                    )
                )

        if not candidates:
            return None

        candidates.sort(key=lambda c: c.score, reverse=True)
        top = candidates[0]

        is_confident = top.score >= 0.75
        explanation = (
            f"Semantic vector match: '{raw_query}' matches catalog product '{top.name}' "
            f"({top.sku}) via domain synonyms & token cosine similarity ({top.score * 100:.1f}%)."
        )

        return MatchResult(
            raw_query=raw_query,
            matched_sku=top.sku,
            name=top.name,
            unit_price=top.unit_price,
            stock=top.stock,
            active=top.active,
            confidence_score=top.score,
            tier_used=ResolutionTier.TIER_3_SEMANTIC_VECTOR,
            is_confident=is_confident,
            explanation=explanation,
            candidates=candidates[:3],
        )
