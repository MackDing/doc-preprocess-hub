# orchestrator-api

FastAPI service that accepts document processing requests and dispatches them to the worker pool.

## Run locally

```bash
# From the repo root:
docker compose up -d postgres redis rabbitmq minio

# Then from this directory:
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

OpenAPI docs at http://localhost:8000/docs

## Test

```bash
pytest
```

## Contracts

See [../../ARCHITECTURE.md](../../ARCHITECTURE.md) for the full API contract.
The v1 API surface is frozen. Breaking changes go to `/v2/`.

## TODOs

- [ ] OIDC / JWT middleware (currently trust-all in dev)
- [ ] OpenTelemetry full instrumentation
- [ ] MinIO pre-signed URL generation for result URLs
- [ ] Webhook subscription endpoints
- [ ] Celery task revocation on cancel
