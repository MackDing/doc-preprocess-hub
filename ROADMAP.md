# Roadmap

Living document. Subject to change based on contributor interest and real-world usage.

---

## v0.1 (alpha) — Scaffolding complete

- [x] Project layout, docker-compose dev environment
- [x] Architecture, API contract, data model frozen
- [x] Postgres schema + Alembic migrations
- [x] orchestrator-api: FastAPI app with `POST /v1/jobs` stub
- [x] Worker skeletons for MinerU / docling / postproc
- [x] Python SDK scaffold
- [x] CI with lint + tests
- [x] Apache-2.0 license + NOTICE

## v0.2 — Engines integrated

- [ ] `worker-mineru` wired to actual MinerU (GPU required)
- [ ] `worker-docling` wired to actual docling (CPU)
- [ ] `worker-postproc` wired to actual Presidio + LangChain chunking
- [ ] Per-scene PII whitelist configuration format
- [ ] `docker compose up` → end-to-end happy path: submit PDF → poll → get Markdown
- [ ] Parsing benchmark harness with 20+ document corpus

## v0.3 — Production readiness

- [ ] APISIX gateway configuration samples
- [ ] OIDC / JWT middleware
- [ ] OpenTelemetry full instrumentation
- [ ] Prometheus metrics + example Grafana dashboards
- [ ] Helm chart for Kubernetes deployment
- [ ] SBOM + Trivy + Cosign in CI, publishing to GHCR
- [ ] Webhook push delivery (`webhook-sender` service)

## v0.4 — Operator console

- [ ] Ant Design Pro v6 skeleton
- [ ] Jobs list + Drawer detail view
- [ ] DLQ management with replay / discard
- [ ] SLA dashboard (Grafana iframe)
- [ ] Audit query with CSV export
- [ ] Chinese / English i18n

## v0.5 — Governance

- [ ] Model registry service (`governance-svc`)
- [ ] License tracking per model version
- [ ] Manual canary deployment UI
- [ ] Audit export endpoint for compliance

## v1.0 — First stable

Criteria:

- All v0.1 – v0.5 items done
- At least one production deployment reported
- Parsing accuracy ≥ 90% on public benchmarks (contributed)
- SLA: P95 parse latency < 5min on reference hardware
- PII recall ≥ 99% on public test set

---

## Beyond v1.0 (ideas, not commitments)

- Multi-datacenter replication
- Chart / formula understanding (DePlot integration)
- Streaming parse output (SSE)
- Mobile-friendly console
- Additional language SDKs (Java, Go, TypeScript)
- Alternative routing strategies (ML-based engine selection)
- Plugin system for custom post-processors

---

## How to influence the roadmap

Open an issue with the `roadmap` label. Explain:

- What problem you're solving
- Why it matters beyond your use case
- What a minimal viable version looks like
- Whether you're willing to contribute the code

Good proposals move up. Quiet proposals sit.
