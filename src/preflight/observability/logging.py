from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

from preflight.observability.context import get_logging_context, get_request_id, get_user_id, get_order_id

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
WHITE = "\033[37m"


class JsonLogFormatter(logging.Formatter):
    """Structured JSON formatter for production and observability tooling (ELK, Datadog, CloudWatch)."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Correlate context variables
        req_id = get_request_id() or getattr(record, "request_id", None)
        if req_id:
            log_data["request_id"] = req_id

        usr_id = get_user_id() or getattr(record, "user_id", None)
        if usr_id:
            log_data["user_id"] = usr_id

        ord_id = get_order_id() or getattr(record, "order_id", None)
        if ord_id:
            log_data["order_id"] = ord_id

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include custom extra fields if present
        for key, val in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "message", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName",
                "request_id", "user_id", "order_id"
            ):
                try:
                    json.dumps(val)
                    log_data[key] = val
                except (TypeError, ValueError):
                    log_data[key] = str(val)

        return json.dumps(log_data, ensure_ascii=False)


class ColoredLogFormatter(logging.Formatter):
    """Human-friendly ANSI terminal formatter with request ID and user correlation."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
        time_str = f"{DIM}[{timestamp}]{RESET}"

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

        ctx_parts = []
        req_id = get_request_id() or getattr(record, "request_id", None)
        if req_id:
            ctx_parts.append(f"req_id={req_id}")
        usr_id = get_user_id() or getattr(record, "user_id", None)
        if usr_id:
            ctx_parts.append(f"user={usr_id}")
        ord_id = get_order_id() or getattr(record, "order_id", None)
        if ord_id:
            ctx_parts.append(f"order={ord_id}")

        ctx_str = f" {DIM}[{', '.join(ctx_parts)}]{RESET}" if ctx_parts else ""

        formatted = f"{time_str} {level_str} {tag_str} {msg}{ctx_str}"
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        return formatted


def configure_logging(default_format: str | None = None) -> logging.Formatter:
    """Configure global logging format based on environment or configuration."""
    env = os.getenv("PREFLIGHT_ENV", "development").strip().lower()
    fmt_setting = (
        default_format
        or os.getenv("PREFLIGHT_LOG_FORMAT", "")
    ).strip().lower()

    # In production, default format is json
    if fmt_setting == "json" or (env == "production" and fmt_setting != "text"):
        formatter = JsonLogFormatter()
    else:
        formatter = ColoredLogFormatter()

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(formatter)

    return formatter
