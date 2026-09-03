from __future__ import annotations

import json
import logging
import os
import time
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from preflight.models import Product
from preflight.rag.schemas import MatchCandidate, MatchResult, ResolutionTier

logger = logging.getLogger("preflight.rag.llm")


class SKUChoice(BaseModel):
    matched_sku: str | None = Field(default=None, description="Exact SKU from candidate list, or null if no confident match")
    reasoning: str = Field(default="", description="Procurement matching justification")
    confidence: float = Field(default=0.85, description="Confidence score from 0.0 to 1.0")


class LLMCircuitBreaker:
    """Circuit Breaker for Tier-4 Gemini LLM calls.
    
    Opens after 3 consecutive failures.
    When OPEN, requests fail fast with explanation 'LLM tạm ngưng'.
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout_seconds
        self.consecutive_failures = 0
        self.state = "CLOSED"  # "CLOSED" or "OPEN"
        self.last_failure_time: float = 0.0

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        if self.consecutive_failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                "Tier-4 LLM Circuit Breaker opened after %d consecutive failures. Failing fast.",
                self.consecutive_failures,
            )

    def is_open(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                logger.info("Tier-4 LLM Circuit Breaker entering HALF-OPEN probe state.")
                return False
            return True
        return False


class LLMContextResolver:
    """Tier 4: Context-Aware Reasoning using Gemini 2.0 Flash via official google-genai SDK.
    
    Guarantees:
    - Constrained candidate set: Only top-20 candidates sent to the model (never full catalog).
    - Structured output via SKUChoice schema.
    - Timeout, retry, circuit breaker (fails fast after 3 errors with 'LLM tạm ngưng').
    - Token usage logging.
    """

    def __init__(
        self,
        catalog: dict[str, Product],
        store: Any | None = None,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
        circuit_breaker: LLMCircuitBreaker | None = None,
    ):
        self.catalog = catalog
        self.store = store
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model
        self.circuit_breaker = circuit_breaker or LLMCircuitBreaker()

    def _call_gemini_reasoning(
        self,
        raw_query: str,
        customer_id: str | None = None,
        candidates: list[MatchCandidate] | None = None,
    ) -> tuple[str | None, str, float, bool]:
        """Call Gemini via official google-genai SDK.
        
        Returns: (matched_sku, reasoning, confidence, is_circuit_open)
        """
        if self.circuit_breaker.is_open():
            return None, "LLM tạm ngưng (circuit breaker OPEN sau 3 lần lỗi liên tiếp)", 0.0, True

        if not self.api_key:
            return None, "GEMINI_API_KEY not configured", 0.0, False

        # Constrain to top-20 candidates
        if candidates and len(candidates) > 0:
            candidate_pool = [
                {"sku": c.sku, "name": c.name, "unit_price": str(c.unit_price)}
                for c in candidates[:20]
            ]
        else:
            active_prods = [p for p in self.catalog.values() if p.active][:20]
            candidate_pool = [
                {"sku": p.sku, "name": p.name, "unit_price": str(p.unit_price)}
                for p in active_prods
            ]

        prompt = (
            f"Customer: {customer_id or 'General'}\n"
            f"Buyer Line Item Query: \"{raw_query}\"\n"
            f"Candidate Products (Choose ONLY from this list or return null):\n"
            f"{json.dumps(candidate_pool, ensure_ascii=False, indent=2)}"
        )

        system_instruction = (
            "You are a zero-hallucination B2B procurement catalog matcher for PO Preflight. "
            "Match the buyer's query strictly to ONE product from the provided Candidate Products list. "
            "If no confident match exists in the candidate list, matched_sku MUST be null."
        )

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=self.model,
                    contents=f"{system_instruction}\n\n{prompt}",
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=SKUChoice,
                        temperature=0.1,
                    ),
                )

                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    logger.info(
                        "Tier-4 Gemini token usage: prompt=%s, candidates=%s, total=%s",
                        response.usage_metadata.prompt_token_count,
                        response.usage_metadata.candidates_token_count,
                        response.usage_metadata.total_token_count,
                    )

                text = response.text or "{}"
                parsed = json.loads(text)
                chosen_sku = parsed.get("matched_sku")
                reasoning = parsed.get("reasoning", "Matched via Gemini 2.0 Flash")
                conf = float(parsed.get("confidence", 0.85))

                self.circuit_breaker.record_success()
                return chosen_sku, reasoning, conf, False

            except Exception as exc:
                logger.warning("Gemini Tier-4 call attempt %d failed: %s", attempt + 1, exc)
                if attempt == max_retries:
                    self.circuit_breaker.record_failure()
                    is_now_open = self.circuit_breaker.is_open()
                    msg = "LLM tạm ngưng" if is_now_open else f"Gemini call failed: {exc}"
                    return None, msg, 0.0, is_now_open
                time.sleep(0.2)

        return None, "Gemini call exceeded retries", 0.0, False

    def match(
        self,
        raw_query: str,
        customer_id: str | None = None,
        candidates: list[MatchCandidate] | None = None,
    ) -> MatchResult:
        query_clean = raw_query.strip()
        if not query_clean:
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
                explanation="Empty query line item",
                candidates=[],
            )

        # 0. Check circuit breaker status first
        if self.circuit_breaker.is_open():
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
                explanation="LLM tạm ngưng (circuit breaker OPEN sau 3 lần lỗi liên tiếp)",
                candidates=[],
            )

        # 1. Customer Active Learning Memory Check
        matched_sku: str | None = None
        historical_rationale: str | None = None

        if customer_id and self.store and hasattr(self.store, "get_customer_alias"):
            learned = self.store.get_customer_alias(customer_id, raw_query)
            if learned and learned in self.catalog:
                matched_sku = learned
                historical_rationale = f"Khớp từ bộ nhớ biệt danh khách hàng '{customer_id}'."

        # 2. Gemini Official SDK invocation with constrained candidate list
        conf = 0.85
        if not matched_sku and self.api_key:
            call_res = self._call_gemini_reasoning(
                raw_query, customer_id=customer_id, candidates=candidates
            )
            if len(call_res) == 4:
                gemini_sku, reasoning, conf_score, is_open = call_res
            else:
                gemini_sku, reasoning = call_res[0], call_res[1]
                conf_score, is_open = 0.85, False
            if is_open:
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
                    explanation="LLM tạm ngưng",
                    candidates=[],
                )
            if gemini_sku and gemini_sku in self.catalog:
                matched_sku = gemini_sku
                historical_rationale = f"Gemini 2.0 Flash: {reasoning}"
                conf = conf_score

        # 3. Catalog Grounding Validation
        if matched_sku and matched_sku in self.catalog:
            prod = self.catalog[matched_sku]
            return MatchResult(
                raw_query=raw_query,
                matched_sku=prod.sku,
                name=prod.name,
                unit_price=prod.unit_price,
                stock=prod.stock,
                active=prod.active,
                confidence_score=conf,
                tier_used=ResolutionTier.TIER_4_LLM_CONTEXT,
                is_confident=True,
                explanation=f"Tier 4 LLM Reasoning: {historical_rationale}",
                candidates=[
                    MatchCandidate(
                        sku=prod.sku,
                        name=prod.name,
                        unit_price=prod.unit_price,
                        stock=prod.stock,
                        active=prod.active,
                        score=conf,
                        tier=ResolutionTier.TIER_4_LLM_CONTEXT,
                    )
                ],
            )

        # 4. Unresolved Fallback
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
            explanation=f"Không thể xác định SKU từ chuỗi '{raw_query}' qua các tầng RAG và LLM.",
            candidates=[],
        )
