# doc-preprocess-hub

> Enterprise-grade document preprocessing platform. Turn scanned PDFs, Office files, HTML, and emails into clean Markdown + structured JSON, ready for RAG, intelligent review, and knowledge bases.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Status: alpha](https://img.shields.io/badge/status-alpha-orange.svg)]()
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

---

## Why this exists

Every large organization building RAG, intelligent review, or knowledge-base systems hits the same wall: **the documents are a mess**. Scanned PDFs with cross-page tables. Office files with embedded objects. Complex layouts that open-source parsers choke on. PII that compliance will not let you ship without redacting. No single tool solves all of it.

Two excellent engines solve most of it:
- **[MinerU](https://github.com/opendatalab/MinerU)** handles scanned PDFs, complex tables, formulas, and charts. Production-grade for Chinese financial documents.
- **[docling](https://github.com/DS4SD/docling)** handles Office, HTML, email, and native PDFs with solid document governance.

**What's missing is the enterprise shell around them**: routing, async orchestration, PII redaction, audit trails, SBOM, model governance, and a console operators can actually use.

`doc-preprocess-hub` is that shell.

---

## What you get

- **Dual-engine parser** — MinerU for scans & complex PDFs, docling for Office & native PDFs, with a routing layer
- **Async job API** — FastAPI + Celery + RabbitMQ for batch, Redis fallback supported
- **PII redaction pipeline** — [Microsoft Presidio](https://github.com/microsoft/presidio) with configurable whitelists per scenario
- **Chunking** — LangChain text splitters, table-aware
- **Audit trail** — every state transition logged to Postgres, full OpenTelemetry tracing
- **Operator console** — Ant Design Pro 6 based, Chinese/English i18n, jobs list / DLQ / SLA / audit query
- **Supply chain hygiene** — Syft SBOM + Trivy scan + Cosign signing in CI
- **Model registry** — versioning, license tracking, changelog
- **Pull + Push delivery** — downstream systems can poll status or receive webhooks

---

## Architecture

```
                        ┌──────────────────────┐
                        │   Your business apps │
                        │ (credit/compliance/..│
                        └──────────┬───────────┘
                                   │ HTTPS (SDK)
                                   ▼
                        ┌──────────────────────┐
                        │   APISIX gateway     │
                        │ + your enterprise IAM│
                        └──────────┬───────────┘
                                   │
                                   ▼
     ┌───────────────────────────────────────────────────┐
     │         orchestrator-api (FastAPI)                │
     │  POST /v1/jobs  /  GET /v1/jobs/{id}  /  ...      │
     └───────────────────────┬───────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
     [queue.mineru]  [queue.docling]  [queue.postproc]
            │                │                │
            ▼                ▼                ▼
     worker-mineru   worker-docling    worker-postproc
      (GPU)           (CPU)              (Presidio+chunk)
            └────────────────┴────────────────┘
                             │
                             ▼
                ┌────────────────────────┐
                │  Postgres + MinIO      │
                │  + Redis (cache)       │
                └───────────┬────────────┘
                            │
              ┌─────────────┴────────────┐
              ▼                          ▼
         Pull (poll GET)          Push (webhook)
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full technical deep-dive including data model, API contracts, and failure-mode analysis.

---

## Quickstart (dev environment)

```bash
# 1. Clone
git clone https://github.com/MackDing/doc-preprocess-hub.git
cd doc-preprocess-hub

# 2. Copy env template
cp .env.example .env

# 3. Bring up stack
docker compose up -d postgres redis rabbitmq minio
docker compose up orchestrator worker-docling worker-postproc

# 4. Submit a test job (in another shell)
curl -X POST http://localhost:8000/v1/jobs \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: $(uuidgen)" \
  -H "X-Tenant-Scene: default" \
  -d '{
    "business_ref": "TEST-001",
    "source": {
      "type": "presigned_url",
      "url_or_ref": "https://example.com/sample.pdf"
    }
  }'

# 5. Poll status
curl http://localhost:8000/v1/jobs/<job_id>
```

The `worker-mineru` service requires GPU — start it separately once you have a GPU host. See [docs/deployment.md](./docs/deployment.md) for production deployment.

---

## Status

**Alpha.** The architecture is locked, the scaffolding is in place, but the real engine integration is being filled in. Contributions welcome. See [ROADMAP.md](./ROADMAP.md).

### What works today
- [x] Project scaffold + docker-compose dev environment
- [x] Postgres schema + Alembic migrations
- [x] Job submission API contract (FastAPI stubs)
- [x] Celery worker skeletons for MinerU / docling / postproc
- [x] Python SDK scaffold

### In progress
- [ ] Real MinerU integration in `worker-mineru`
- [ ] Real docling integration in `worker-docling`
- [ ] Presidio pipeline with configurable whitelists
- [ ] Ant Design Pro console
- [ ] CI with SBOM + Trivy + Cosign
- [ ] Benchmark harness (parsing / PII / SLA evals)

---

## Philosophy

1. **Boring by default.** The shell uses proven infrastructure (Postgres, RabbitMQ, Redis, Celery, FastAPI). Your team already knows these. Innovation tokens are spent on the problem, not on the plumbing.
2. **Composable over monolithic.** MinerU, docling, Presidio, MinIO, APISIX are all swappable. If docling ships an improvement that makes MinerU unnecessary for your use case, you can drop MinerU without rewriting anything else.
3. **Distribution is part of the product.** The CI publishes versioned container images with SBOM and signatures. Pull from GHCR, sign a policy, run in production.
4. **Audit is not an afterthought.** Every state transition is logged. Every PII hit is recorded. Every model load is attributed. Your compliance team will love you.
5. **Ship the complete thing.** Empty states are features. Error states are features. DLQ replay is a feature. If your operators can't use it at 3am, the system is incomplete.

---

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) — Full architecture, data model, API contracts, failure modes
- [ROADMAP.md](./ROADMAP.md) — What's next
- [CONTRIBUTING.md](./CONTRIBUTING.md) — How to contribute
- [docs/deployment.md](./docs/deployment.md) — Production deployment guide
- [docs/security.md](./docs/security.md) — Security & compliance posture
- [docs/design-principles.md](./docs/design-principles.md) — Design decisions and their rationale

---

## 中文说明

`doc-preprocess-hub` 是一个企业级文档数据预处理平台的参考实现。

**要解决的问题**:大型组织要搞 RAG / 智能审单 / 知识库,输入的文档格式五花八门(扫描件、复杂 PDF、Office、HTML、邮件),质量参差不齐,还要考虑 PII 脱敏、审计、合规、供应链管理等企业级需求。没有一个开源工具把这些事情都做了。

**本项目的定位**:把 MinerU(扫描件/复杂 PDF 强)和 docling(Office/数字文档治理强)两个优秀的解析引擎,包装成一个企业可直接部署的平台。**我们不重造解析引擎**,我们做的是外面的壳 — 任务编排、PII 脱敏、审计链、模型治理、运维控制台。

**架构特点**:

- **双引擎可路由**:按文档类型路由到 MinerU 或 docling
- **异步任务编排**:Celery + RabbitMQ(可降级 Redis)
- **PII 脱敏可配置**:Presidio + 按业务场景白名单(防误杀)
- **全链路审计**:Postgres + OpenTelemetry,每个 jobId 可回放
- **运营 Console**:AntD Pro v6,中英文切换
- **供应链合规**:Syft SBOM + Trivy + Cosign(CI 内置)
- **下游交付**:Pull(轮询)+ Push(webhook)双通道

详见 [ARCHITECTURE.md](./ARCHITECTURE.md)。

---

## License

Apache-2.0. See [LICENSE](./LICENSE) and [NOTICE](./NOTICE) for third-party attributions (MinerU, docling, Presidio, etc. have their own licenses — please review).

---

## Acknowledgments

Built on the shoulders of giants:

- [opendatalab/MinerU](https://github.com/opendatalab/MinerU) — complex document parsing
- [DS4SD/docling](https://github.com/DS4SD/docling) — document conversion and understanding
- [microsoft/presidio](https://github.com/microsoft/presidio) — PII detection and anonymization
- [apache/apisix](https://github.com/apache/apisix) — API gateway
- [langchain-ai/langchain](https://github.com/langchain-ai/langchain) — text splitters
- [anchore/syft](https://github.com/anchore/syft), [aquasecurity/trivy](https://github.com/aquasecurity/trivy), [sigstore/cosign](https://github.com/sigstore/cosign) — supply chain tooling
- [ant-design/ant-design-pro](https://github.com/ant-design/ant-design-pro) — admin console framework
