from __future__ import annotations

import enum
import logging
import threading
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger("PreflightResilience")

T = TypeVar("T")


class CircuitState(str, enum.Enum):
    CLOSED = "CLOSED"  # Healthy, traffic flows normally
    OPEN = "OPEN"  # Unhealthy, fast-fail without calling backend
    HALF_OPEN = "HALF_OPEN"  # Trial probe testing backend recovery


class CircuitBreakerOpenException(Exception):
    """Raised when an execution is attempted on an open circuit breaker."""

    def __init__(self, name: str, retry_after_sec: float):
        super().__init__(f"Circuit breaker '{name}' is OPEN. Fast-failing (retry after {retry_after_sec:.1f}s).")
        self.name = name
        self.retry_after_sec = retry_after_sec


class CircuitBreaker:
    """Enterprise Circuit Breaker (FAANG / Netflix Hystrix pattern)."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_sec: float = 30.0,
        half_open_success_threshold: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.half_open_success_threshold = half_open_success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._consecutive_successes = 0
        self._last_state_change = time.time()
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                now = time.time()
                if now - self._last_state_change >= self.recovery_timeout_sec:
                    self._state = CircuitState.HALF_OPEN
                    self._last_state_change = now
                    logger.info(f"Circuit '{self.name}' transitioned from OPEN -> HALF_OPEN (probing recovery).")
            return self._state

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute callable through circuit breaker guard."""
        current_state = self.state

        if current_state == CircuitState.OPEN:
            remaining = max(0.0, self.recovery_timeout_sec - (time.time() - self._last_state_change))
            raise CircuitBreakerOpenException(self.name, remaining)

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure(exc)
            raise

    def _on_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._consecutive_successes += 1
                if self._consecutive_successes >= self.half_open_success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._consecutive_successes = 0
                    self._last_state_change = time.time()
                    logger.info(f"Circuit '{self.name}' recovered: HALF_OPEN -> CLOSED.")
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def _on_failure(self, exc: Exception) -> None:
        with self._lock:
            self._failure_count += 1
            now = time.time()
            if self._state == CircuitState.HALF_OPEN or self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._last_state_change = now
                self._consecutive_successes = 0
                logger.warning(
                    f"Circuit '{self.name}' tripped -> OPEN due to error: {exc} (Failures: {self._failure_count})"
                )

    def reset(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._consecutive_successes = 0
            self._last_state_change = time.time()


# Global circuit breakers for external systems
vision_ai_circuit_breaker = CircuitBreaker("gemini_vision_ocr", failure_threshold=3, recovery_timeout_sec=15.0)
erp_circuit_breaker = CircuitBreaker("erp_outbox_gateway", failure_threshold=5, recovery_timeout_sec=20.0)
