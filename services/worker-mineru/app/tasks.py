"""MinerU worker.

Handles: scanned PDFs, complex PDFs with multi-page tables, formulas, charts,
Chinese financial reports.

This module is a scaffold. Fill in `_parse_with_mineru()` with the actual
MinerU invocation to make it work.

See: https://github.com/opendatalab/MinerU
"""

from __future__ import annotations

import logging
import os

from celery import Celery

log = logging.getLogger(__name__)

_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

app = Celery("dph-worker-mineru", broker=_BROKER_URL, backend=_RESULT_BACKEND)
app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # 1 task per GPU worker
    broker_connection_retry_on_startup=True,
)


@app.task(name="queue.mineru.parse", bind=True, max_retries=3, default_retry_delay=30)
def parse(self, job_id: str, source_uri: str, doc_type: str) -> dict:
    """Parse a document using MinerU.

    TODO(engine): wire up the actual MinerU pipeline. Steps:
      1. Download source_uri to local disk (MinIO client).
      2. Run MinerU: magic_pdf.pipe.UNIPipe(...) or the current recommended entry.
      3. Upload result.md, result.json, and any figures back to MinIO.
      4. Publish postproc task via app.send_task("queue.postproc.run", ...).

    Returns a dict with the MinIO result_uri so the orchestrator can update
    the job record (currently via a separate "results" callback task — TBD).
    """
    log.info("mineru.parse job_id=%s source=%s doc_type=%s", job_id, source_uri, doc_type)
    try:
        result = _parse_with_mineru(source_uri, doc_type)
    except MemoryError as exc:
        # GPU OOM: surface a retry with fallback hint
        log.warning("mineru OOM for job_id=%s, requesting docling fallback", job_id)
        raise self.retry(exc=exc, countdown=10) from exc
    except Exception as exc:
        log.exception("mineru.parse failed job_id=%s", job_id)
        raise self.retry(exc=exc) from exc

    # TODO(orchestrator): post back to orchestrator-api with result_uri so jobs
    # table can move to `postproc` / `succeeded` state.
    return {"job_id": job_id, "result": result}


def _parse_with_mineru(source_uri: str, doc_type: str) -> dict:
    """Real MinerU invocation. STUB — implement me."""
    # Placeholder until the engine is wired in.
    return {
        "stub": True,
        "message": "MinerU not yet integrated. See app/tasks.py:_parse_with_mineru",
        "source_uri": source_uri,
        "doc_type": doc_type,
    }
