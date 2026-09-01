from __future__ import annotations

import logging
import sys
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Foreground Colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
WHITE = "\033[37m"

# Method Colors
METHOD_COLORS = {
    "GET": BLUE,
    "POST": GREEN,
    "PUT": YELLOW,
    "DELETE": RED,
    "PATCH": MAGENTA,
    "OPTIONS": CYAN,
}


class ColoredFormatter(logging.Formatter):
    """Custom ANSI formatter for beautiful terminal logs."""

    def format(self, record: logging.LogRecord) -> str:
        # Time string
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
        time_str = f"{DIM}[{timestamp}]{RESET}"

        # Level coloring
        level = record.levelname
        if level == "INFO":
            level_str = f"{GREEN}{BOLD}INFO{RESET}"
        elif level == "WARNING":
            level_str = f"{YELLOW}{BOLD}WARN{RESET}"
        elif level == "ERROR":
            level_str = f"{RED}{BOLD}ERROR{RESET}"
        elif level == "DEBUG":
            level_str = f"{CYAN}{BOLD}DEBUG{RESET}"
        else:
            level_str = f"{WHITE}{BOLD}{level}{RESET}"

        tag_str = f"{MAGENTA}[PreflightAPI]{RESET}"
        msg = record.getMessage()

        return f"{time_str} {level_str} {tag_str} {msg}"


def setup_logger(name: str = "preflight.api") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs incoming requests and responses with latency and colored status."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:8]

        method = request.method
        method_color = METHOD_COLORS.get(method, WHITE)
        path = request.url.path

        # Process the request
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

            # Avoid spamming logs with frequent healthcheck polls if desired, but format nicely
            logger.info(
                f"{method_color}{BOLD}{method:<6}{RESET} {path:<28} "
                f"-> {status_color}{BOLD}{status_code}{RESET} "
                f"({duration_ms:.2f}ms) {DIM}[req_id={request_id}]{RESET}"
            )

            # Record Prometheus OpenMetrics
            try:
                from preflight.observability.metrics import metrics_registry

                metrics_registry.record_http_request(method, path, status_code, duration_ms / 1000.0)
            except Exception:
                pass

            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"{method_color}{BOLD}{method:<6}{RESET} {path:<28} "
                f"-> {RED}{BOLD}500 ERROR{RESET} ({duration_ms:.2f}ms) "
                f"[req_id={request_id}] - Exception: {exc}"
            )
            raise
