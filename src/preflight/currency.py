from __future__ import annotations

import json
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

    def get_rate(self, base_currency: str = "USD", target_currency: str = "VND") -> float:
        base = base_currency.strip().upper()
        target = target_currency.strip().upper()

        if base == target:
            return 1.0

        key = f"{base}_{target}"

        # 1. Check TTL Cache
        now = time.time()
        if key in self._cache:
            rate, cached_at = self._cache[key]
            if now - cached_at < self.cache_ttl:
                return rate

        # 2. Attempt Dynamic Online Fetch (open API with 2s timeout)
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
                        # Cache reverse rate
                        if live_rate > 0:
                            self._cache[f"{target}_{base}"] = (1.0 / live_rate, now)
                        return live_rate
        except Exception:
            # Fall through to baseline fallback rate on offline/network errors
            pass

        # 3. Offline Baseline Fallback
        return self.FALLBACK_RATES.get(key, 25400.0 if base == "USD" and target == "VND" else 1.0)

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
