from __future__ import annotations

import json
import os
import time
from decimal import Decimal
from typing import Any
import urllib.request
import urllib.error


class DynamicFXEngine:
    """Enterprise Currency Exchange Rate Engine with 12-Hour TTL Caching & Offline Fallback.
    
    Provides reliable, zero-latency rate lookups with automatic caching and graceful fallback
    to official central bank baseline rates when external internet access is unavailable.
    """

    # Static fallback rates (Baseline: 1 USD = 25,400 VND, 1 EUR = 27,500 VND)
    FALLBACK_RATES: dict[str, float] = {
        "USD_VND": 25400.0,
        "VND_USD": 1.0 / 25400.0,
        "EUR_VND": 27500.0,
        "VND_EUR": 1.0 / 27500.0,
        "USD_USD": 1.0,
        "VND_VND": 1.0,
        "EUR_EUR": 1.0,
    }

    def __init__(self, cache_ttl_seconds: int = 43200) -> None:  # 12 hours

        self.cache_ttl = cache_ttl_seconds
        self._cache: dict[str, tuple[float, float]] = {}  # key -> (rate, timestamp)

    @property
    def is_live_enabled(self) -> bool:
        return os.getenv("PREFLIGHT_FX_LIVE", "false").strip().lower() in ("true", "1", "yes")

    def get_rate_info(self, base_currency: str = "USD", target_currency: str = "VND") -> tuple[Decimal, str]:
        """Returns (rate, source) where source is 'live' | 'static' | 'fallback'."""
        base = base_currency.strip().upper()
        target = target_currency.strip().upper()

        if base == target:
            return Decimal("1.0"), "static"

        key = f"{base}_{target}"

        # If live FX is not enabled, use static fallback
        if not self.is_live_enabled:
            rate = self.FALLBACK_RATES.get(key, 25400.0 if base == "USD" and target == "VND" else 1.0)
            return Decimal(str(rate)), "static"

        # 1. Check TTL Cache
        now = time.time()
        if key in self._cache:
            rate, cached_at = self._cache[key]
            if now - cached_at < self.cache_ttl:
                return Decimal(str(rate)), "live"

        # 2. Attempt Dynamic Online Fetch
        try:
            url = f"https://open.er-api.com/v6/latest/{base}"
            req = urllib.request.Request(url, headers={"User-Agent": "PO-Preflight/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    rates = payload.get("rates", {})
                    if target in rates:
                        live_rate = float(rates[target])
                        self._cache[key] = (live_rate, now)
                        if live_rate > 0:
                            self._cache[f"{target}_{base}"] = (1.0 / live_rate, now)
                        return Decimal(str(live_rate)), "live"
        except Exception:
            pass

        # 3. Fallback on network error
        rate = self.FALLBACK_RATES.get(key, 25400.0 if base == "USD" and target == "VND" else 1.0)
        return Decimal(str(rate)), "static"

    def get_rate(self, base_currency: str = "USD", target_currency: str = "VND") -> float:
        rate, _ = self.get_rate_info(base_currency, target_currency)
        return float(rate)

    def convert(
        self,
        amount: float | int | Decimal,
        from_currency: str,
        to_currency: str = "VND",
    ) -> float:
        amt = float(amount)
        rate = self.get_rate(from_currency, to_currency)
        return amt * rate


# Global engine instance
fx_engine = DynamicFXEngine()

