# worker-docling

Celery worker for docling-powered parsing.

**Status:** scaffold. The docling pipeline itself is not yet wired in.

## Why docling?

docling is optimized for:
- Native PDFs (digital-origin, no OCR needed)
- Office files (docx, xlsx, pptx)
- HTML, Markdown
- Email (eml, msg)
- Document governance metadata

See https://github.com/DS4SD/docling.

## Run

```bash
celery -A app.tasks worker --loglevel=INFO -Q queue.docling
```

Or via docker-compose:
```bash
docker compose up worker-docling
```

## What to implement

Open `app/tasks.py` and fill in `_parse_with_docling()`.
