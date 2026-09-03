from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from typing import Any

from arq.connections import RedisSettings
from arq.cron import cron
from arq.worker import run_worker

from preflight.jobs.definitions import (
    analyze_order,
    email_poll,
    escalation_check,
    inventory_sync,
    notify,
    outbox_dispatch,
    run_ocr,
)
from preflight.jobs.queue import get_redis_url

logger = logging.getLogger("PreflightWorker")


async def startup(ctx: dict[str, Any]) -> None:
    logger.info("PO Preflight Background Worker started.")


async def shutdown(ctx: dict[str, Any]) -> None:
    logger.info("PO Preflight Background Worker shutting down gracefully.")


# Cron expressions (configurable via env)
CRON_OUTBOX_MIN = os.getenv("PREFLIGHT_CRON_OUTBOX", "*")  # Every 1 minute
CRON_INVENTORY_MIN = os.getenv("PREFLIGHT_CRON_INVENTORY", "*/30")  # Every 30 minutes
CRON_EMAIL_MIN = os.getenv("PREFLIGHT_CRON_EMAIL", "*/2")  # Every 2 minutes
CRON_ESCALATION_MIN = os.getenv("PREFLIGHT_CRON_ESCALATION", "*/15")  # Every 15 minutes


class WorkerSettings:
    """arq Worker Settings for background PO processing."""

    functions = [analyze_order, run_ocr, outbox_dispatch, inventory_sync, email_poll, notify, escalation_check]
    cron_jobs = [
        cron(outbox_dispatch, minute=CRON_OUTBOX_MIN, unique=True),
        cron(inventory_sync, minute=CRON_INVENTORY_MIN, unique=True),
        cron(email_poll, minute=CRON_EMAIL_MIN, unique=True),
        cron(escalation_check, minute=CRON_ESCALATION_MIN, unique=True),
    ]

    # Redis connection settings
    redis_url = get_redis_url() or "redis://localhost:6379/0"
    redis_settings = RedisSettings.from_dsn(redis_url)

    max_retries = 3
    retry_delay = 5
    job_timeout = 300  # 5 minutes

    on_startup = startup
    on_shutdown = shutdown


def start_worker(burst: bool = False) -> None:
    """CLI Entrypoint to start the worker process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Starting PO Preflight arq worker (burst=%s, redis=%s)...", burst, WorkerSettings.redis_url)

    try:
        run_worker(WorkerSettings, burst=burst)
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user.")
    except Exception as exc:
        logger.error("Worker encountered fatal error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    start_worker()
