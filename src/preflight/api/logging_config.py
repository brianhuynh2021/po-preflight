from __future__ import annotations

import logging
import os
import sys
import time
import traceback
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from preflight.observability.context import (
    request_id_var,
    user_id_var,
    order_id_var,
    set_request_id,
    set_user_id,
    set_order_id,
)
from preflight.observability.logging import (
    JsonLogFormatter,
    ColoredLogFormatter,
    configure_logging,
    BOLD,
    CYAN,
    DIM,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    WHITE,
    YELLOW,
)

# Method Colors
METHOD_COLORS = {
    "GET": "\033[34m",
    "POST": "\033[32m",
    "PUT": "\033[33m",
    "DELETE": "\033[31m",
    "PATCH": "\033[35m",
    "OPTIONS": "\033[36m",
}

# Ensure global logging is configured
formatter = configure_logging()
logger = logging.getLogger("preflight.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that correlates request_id, user_id, logs responses, tracks Prometheus metrics and persists 5xx errors."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:8]
        request.state.request_id = request_id

        # Set ContextVars
        token_req = set_request_id(request_id)

        # Extract user if available in cookie/auth
        user_id = ""
        cookie_sess = request.cookies.get("pf_session")
        if cookie_sess:
            try:
                from preflight.security.session import verify_session_token
                principal = verify_session_token(cookie_sess)
                user_id = principal.username
            except Exception:
                pass
        token_user = set_user_id(user_id) if user_id else None

        method = request.method
        method_color = METHOD_COLORS.get(method, WHITE)
        path = request.url.path

        # Check if JSON logging is active
        is_json = os.getenv("PREFLIGHT_LOG_FORMAT", "").lower() == "json" or (
            os.getenv("PREFLIGHT_ENV", "").lower() == "production" and os.getenv("PREFLIGHT_LOG_FORMAT", "").lower() != "text"
        )

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            status_code = response.status_code
            if 200 <= status_code < 300:
                status_color = GREEN
            elif 300 <= status_code < 400:
                status_color = CYAN
            elif 400 <= status_code < 500:
                status_color = YELLOW
            else:
                status_color = RED

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            if is_json:
                logger.info(
                    f"{method} {path} -> {status_code} ({duration_ms:.2f}ms)",
                    extra={"method": method, "path": path, "status_code": status_code, "duration_ms": duration_ms},
                )
            else:
                logger.info(
                    f"{method_color}{BOLD}{method:<6}{RESET} {path:<28} "
                    f"-> {status_color}{BOLD}{status_code}{RESET} "
                    f"({duration_ms:.2f}ms)"
                )

            # Record Prometheus OpenMetrics
            try:
                from preflight.observability.metrics import metrics_registry

                metrics_registry.record_http_request(method, path, status_code, duration_ms / 1000.0)
            except Exception:
                pass

            # Record 5xx errors into store
            if status_code >= 500:
                try:
                    from preflight.api.deps import get_db_path
                    from preflight.store import create_audit_store
                    with create_audit_store(get_db_path()) as store:
                        store.record_request_error(
                            request_id=request_id,
                            endpoint=f"{method} {path}",
                            status_code=status_code,
                            error_message=f"HTTP {status_code}",
                            traceback_str="",
                        )
                except Exception:
                    pass

            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            tb_str = traceback.format_exc()
            if is_json:
                logger.error(
                    f"{method} {path} -> 500 ERROR ({duration_ms:.2f}ms): {exc}",
                    extra={"method": method, "path": path, "status_code": 500, "duration_ms": duration_ms, "exception": str(exc)},
                )
            else:
                logger.error(
                    f"{method_color}{BOLD}{method:<6}{RESET} {path:<28} "
                    f"-> {RED}{BOLD}500 ERROR{RESET} ({duration_ms:.2f}ms) "
                    f"- Exception: {exc}"
                )

            # Record 5xx exception into store
            try:
                from preflight.api.deps import get_db_path
                from preflight.store import create_audit_store
                with create_audit_store(get_db_path()) as store:
                    store.record_request_error(
                        request_id=request_id,
                        endpoint=f"{method} {path}",
                        status_code=500,
                        error_message=str(exc),
                        traceback_str=tb_str,
                    )
            except Exception:
                pass

            raise
