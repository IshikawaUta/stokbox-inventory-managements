"""Background Queue & Worker — Integrasi Fenrir Queue/MemoryQueue untuk background jobs."""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from fenrir.queue import MemoryQueue, Queue, Worker, Job

logger = logging.getLogger("inventaris.queue")

# ── Singleton Queue + Worker ────────────────────────────────────────────

_queue: Optional[Queue] = None
_worker: Optional[Worker] = None


def get_queue() -> Queue:
    """Ambil singleton queue instance."""
    global _queue
    if _queue is None:
        _queue = Queue(backend=MemoryQueue())
    return _queue


def get_worker(concurrency: int = 2) -> Worker:
    """Ambil singleton worker instance."""
    global _worker
    if _worker is None:
        _worker = Worker(queue=get_queue(), concurrency=concurrency, poll_interval=0.5)
    return _worker


def enqueue_job(
    func: Callable,
    *args: Any,
    priority: int = 100,
    delay: Optional[float] = None,
    timeout: Optional[float] = None,
    max_retries: int = 0,
    **kwargs: Any,
) -> Job:
    """Enqueue job ke background queue.

    Contoh:
        enqueue_job(send_notification, "user123", "Stok rendah!", priority=50)
        enqueue_job(heavy_computation, data, delay=10.0)
    """
    import asyncio

    q = get_queue()

    handler_name = getattr(func, '_queue_name', None) or f"{func.__module__}.{func.__qualname__}"
    q.register(handler_name, func)

    job = Job(
        handler=handler_name,
        args=args,
        kwargs=kwargs,
        priority=priority,
        delay=delay or 0,
        timeout=timeout,
        max_retries=max_retries,
    )

    backend = q.backend

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(backend.enqueue(job))
    except RuntimeError:
        asyncio.run(backend.enqueue(job))

    logger.info(f"Job di-enqueue: {func.__name__} (priority={priority})")
    return job
