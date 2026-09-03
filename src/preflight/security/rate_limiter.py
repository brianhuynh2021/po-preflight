from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


import os


class SlidingWindowRateLimiter:
    """Thread-safe sliding window rate limiter for DDoS and abuse mitigation.
    
    Supports:
    - Redis-backed distributed sliding window across processes when REDIS_URL is present.
    - Thread-safe in-memory deque sliding window fallback.
    """

    def __init__(self, default_limit: int = 120, window_seconds: int = 60, redis_url: str | None = None):
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._history: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self.enabled = os.getenv("PREFLIGHT_RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self._redis = None

        if self.redis_url:
            try:
                import redis
                self._redis = redis.Redis.from_url(self.redis_url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

        # Custom path limits
        self.path_limits: dict[str, int] = {
            "/api/v1/orders/upload": 30,  # 30 uploads/min
            "/api/v1/ingest/extract": 30,  # 30 OCR extractions/min
            "/api/v1/bot/telegram/webhook": 60,  # 60 webhooks/min
        }

    @property
    def mode(self) -> str:
        current_redis = os.getenv("REDIS_URL") or self.redis_url
        if current_redis:
            return "redis"
        return "in_memory"

    def is_allowed(self, client_key: str, path: str = "") -> tuple[bool, int]:
        """Check if request is within rate limit. Returns (is_allowed, remaining_requests)."""
        if not self.enabled:
            return True, self.default_limit

        now = time.time()
        cutoff = now - self.window_seconds
        limit = self.path_limits.get(path, self.default_limit)

        current_redis_url = os.getenv("REDIS_URL") or self.redis_url
        if current_redis_url:
            if not self._redis:
                try:
                    import redis
                    self._redis = redis.Redis.from_url(current_redis_url, decode_responses=True)
                except Exception:
                    self._redis = None

            if self._redis:
                key = f"preflight:ratelimit:{client_key}:{path or 'default'}"
                try:
                    pipe = self._redis.pipeline()
                    pipe.zremrangebyscore(key, 0, cutoff)
                    pipe.zcard(key)
                    _, count = pipe.execute()

                    if count >= limit:
                        return False, 0

                    pipe = self._redis.pipeline()
                    pipe.zadd(key, {f"{now}_{time.time_ns()}": now})
                    pipe.expire(key, self.window_seconds + 5)
                    pipe.execute()
                    return True, max(0, limit - (count + 1))
                except Exception:
                    pass

        # In-memory fallback
        with self._lock:
            timestamps = self._history[client_key]
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            if len(timestamps) >= limit:
                return False, 0

            timestamps.append(now)
            return True, limit - len(timestamps)

    def reset(self):
        """Clear all rate limit histories."""
        with self._lock:
            self._history.clear()
        if self._redis:
            try:
                keys = self._redis.keys("preflight:ratelimit:*")
                if keys:
                    self._redis.delete(*keys)
            except Exception:
                pass


global_rate_limiter = SlidingWindowRateLimiter()



import json


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware to enforce sliding window rate limiting."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip health, metrics, and docs endpoints
        path = request.url.path
        if path in ("/health", "/health/live", "/health/ready", "/metrics", "/docs", "/openapi.json"):
            return await call_next(request)

        # Identify client by API Key header or Client IP
        client_key = request.headers.get("X-API-Key") or (
            request.client.host if request.client else "127.0.0.1"
        )

        allowed, remaining = global_rate_limiter.is_allowed(client_key, path)
        if not allowed:
            req_id = request.headers.get("X-Request-ID", "")
            doc = {
                "type": "https://popreflight.vn/errors/rate_limited",
                "title": "Too Many Requests",
                "status": 429,
                "code": "RATE_LIMITED",
                "detail": "Vượt quá giới hạn tần suất yêu cầu. Vui lòng thử lại sau 60 giây.",
                "request_id": req_id,
            }
            return Response(
                content=json.dumps(doc),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/problem+json",
                headers={"Retry-After": "60", "X-RateLimit-Remaining": "0", "X-Request-ID": req_id},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
