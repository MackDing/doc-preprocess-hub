# Security & compliance posture

This document is what a security-focused reviewer will want to see. It is not a substitute for a real security review in your own environment.

---

## Threat model

In scope:
- Ingress to the orchestrator API
- Data at rest in Postgres, MinIO, Redis
- Data in transit between services
- Supply chain integrity of container images
- PII exposure in parsed outputs

Out of scope for this repo (your org handles):
- Host / OS hardening
- Network perimeter (VPN, firewall)
- Physical security
- Endpoint security of operators using the console

---

## Authentication

- **Public API** (POST /v1/jobs, etc.): OIDC bearer tokens verified by the gateway (APISIX) before requests reach orchestrator-api. In dev, `AUTH_MODE=trust-all` bypasses this — never use in prod.
- **Service-to-service**: mTLS or short-lived tokens via your service mesh / internal PKI. Not enforced by default in this scaffold — add to the deployment config.
- **Celery broker**: RabbitMQ with username/password (rotate regularly). Prefer TLS for broker traffic in production.

---

## Authorization

The API currently accepts any valid JWT and does not enforce per-scene RBAC. Production deployments should:

- Add an authorization layer (Open Policy Agent, Casbin, or custom) that checks the `tenant_scene` header against the JWT's claims.
- Require explicit grant for each scene a user can submit to.
- Deny access to other users' jobs in GET /v1/jobs/{id} — enforce ownership via `submit_by`.

This is a **TODO for v0.3** in the roadmap.

---

## Data classification

Every job carries a `data_classification` label (public / internal / confidential / restricted). The label is the client's responsibility — the orchestrator is stateless with respect to classification rules.

Workers should route by classification when multiple deployment zones exist (e.g. `restricted` goes to a physically isolated cluster). This is a deployment-time concern, not baked in.

---

## Data at rest

- **Postgres**: enable TDE (Transparent Data Encryption) or disk-level encryption (LUKS, cloud-native KMS).
- **MinIO**: server-side encryption with KMS (SSE-KMS) for all buckets.
- **Redis**: avoid storing sensitive data. It's a cache and Celery result backend — keep TTLs short.
- **Raw document retention**: 90 days default. Configurable via MinIO lifecycle policy.
- **Audit retention**: permanent by default. Export to cold storage periodically.

---

## Data in transit

- All HTTPS between client → gateway, gateway → orchestrator.
- Internal mesh: enable TLS between Postgres / RabbitMQ / Redis / MinIO and their clients.
- Webhook deliveries: HTTPS only, with HMAC-SHA256 signatures.

---

## PII handling

- All parsed outputs go through worker-postproc before reaching result storage.
- Default recognizers: CREDIT_CARD, US_SSN, PHONE_NUMBER, EMAIL_ADDRESS, IP_ADDRESS.
- Chinese recognizers (CN_MOBILE, CN_ID_CARD, CN_BANK_CARD) require custom code — contributions welcome.
- Per-scene whitelist prevents redaction of legitimate business fields. This is the highest-leverage policy knob.
- All PII hits are logged to `audit_events` (what matched, not the value itself).

**Red line**: never log the matched PII value. Only log the entity type, position offsets, and confidence. The audit trail must not itself become a PII leak.

---

## Supply chain

CI produces:
- Container images signed with Cosign (keyless / OIDC, or KMS-backed)
- SPDX SBOMs via Syft, attached to each image
- Trivy vulnerability scans with HIGH/CRITICAL gating

In production, verify the Cosign signature before running an image:

```bash
cosign verify ghcr.io/mackding/doc-preprocess-hub-orchestrator:v0.1.0 \
  --certificate-identity-regexp "https://github.com/MackDing/doc-preprocess-hub" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

Consider a Kubernetes admission controller (Kyverno, Gatekeeper, sigstore-policy-controller) that enforces signature verification at deploy time.

---

## Audit

Every state transition is an `audit_events` row with:
- `job_id` — which document
- `event_type` — what happened
- `actor` — who or what caused it
- `payload` — structured context (model version, duration, PII entity types hit)
- `trace_id` — link to OpenTelemetry trace

Typical audit queries:

```sql
-- All events for a job
SELECT * FROM audit_events WHERE job_id = '...' ORDER BY created_at;

-- All PII hits in the last 24 hours, grouped by entity type
SELECT payload->>'entity_type' AS entity, COUNT(*)
FROM audit_events
WHERE event_type = 'pii_hit' AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY entity;

-- All exports by a user in the last 7 days (compliance audit trail)
SELECT * FROM audit_events
WHERE event_type = 'audit_exported' AND actor = 'alice' AND created_at > NOW() - INTERVAL '7 days';
```

---

## Known limitations

- No row-level security in Postgres by default. If multiple orgs share a deployment, add RLS.
- The console currently has no 2FA requirement. Enforce at the IAM layer.
- No rate limiting in the scaffold. APISIX has `limit-req` and `limit-count` — use them.
- No automated pen-test suite in CI. Manual pen test recommended before first production traffic.

---

## Reporting vulnerabilities

See [CONTRIBUTING.md#reporting-security-issues](../CONTRIBUTING.md#reporting-security-issues).
