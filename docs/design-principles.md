# Design principles

Why the system is the way it is. If you're about to propose a change that contradicts one of these, open an RFC issue first.

---

## 1. Boring by default

The shell is built on proven infrastructure: Postgres, RabbitMQ, Redis, Celery, FastAPI, AntD Pro. Your team already knows these. Your vendor has docs for these. Your on-call rotation can debug these at 3am.

Innovation tokens are spent on the problem (document preprocessing at enterprise scale with compliance constraints), not on the plumbing.

**What this means in practice**: if you're about to introduce a new datastore, message broker, or language runtime, please explain why. Usually the answer is "we don't need to."

---

## 2. Composable over monolithic

MinerU and docling are swappable. If docling ships an improvement that makes MinerU unnecessary for your use case, you can drop MinerU without rewriting the orchestrator, the console, or the API contract.

Same for Presidio (swap for another PII engine), APISIX (swap for Kong), RabbitMQ (swap for Redis Streams in smaller deployments).

**What this means in practice**: don't add direct dependencies from the orchestrator to the engines' internal types. Talk through Celery task messages. Talk through MinIO. Keep the seams.

---

## 3. Async by default, sync by exception

Most documents take 1-5 minutes to parse. Forcing them into synchronous API calls leads to:
- Client timeout retries
- Retry storms during incidents
- False "failed" reports when the job actually succeeded

The v1 API is fundamentally async. Submit returns 202. The client picks Pull (poll GET) or Push (webhook).

**What this means in practice**: no endpoint does "submit and block until done." Even if the parse would have finished in 5 seconds, we do not block.

---

## 4. Classification is a label, not a code path

Data classification (public / internal / confidential / restricted) comes from your data gateway or the client. The orchestrator treats it as a tag and routes to the right deployment zone.

The alternative — classification rules baked into the orchestrator — means every rule change is a code change. That's backwards.

**What this means in practice**: `X-Data-Classification` is a header. The orchestrator validates it's one of the known values and records it. Everything else is deployment config.

---

## 5. Audit is a first-class event stream

Every state transition is an `audit_events` row. Every PII hit. Every model load. Every cancel. Every export.

This makes compliance auditing a `SELECT` query, not a log-grep adventure.

**What this means in practice**: when you add a new operation, add a new `audit_events` row for it. If you can't describe the operation in one `event_type` + `payload`, you're probably doing too much in one operation.

---

## 6. Idempotency is not optional

Clients will retry. Networks will flap. Workers will restart mid-task. Every submission point (`POST /v1/jobs`, webhook delivery, Celery task) must be idempotent, or we lose data.

**What this means in practice**: `X-Idempotency-Key` is required in production. Celery tasks use `acks_late` + `reject_on_worker_lost`. Webhook receivers should deduplicate on `jobId` + `event_type`.

---

## 7. Defaults are features

Empty states. Error messages. Retry behavior. Pagination. These are not afterthoughts. Every default the code ships with is a user experience.

**What this means in practice**: when in doubt, ask "what does this look like at 3am when everything is going wrong?" If the answer is "a blank page" or "a stack trace," go back and finish the feature.

---

## 8. No vendor lock-in we can avoid

We use open-source engines (MinerU, docling), open standards (S3, OIDC, Prometheus, OpenTelemetry), and self-hostable infrastructure (Postgres, RabbitMQ, MinIO). You can run this air-gapped on your own hardware.

**What this means in practice**: hard no on hosted-only SaaS dependencies for core paths. Integrations with hosted SaaS are fine as optional extensions.
