# worker-mineru

Celery worker for MinerU-powered parsing.

**Status:** scaffold. The MinerU pipeline itself is not yet wired in.

## Why MinerU?

MinerU is optimized for:
- Scanned PDFs
- Complex tables spanning multiple pages
- Formulas (LaTeX output)
- Charts and figures
- Chinese financial documents

See https://github.com/opendatalab/MinerU.

## GPU

MinerU requires a GPU. This worker is not started by the default `docker compose up` — it's gated behind the `gpu` profile:

```bash
docker compose --profile gpu up worker-mineru
```

## What to implement

Open `app/tasks.py` and fill in `_parse_with_mineru()`. The steps are listed in the docstring of `parse()`.

## TODOs

- [ ] Wire up the actual MinerU pipeline
- [ ] Bake model weights into the Docker image (see docs/deployment.md)
- [ ] Add a `health` task for readiness probes
- [ ] Wire post-processing handoff via `app.send_task("queue.postproc.run", ...)`
