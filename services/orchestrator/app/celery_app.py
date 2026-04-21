"""Celery app used by the orchestrator to dispatch tasks.

Workers import their own Celery apps pointing at the same broker. The
orchestrator never executes tasks itself, it only sends them.
"""

from __future__ import annotations

from celery import Celery

from .config import get_settings

_settings = get_settings()

celery_app = Celery(
    "dph-orchestrator",
    broker=_settings.celery_broker_url,
    backend=_settings.celery_result_backend,
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)


def send_parse_task(queue: str, job_id: str, source_uri: str, doc_type: str) -> None:
    """Dispatch a parsing task to the given queue without importing worker code."""
    celery_app.send_task(
        f"{queue}.parse",
        args=[job_id, source_uri, doc_type],
        queue=queue,
    )
