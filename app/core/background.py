"""Background task dispatcher.

- Default: threaded executor (no external broker required).
- Optional: when USE_REDIS=True, delegates to Celery.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from app.config import settings

logger = logging.getLogger("certificate-generator.background")

_executor: ThreadPoolExecutor | None = None


def _get_executor() -> ThreadPoolExecutor:
    global _executor  # noqa: PLW0603
    if _executor is None or _executor._shutdown:
        _executor = ThreadPoolExecutor(max_workers=settings.BACKGROUND_WORKER_THREADS)
    return _executor


def dispatch_job(
    job_id: uuid.UUID,
    coro_factory: Callable,
    db_factory: Callable,
) -> None:
    """Dispatch a background job.

    If USE_REDIS is True, delegates to Celery; otherwise runs in a
    thread pool so the event loop is not blocked.
    """
    if settings.USE_REDIS:
        from app.tasks.celery_app import process_job_celery  # type: ignore[import-untyped]
        process_job_celery.delay(str(job_id), db_factory)
        return

    executor = _get_executor()
    executor.submit(lambda: asyncio.run(coro_factory(job_id, db_factory)))


async def shutdown_background() -> None:
    """Graceful shutdown of the thread pool."""
    global _executor  # noqa: PLW0603
    if _executor:
        _executor.shutdown(wait=True)