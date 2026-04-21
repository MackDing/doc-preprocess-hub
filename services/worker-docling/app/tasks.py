"""docling worker.

Handles: native PDFs, Office (docx/xlsx/pptx), HTML, Markdown, email (eml/msg).

This module is a scaffold. Fill in `_parse_with_docling()` with the actual
docling invocation to make it work.

See: https://github.com/DS4SD/docling
"""

from __future__ import annotations

import logging
import os

from celery import Celery

log = logging.getLogger(__name__)

_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

app = Celery("dph-worker-docling", broker=_BROKER_URL, backend=_RESULT_BACKEND)
app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=4,  # CPU, can parallelize
    broker_connection_retry_on_startup=True,
)


@app.task(name="queue.docling.parse", bind=True, max_retries=3, default_retry_delay=15)
def parse(self, job_id: str, source_uri: str, doc_type: str) -> dict:
    """Parse a document using docling.

    TODO(engine): wire up docling. Steps:
      1. Download source_uri to a temp file (MinIO client).
      2. from docling.document_converter import DocumentConverter
         result = DocumentConverter().convert(path)
      3. Serialize result.document.export_to_markdown() and to_dict() into MinIO.
      4. Publish postproc task via app.send_task("queue.postproc.run", ...).
    """
    log.info("docling.parse job_id=%s source=%s doc_type=%s", job_id, source_uri, doc_type)
    try:
        result = _parse_with_docling(source_uri, doc_type)
    except Exception as exc:
        log.exception("docling.parse failed job_id=%s", job_id)
        raise self.retry(exc=exc) from exc

    return {"job_id": job_id, "result": result}


def _parse_with_docling(source_uri: str, doc_type: str) -> dict:
    """Real docling invocation. STUB — implement me."""
    return {
        "stub": True,
        "message": "docling not yet integrated. See app/tasks.py:_parse_with_docling",
        "source_uri": source_uri,
        "doc_type": doc_type,
    }
