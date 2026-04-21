# Architecture

This document describes the architecture of `doc-preprocess-hub`: what each service does, how data flows, what we store, what the API contract is, and how we handle failures.

It is deliberately concrete. Vague architecture documents are lies told in markdown.

---

## 1. System overview

```
                        ┌──────────────────────┐
                        │   Business systems   │
                        │ (credit/compliance/..│
                        └──────────┬───────────┘
                                   │ HTTPS (SDK)
                                   ▼
                        ┌──────────────────────┐
                        │   APISIX gateway     │
                        │  - OIDC (your IAM)   │
                        │  - JWT verify        │
                        │  - per-scene rate    │
                        └──────────┬───────────┘
                                   │
                                   ▼
   ┌────────────────────────────────────────────────────┐
   │         orchestrator-api (FastAPI)                 │
   │  POST /v1/jobs          submit document            │
   │  GET  /v1/jobs/{id}     poll status / result       │
   │  POST /v1/jobs/{id}/cancel                         │
   │  POST /v1/webhooks      configure push callbacks   │
   │        ↓ writes to jobs table (Postgres)           │
   │        ↓ publishes to RabbitMQ queue               │
   └────────────────────────────────────────────────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                ▼                  ▼                  ▼
        [queue.mineru]     [queue.docling]    [queue.postproc]
                │                  │                  │
                ▼                  ▼                  ▼
        ┌───────────────┐  ┌───────────────┐  ┌────────────────┐
        │ worker-mineru │  │ worker-docling│  │ worker-postproc│
        │ (Celery, GPU) │  │ (Celery, CPU) │  │ (Celery, CPU)  │
        │ scans/complex │  │ Office/HTML   │  │ Presidio + LC  │
        │ PDFs          │  │ native PDFs   │  │ chunking       │
        └───────┬───────┘  └───────┬───────┘  └────────┬───────┘
                └──────────────────┴──────────────────┘
                                   │
                                   ▼
                   ┌──────────────────────────────┐
                   │  Storage layer               │
                   │  - Postgres  (metadata/audit)│
                   │  - MinIO     (raw + parsed)  │
                   │  - Redis     (cache)         │
                   └──────────────┬───────────────┘
                                  │
                ┌─────────────────┴─────────────────┐
                ▼                                   ▼
        [dispatcher]                        [webhook-sender]
         Pull channel                        Push channel
         client polls GET /v1/jobs/{id}      client pre-registers URL
```

## 2. Services

| Service           | Runtime          | Role                                                             | Scale point |
|-------------------|------------------|------------------------------------------------------------------|-------------|
| `orchestrator-api`| Python + FastAPI | REST API, job lifecycle, routing decisions                       | 3+ replicas |
| `worker-mineru`   | Python + Celery  | MinerU parser (scans, complex PDFs, formulas, tables)           | per-GPU replica |
| `worker-docling`  | Python + Celery  | docling parser (Office, HTML, native PDFs, email)               | CPU-scaled |
| `worker-postproc` | Python + Celery  | Presidio PII redaction + LangChain chunking                     | CPU-scaled |
| `webhook-sender`  | Python + Celery  | Push delivery with signed HMAC callbacks                         | 2+ replicas |
| `console-api`     | Python + FastAPI | Operator console backend                                         | 2 replicas |
| `console-ui`      | React (AntD Pro) | Operator console frontend                                        | 2 replicas |
| `governance-svc`  | Python + FastAPI | Model registry, license tracking (optional)                      | 1 replica |

---

## 3. Data model

### 3.1 Core tables

```sql
-- Main job table
CREATE TABLE jobs (
  id                    UUID PRIMARY KEY,                    -- UUIDv7
  tenant_scene          TEXT NOT NULL,                       -- e.g. 'default', 'credit', 'compliance'
  business_ref          TEXT NOT NULL,                       -- client-provided reference
  data_classification   TEXT NOT NULL,                       -- 'public'/'internal'/'confidential'/'restricted'
  source_uri            TEXT NOT NULL,                       -- MinIO URI of original document
  doc_type              TEXT NOT NULL,                       -- pdf-scan/pdf-native/docx/xlsx/pptx/html/email
  engine                TEXT,                                -- 'mineru' or 'docling' (filled after routing)
  status                TEXT NOT NULL,                       -- queued/parsing/postproc/succeeded/failed/cancelled
  result_uri            TEXT,                                -- MinIO URI of parsed output
  error_code            TEXT,
  error_msg             TEXT,
  priority              SMALLINT DEFAULT 5,
  submit_by             TEXT NOT NULL,                       -- userId from IAM JWT
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at            TIMESTAMPTZ,
  finished_at           TIMESTAMPTZ
);
CREATE INDEX idx_jobs_status_created ON jobs (status, created_at);
CREATE INDEX idx_jobs_business_ref ON jobs (tenant_scene, business_ref);

-- Append-only audit log
CREATE TABLE audit_events (
  id            BIGSERIAL PRIMARY KEY,
  job_id        UUID NOT NULL REFERENCES jobs(id),
  event_type    TEXT NOT NULL,
  actor         TEXT NOT NULL,                              -- userId or 'system:worker-mineru@pod-xxx'
  payload       JSONB,                                      -- structured context (model version, duration, hits)
  trace_id      TEXT,                                       -- OpenTelemetry trace
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_job ON audit_events (job_id, created_at);
CREATE INDEX idx_audit_trace ON audit_events (trace_id);

-- Model registry
CREATE TABLE model_registry (
  id            UUID PRIMARY KEY,
  name          TEXT NOT NULL,
  version       TEXT NOT NULL,
  image_digest  TEXT NOT NULL,                              -- sha256:... of the container
  license       TEXT NOT NULL,
  approved_by   TEXT,
  approved_at   TIMESTAMPTZ,
  status        TEXT NOT NULL,                              -- staging/production/retired
  notes         TEXT,
  UNIQUE (name, version)
);

-- Webhook subscriptions (push delivery)
CREATE TABLE webhook_subscriptions (
  id            UUID PRIMARY KEY,
  tenant_scene  TEXT NOT NULL,
  callback_url  TEXT NOT NULL,
  secret_id     TEXT NOT NULL,                              -- reference to secrets manager
  event_filter  JSONB NOT NULL,                             -- {"status": ["succeeded","failed"]}
  active        BOOLEAN NOT NULL DEFAULT true,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.2 MinIO layout

```
/raw/{tenant_scene}/{yyyy}/{mm}/{dd}/{jobId}.{ext}          ← original document (90d retention)
/parsed/{tenant_scene}/{yyyy}/{mm}/{dd}/{jobId}/result.md   ← parsed markdown  (30d retention)
/parsed/{tenant_scene}/{yyyy}/{mm}/{dd}/{jobId}/result.json ← structured JSON  (30d retention)
/parsed/{tenant_scene}/{yyyy}/{mm}/{dd}/{jobId}/chunks.json ← chunking output  (7d retention)
```

Audit records in Postgres are retained permanently (or per your compliance policy).

---

## 4. API contract (frozen v1)

```yaml
POST /v1/jobs
  headers:
    Authorization: Bearer <IAM JWT>
    X-Tenant-Scene: default | credit | compliance | ...
    X-Idempotency-Key: <client-side UUID>
  body:
    business_ref: string                              # required
    source:
      type: "presigned_url" | "direct_upload" | "inner_oss_ref"
      url_or_ref: string
    priority: 1-9                                      # optional, default 5
    callback:                                          # optional (push delivery)
      url: string
      event_filter: {status: ["succeeded","failed"]}
  response 202:
    { jobId: uuid, status: "queued", createdAt: iso8601 }
  response 409:
    { error: "duplicate_idempotency_key", existingJobId: uuid }

GET /v1/jobs/{jobId}
  response 200:
    {
      jobId, status, progress?: 0-100,
      resultUrls?: { md, json, chunks },              # pre-signed, 5-min expiry
      error?
    }

POST /v1/jobs/{jobId}/cancel
  response 200: { cancelled: true }
  response 409: { error: "already_terminal" }

POST /v1/webhooks
  body: { tenantScene, callbackUrl, eventFilter, secretId }
  response 201: { subscriptionId }
```

### 4.1 Idempotency

Two requests with the same `X-Idempotency-Key` will return the same jobId. The second request does not cause a new job to be created or charged. This prevents duplicate processing from client retries.

### 4.2 Source types

- **`presigned_url`** — client provides a time-limited URL to download the document
- **`direct_upload`** — client uploads via multipart (for small documents < 100MB)
- **`inner_oss_ref`** — client passes a reference to an object in your internal MinIO/S3 (recommended in enterprise contexts where the document is already in your object store)

### 4.3 Webhook signature

Push callbacks include a header:
```
X-DPH-Signature: sha256=<hex>
```
computed as `HMAC-SHA256(secret, timestamp + "." + body)`. Receivers should verify this before trusting the payload.

---

## 5. Failure modes

| Scenario | Tested? | Handling | User-visible |
|---|---|---|---|
| MinerU model load fails (OOM) | yes | fallback to docling, mark `degraded=true` | job succeeds, metadata shows degraded |
| Document is blank / empty scan | yes | `status=failed, error_code=empty_content` | "document has no parseable content" |
| Document > 500MB | yes | gateway 413 reject | "document exceeds size limit" |
| Cross-page table parse fails | yes | partial result + warnings field | result returned with warnings |
| PII redaction hits legitimate field | yes | per-scene whitelist rules | whitelist acceptance rate > 99% |
| RabbitMQ flap / worker disconnect | yes | Celery ack-late + 3 retries + DLQ | jobId retries successfully or DLQ |
| Webhook 5xx | yes | exponential backoff 5 attempts, then DLQ + alert | subscriber sees repeated calls |
| Worker pod OOM mid-parse | yes | job requeued, picked up by another worker | no data loss, slight delay |
| IAM unreachable | yes | 15-min public key cache, short-term offline verify | unaffected for 15 minutes |
| MinIO single-node outage | partial | single-DC MVP accepts SLA 99.0%; multi-DC is post-MVP | downtime during outage |

Whitelist rules for PII are critical and must be authored per-scene by your compliance team. The default ships with sensible rules for IDs, credit cards, phone numbers, and emails, but these are starting points, not compliance guarantees.

---

## 6. Observability

- **Tracing** — OTel SDK instruments FastAPI and Celery. Every `audit_events.trace_id` matches the trace that produced it. Any jobId can be replayed by querying `audit_events WHERE job_id = ? ORDER BY created_at`.
- **Metrics** — Prometheus scrape endpoint on every service. Key SLIs:
  - `job_duration_seconds{scene,engine}` (histogram)
  - `job_failure_rate{error_code}`
  - `queue_depth{queue}`
- **Logs** — structured JSON to stdout, shipped via your log aggregator

---

## 7. Supply chain

CI pipeline (see `.github/workflows/`):

```
lint → unit-test → integration-test (docker-compose) → build-image
                                                          ├── syft (SBOM, spdx-json)
                                                          ├── trivy (HIGH/CRITICAL gate)
                                                          └── cosign (sign image)
push to GHCR
```

Consumers should verify the Cosign signature before running production images.

---

## 8. Design principles (why things are the way they are)

1. **Two engines, because no single engine dominates.** MinerU wins on Chinese financial documents with scanned tables and formulas. docling wins on Office files, HTML, and governance features. Routing between them is cheaper than rewriting either.
2. **Async by default, sync by exception.** Most documents take 1-5 minutes. Forcing them into synchronous requests leads to timeout retries, retry storms, and false failures. The API is fundamentally async; the client picks pull or push.
3. **Classification on the way in, not the way through.** Data classification labels come from the client (or your data gateway), not from the processor. The processor is a stateless compute service. Changing classification rules should not require redeploying the processor.
4. **Audit as a first-class event stream, not a logging afterthought.** Every state transition is a row. This makes compliance auditing a `SELECT` query, not a log-grep adventure.
5. **Reuse enterprise infrastructure.** API gateway (APISIX), IAM (your OIDC), observability (your Prometheus + log aggregator), secrets (your KMS), container registry (your Harbor). Do not build your own.

---

## 9. What's explicitly out of scope

- Cross-datacenter replication (post-MVP)
- Multi-tenant isolation beyond logical `tenant_scene`
- Model canary + auto-rollback (post-MVP; manual for now)
- Deep chart understanding (chart-to-data)
- Formula rendering beyond MinerU's LaTeX output
- Languages other than Chinese and English (community contributions welcome)
- Streaming parse output (chunked SSE)
- Mobile UI for the operator console

---

## 10. References

- MinerU: https://github.com/opendatalab/MinerU
- docling: https://github.com/DS4SD/docling
- Presidio: https://github.com/microsoft/presidio
- Celery: https://docs.celeryproject.org
- FastAPI: https://fastapi.tiangolo.com
- Ant Design Pro: https://pro.ant.design
