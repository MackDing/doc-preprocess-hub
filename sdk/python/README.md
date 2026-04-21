# doc-preprocess-hub — Python SDK

Thin client for the orchestrator API.

## Install

```bash
pip install doc-preprocess-hub   # once published to PyPI
# or from source:
pip install -e sdk/python
```

## Usage

```python
from doc_preprocess_hub import Client

with Client(base_url="https://dph.example.com", token="your-jwt") as c:
    job = c.submit(
        business_ref="DD-2026-001",
        source_url="https://my-bucket.example.com/docs/report.pdf",
        tenant_scene="credit",
    )
    result = c.wait(job.job_id, timeout=300)
    print(result.status, result.result_urls.md)
```

## API

- `Client(base_url, token=None, timeout=30.0)`
- `.submit(business_ref, source_url, source_type='presigned_url', ...)` → `Job`
- `.get(job_id)` → `JobStatus`
- `.cancel(job_id)` → `bool`
- `.wait(job_id, timeout=300, poll_interval=3)` → `JobStatus` (terminal)
