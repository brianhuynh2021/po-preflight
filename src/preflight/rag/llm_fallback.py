from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from typing import Any

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
    "VINGROUP": {
        "máy trạm kỹ thuật": "LAPTOP-A14",
        "tai nghe chống ồn": "HEADSET-PRO",
        "cáp mạng nội bộ": "CAB-CAT6-3M",
    },
}


class LLMContextResolver:
    """Tier 4: Context-Aware Reasoning over Customer History & Gemini 2.0 Flash Fallback."""

    def __init__(self, catalog: dict[str, Product], api_key: str | None = None, model: str = "gemini-2.0-flash"):
        self.catalog = catalog
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model

    def _call_gemini_reasoning(self, raw_query: str, customer_id: str | None = None) -> tuple[str | None, str | None]:
        """Call Gemini 2.0 Flash structured reasoning API with catalog constraints."""
        if not self.api_key:
            return None, None

        catalog_summary = [
            {"sku": p.sku, "name": p.name, "unit_price": str(p.unit_price)}
            for p in self.catalog.values()
            if p.active
        ]

        system_instruction = (
            "You are a strict procurement product matcher for PO Preflight. "
            "Match the buyer's query to exactly ONE SKU from the catalog. "
            "If no confident match exists, return null for matched_sku. "
            "Respond ONLY with valid JSON: {\"matched_sku\": string|null, \"reasoning\": string}"
        )

        prompt = f"Customer: {customer_id or 'General'}\nQuery: {raw_query}\nCatalog:\n{json.dumps(catalog_summary, ensure_ascii=False)}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\n{prompt}"}]}],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1},
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                result_json = json.loads(resp.read().decode("utf-8"))
                text_out = result_json["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text_out)
                return parsed.get("matched_sku"), parsed.get("reasoning")
        except Exception:
            return None, None

    def match(self, raw_query: str, customer_id: str | None = None) -> MatchResult:
        query_lower = raw_query.strip().lower()

        # 1. Check customer-specific purchase history memory first
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

        # 2. If historical memory did not match, try Gemini 2.0 Flash reasoning
        if not matched_sku and self.api_key:
            gemini_sku, reasoning = self._call_gemini_reasoning(raw_query, customer_id)
            if gemini_sku and gemini_sku in self.catalog:
                matched_sku = gemini_sku
                historical_rationale = f"Gemini 2.0 Flash structured reasoning: {reasoning}"

        # 3. Validate against catalog (Zero-hallucination guarantee)
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
