-- doc-preprocess-hub — initial schema
-- Consumed by docker-compose on first Postgres boot.
-- For production, use Alembic migrations in services/orchestrator/migrations/.

SET TIME ZONE 'UTC';

-- Jobs: one row per document submission
CREATE TABLE IF NOT EXISTS jobs (
  id                    UUID PRIMARY KEY,
  tenant_scene          TEXT NOT NULL,
  business_ref          TEXT NOT NULL,
  data_classification   TEXT NOT NULL DEFAULT 'internal',
  source_uri            TEXT NOT NULL,
  doc_type              TEXT NOT NULL,
  engine                TEXT,
  status                TEXT NOT NULL DEFAULT 'queued',
  result_uri            TEXT,
  error_code            TEXT,
  error_msg             TEXT,
  priority              SMALLINT NOT NULL DEFAULT 5,
  submit_by             TEXT NOT NULL,
  idempotency_key       TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at            TIMESTAMPTZ,
  finished_at           TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON jobs (status, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_business_ref ON jobs (tenant_scene, business_ref);
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_idempotency
  ON jobs (tenant_scene, idempotency_key)
  WHERE idempotency_key IS NOT NULL;

-- Audit events: append-only log of state transitions and PII hits
CREATE TABLE IF NOT EXISTS audit_events (
  id            BIGSERIAL PRIMARY KEY,
  job_id        UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  event_type    TEXT NOT NULL,
  actor         TEXT NOT NULL,
  payload       JSONB,
  trace_id      TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_job ON audit_events (job_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_trace ON audit_events (trace_id);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events (event_type);

-- Model registry: versioned, license-tracked
CREATE TABLE IF NOT EXISTS model_registry (
  id            UUID PRIMARY KEY,
  name          TEXT NOT NULL,
  version       TEXT NOT NULL,
  image_digest  TEXT NOT NULL,
  license       TEXT NOT NULL,
  approved_by   TEXT,
  approved_at   TIMESTAMPTZ,
  status        TEXT NOT NULL DEFAULT 'staging',
  notes         TEXT,
  UNIQUE (name, version)
);

-- Webhook subscriptions: push delivery config
CREATE TABLE IF NOT EXISTS webhook_subscriptions (
  id            UUID PRIMARY KEY,
  tenant_scene  TEXT NOT NULL,
  callback_url  TEXT NOT NULL,
  secret_id     TEXT NOT NULL,
  event_filter  JSONB NOT NULL,
  active        BOOLEAN NOT NULL DEFAULT true,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_webhook_scene_active
  ON webhook_subscriptions (tenant_scene, active);
