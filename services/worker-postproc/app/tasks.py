"""Post-processing worker.

Pipeline:
  parsed markdown/JSON → PII redaction (Presidio) → chunking (LangChain) → MinIO

This module is a scaffold. Fill in `_redact_pii()` and `_chunk()` with real
implementations. The whitelist config format is defined below and SHOULD be
stable even while the engine evolves.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from celery import Celery

log = logging.getLogger(__name__)

_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

app = Celery("dph-worker-postproc", broker=_BROKER_URL, backend=_RESULT_BACKEND)
app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=4,
    broker_connection_retry_on_startup=True,
)


# --- PII whitelist config ---------------------------------------------------
#
# Per-scene whitelist: entities here are NOT redacted when found in the
# specified field (or when they match a custom regex). This is the single
# most important policy knob in the system — your compliance team owns it.
#
# Shape:
#   {
#     "scene": "credit",
#     "entities": {
#         "CREDIT_CARD": {
#             "whitelist_contexts": ["customer_query_form", "business_ref"],
#             "whitelist_patterns": ["^TEST-\\d{4}$"],
#         },
#         ...
#     }
#   }
#
# Load from Postgres `pii_whitelist` table or a YAML file — for MVP, YAML is fine.


@dataclass
class ChunkingConfig:
    """LangChain splitter config."""

    chunk_size: int = 1000
    chunk_overlap: int = 150
    preserve_tables: bool = True


@app.task(name="queue.postproc.run", bind=True, max_retries=3, default_retry_delay=10)
def run(self, job_id: str, parsed_uri: str, tenant_scene: str) -> dict:
    """Run PII redaction + chunking on a parsed document.

    TODO: download parsed markdown from parsed_uri, redact PII per scene policy,
    chunk the result, upload redacted + chunks back to MinIO, notify
    orchestrator-api that the job is ready.
    """
    log.info("postproc.run job_id=%s parsed_uri=%s scene=%s", job_id, parsed_uri, tenant_scene)
    try:
        redacted = _redact_pii(parsed_uri, tenant_scene)
        chunks = _chunk(redacted, ChunkingConfig())
    except Exception as exc:
        log.exception("postproc.run failed job_id=%s", job_id)
        raise self.retry(exc=exc) from exc

    return {"job_id": job_id, "redacted": redacted, "chunks": chunks}


def _redact_pii(parsed_uri: str, tenant_scene: str) -> dict:
    """Presidio PII redaction. STUB — implement me.

    Apply the per-scene whitelist BEFORE redacting. A field in the whitelist
    must NOT be touched even if Presidio flags it. Compliance red line:
    whitelist precision > 99%, recall > 99%.
    """
    return {"stub": True, "parsed_uri": parsed_uri, "scene": tenant_scene}


def _chunk(document: dict, config: ChunkingConfig) -> list[dict]:
    """LangChain text-splitter chunking. STUB — implement me.

    Must preserve table structure when `preserve_tables=True`. Do not split
    a markdown table mid-row.
    """
    return [{"stub": True, "chunk_size": config.chunk_size}]
