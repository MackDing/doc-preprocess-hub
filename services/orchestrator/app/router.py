"""Document routing: decide which engine handles which doc type.

This is intentionally simple. Override via config or a more sophisticated
classifier (e.g. file-header sniffing, ML-based routing) in production.
"""

from __future__ import annotations

MINERU_TYPES = {
    "pdf-scan",
    "pdf-complex",
    "pdf-financial",  # Chinese financial reports with complex tables
}

DOCLING_TYPES = {
    "pdf-native",
    "docx",
    "xlsx",
    "pptx",
    "html",
    "md",
    "email",
    "eml",
    "msg",
}


def select_engine(doc_type: str) -> str:
    """Return 'mineru' or 'docling' given a document type hint.

    Default is docling (CPU, cheaper, wider coverage). MinerU is reserved
    for the cases where its GPU cost is justified.
    """
    if doc_type in MINERU_TYPES:
        return "mineru"
    if doc_type in DOCLING_TYPES:
        return "docling"
    # Unknown type: default to docling. Caller can override after sniffing.
    return "docling"


def queue_for_engine(engine: str) -> str:
    """Celery queue name for the engine's worker."""
    return f"queue.{engine}"
