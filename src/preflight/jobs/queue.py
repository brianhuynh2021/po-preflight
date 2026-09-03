from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any, Callable, Coroutine

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

logger = logging.getLogger("PreflightJobQueue")

_POOL: ArqRedis | None = None
_POOL_LOCK = asyncio.Lock() if hasattr(asyncio, "Lock") else None

JOB_REGISTRY: dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {}


def register_job(name: str, func: Callable[..., Coroutine[Any, Any, Any]]) -> None:
    JOB_REGISTRY[name] = func


def get_redis_url() -> str | None:
    url = os.getenv("REDIS_URL", "").strip()
    return url if (url and url.startswith("redis")) else None


def get_queue_mode() -> str:
    return "arq_redis" if get_redis_url() else "in_memory"


async def get_redis_pool() -> ArqRedis | None:
    global _POOL
    url = get_redis_url()
    if not url:
        return None

    if _POOL is not None:
        return _POOL

    try:
        settings = RedisSettings.from_dsn(url)
        _POOL = await create_pool(settings)
        logger.info("Connected to arq Redis job queue: %s", url)
        return _POOL
    except Exception as exc:
        logger.warning("Could not connect to Redis pool (%s). Fallback to in-memory: %s", url, exc)
        return None


async def enqueue_job(job_name: str, *args: Any, **kwargs: Any) -> str:
    """Enqueue a job to arq Redis queue, or execute locally in memory if Redis is unavailable."""
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    pool = await get_redis_pool()

    if pool is not None:
        try:
            job = await pool.enqueue_job(job_name, *args, _job_id=job_id, **kwargs)
            logger.info("Enqueued arq job '%s' with id '%s'", job_name, job_id)
            return job_id
        except Exception as exc:
            logger.warning("Failed to enqueue to arq Redis (%s), falling back to local: %s", job_name, exc)

    # In-memory execution
    func = JOB_REGISTRY.get(job_name)
    if not func:
        logger.error("Job '%s' not registered in JOB_REGISTRY", job_name)
        return job_id

    ctx = {"job_id": job_id, "job_try": 1}

    async def _runner():
        try:
            await func(ctx, *args, **kwargs)
        except Exception as e:
            logger.exception("In-memory job '%s' (%s) failed: %s", job_name, job_id, e)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_runner())
    except RuntimeError:
        # If no loop is running, run synchronously
        asyncio.run(_runner())

    return job_id


def sync_enqueue_job(job_name: str, *args: Any, **kwargs: Any) -> str:
    """Synchronously enqueue a job regardless of current thread's event loop state."""
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            task = loop.create_task(enqueue_job(job_name, *args, **kwargs))
            # Generate deterministic or random id to return immediately
            return f"job-{uuid.uuid4().hex[:8]}"
        return loop.run_until_complete(enqueue_job(job_name, *args, **kwargs))
    except RuntimeError:
        return asyncio.run(enqueue_job(job_name, *args, **kwargs))
