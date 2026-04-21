# Deployment

This document covers production deployment. For local dev, see the root README.

---

## Target environments

doc-preprocess-hub is designed for deployment in:

- A single Kubernetes cluster (reference target)
- Docker Compose on a single beefy host (small deployments)
- Docker Swarm (legacy, works but not recommended for new deployments)

It assumes you already have:

- An API gateway (APISIX is the reference; Kong / Envoy / Nginx Plus work)
- An IAM / SSO provider (any OIDC-compatible: Keycloak, Okta, Azure AD, Authing)
- An observability stack (Prometheus + Grafana + a log aggregator)
- A container registry (Harbor, GHCR, ECR, etc.)
- A secrets manager (Vault, AWS Secrets Manager, K8s Sealed Secrets)

You do NOT need to ship any of these with doc-preprocess-hub.

---

## Sizing guide

For 1,000 docs/day mixed load (P95 < 5min):

| Service           | Replicas | Per-replica |
|-------------------|---------:|-------------|
| orchestrator-api  | 3        | 1 vCPU / 512 MB |
| worker-mineru     | 2        | 8 vCPU / 32 GB / 1 × A10 or better |
| worker-docling    | 4        | 4 vCPU / 8 GB |
| worker-postproc   | 3        | 2 vCPU / 4 GB |
| webhook-sender    | 2        | 1 vCPU / 512 MB |
| console-api       | 2        | 1 vCPU / 512 MB |
| console-ui        | 2        | 1 vCPU / 256 MB |
| PostgreSQL        | 1 primary + 1 replica | 4 vCPU / 16 GB / 500 GB SSD |
| RabbitMQ          | 3-node cluster | 2 vCPU / 4 GB each |
| Redis             | 1 primary + 1 replica | 2 vCPU / 4 GB |
| MinIO             | 4 nodes EC:2+2 | 4 vCPU / 16 GB / 2 TB each |

Scale MinerU replicas by expected scan volume — it's the biggest cost center.

---

## Model weights

MinerU models are bulky (~5-10 GB). Two options:

### Option A: bake into the image

```dockerfile
RUN python -c "from magic_pdf.libs.config_reader import get_local_models_dir; ..."
# model download step here
```

Pro: simpler deploy, no dependency at runtime.
Con: image is ~10 GB, image pull is slow on first pod start.

### Option B: shared PVC / NFS mount

Mount a read-only volume at `/models`. Point the MinerU config at it.

Pro: slim image (~500 MB), fast cold start.
Con: requires shared storage with high IOPS.

For the first production deployment, pick Option A. Revisit once you care about startup latency.

---

## APISIX configuration

Example route:

```yaml
# apisix-route.yaml
uri: /v1/*
upstream:
  type: roundrobin
  nodes:
    "orchestrator-api:8000": 1
plugins:
  openid-connect:
    discovery: "https://your-iam/.well-known/openid-configuration"
    client_id: doc-preprocess-hub
    client_secret: $ENV://DPH_OIDC_CLIENT_SECRET
    bearer_only: true
    realm: doc-preprocess-hub
  limit-req:
    rate: 100
    burst: 50
    key: consumer_name
```

---

## OpenTelemetry

Set these environment variables on every service:

```
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-otel-collector:4317
OTEL_SERVICE_NAME=orchestrator-api   # per service
OTEL_RESOURCE_ATTRIBUTES=deployment.environment=prod
```

Traces link request spans to Celery task spans via W3C trace context propagation. Every `audit_events.trace_id` is a valid trace you can open in Jaeger / Tempo.

---

## Secrets

The app expects these secrets to be provided via env or mounted files:

| Secret | Consumer | Where |
|--------|----------|-------|
| `POSTGRES_PASSWORD` | orchestrator, governance-svc | DB connection |
| `RABBITMQ_PASSWORD` | all workers + orchestrator | broker auth |
| `REDIS_PASSWORD` | all workers + orchestrator | if Redis auth enabled |
| `MINIO_SECRET_KEY` | all workers + orchestrator | object storage |
| `OIDC_CLIENT_SECRET` | gateway | IAM |
| `WEBHOOK_SIGNING_SECRETS` | webhook-sender | per-subscription HMAC |

Never bake these into images.

---

## Backup and restore

**Postgres**: logical dumps nightly + continuous WAL to object storage. Restore-time SLO: < 30 min.
**MinIO**: bucket replication to a secondary site. Raw documents: 90 day retention. Parsed results: 30 days.
**RabbitMQ**: queue definitions in IaC (no persistent data to back up — tasks are transient).
**Audit events**: never deleted. Export to cold storage (e.g. monthly parquet to S3) after 90 days.

---

## Upgrade procedure

1. Deploy new image to canary (1 replica per service).
2. Route 10% traffic via APISIX canary rule.
3. Monitor error_rate, p95 latency, and queue depth for 15 min.
4. If green, roll forward. If red, revert image tag.

Database migrations: always backward-compatible within a major version. Multi-step migrations for breaking changes (e.g. `add column nullable` → `backfill` → `flip to non-null`).

---

## Kubernetes

A Helm chart is planned (see ROADMAP.md, v0.3). Until then, use Kustomize or roll your own manifests based on the docker-compose.yml as reference.
