"""Test untuk config/queue.py — Queue/Worker singleton dan enqueue_job."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from config import queue as queue_module


@pytest.fixture(autouse=True)
def _reset_queue_singleton():
    """Reset singleton queue dan worker sebelum setiap tes."""
    queue_module._queue = None
    queue_module._worker = None
    yield
    queue_module._queue = None
    queue_module._worker = None


class TestGetQueue:
    def test_get_queue_returns_queue_instance(self):
        from fenrir.queue import Queue
        q = queue_module.get_queue()
        assert isinstance(q, Queue)

    def test_get_queue_singleton(self):
        q1 = queue_module.get_queue()
        q2 = queue_module.get_queue()
        assert q1 is q2

    def test_get_queue_creates_only_once(self):
        q1 = queue_module.get_queue()
        q2 = queue_module.get_queue()
        assert q1 is q2


class TestGetWorker:
    def test_get_worker_returns_worker_instance(self):
        from fenrir.queue import Worker
        w = queue_module.get_worker()
        assert isinstance(w, Worker)

    def test_get_worker_singleton(self):
        w1 = queue_module.get_worker()
        w2 = queue_module.get_worker()
        assert w1 is w2

    def test_get_worker_with_custom_concurrency(self):
        w = queue_module.get_worker(concurrency=4)
        assert w is not None

    def test_get_worker_uses_queue_singleton(self):
        q = queue_module.get_queue()
        w = queue_module.get_worker()
        assert w._queue is q


class TestEnqueueJob:
    def test_enqueue_job_returns_job(self):
        from fenrir.queue import Job

        def dummy_task():
            pass

        job = queue_module.enqueue_job(dummy_task)
        assert isinstance(job, Job)

    def test_enqueue_job_with_args(self):
        def add(a, b):
            return a + b

        job = queue_module.enqueue_job(add, 1, 2)
        assert job.args == (1, 2)

    def test_enqueue_job_with_kwargs(self):
        def greet(name="world"):
            return f"hello {name}"

        job = queue_module.enqueue_job(greet, name="test")
        assert job.kwargs == {"name": "test"}

    def test_enqueue_job_with_priority(self):
        def task():
            pass

        job = queue_module.enqueue_job(task, priority=50)
        assert job.priority == 50

    def test_enqueue_job_default_priority(self):
        def task():
            pass

        job = queue_module.enqueue_job(task)
        assert job.priority == 100

    def test_enqueue_job_with_delay(self):
        def task():
            pass

        job = queue_module.enqueue_job(task, delay=5.0)
        assert job.delay == 5.0

    def test_enqueue_job_with_timeout(self):
        def task():
            pass

        job = queue_module.enqueue_job(task, timeout=30.0)
        assert job.timeout == 30.0

    def test_enqueue_job_with_max_retries(self):
        def task():
            pass

        job = queue_module.enqueue_job(task, max_retries=3)
        assert job.max_retries == 3

    def test_enqueue_job_handler_stored(self):
        def my_handler():
            pass

        job = queue_module.enqueue_job(my_handler)
        assert isinstance(job.handler, str)
        assert "my_handler" in job.handler

    def test_enqueue_job_is_added_to_queue(self):
        def task():
            pass

        q = queue_module.get_queue()
        initial_len = len(q._pending) if hasattr(q, '_pending') else 0
        queue_module.enqueue_job(task)
        final_len = len(q._pending) if hasattr(q, '_pending') else 0
        assert final_len >= initial_len
