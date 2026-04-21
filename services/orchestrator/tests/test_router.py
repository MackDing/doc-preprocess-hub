"""Test the engine routing logic."""

from __future__ import annotations

from app.router import queue_for_engine, select_engine


def test_scan_goes_to_mineru() -> None:
    assert select_engine("pdf-scan") == "mineru"


def test_native_pdf_goes_to_docling() -> None:
    assert select_engine("pdf-native") == "docling"


def test_office_goes_to_docling() -> None:
    for t in ("docx", "xlsx", "pptx", "html"):
        assert select_engine(t) == "docling"


def test_unknown_defaults_to_docling() -> None:
    assert select_engine("totally-unknown") == "docling"


def test_queue_naming() -> None:
    assert queue_for_engine("mineru") == "queue.mineru"
    assert queue_for_engine("docling") == "queue.docling"
