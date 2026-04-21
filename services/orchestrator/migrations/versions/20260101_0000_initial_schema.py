"""initial schema

Revision ID: 20260101_0000
Revises:
Create Date: 2026-01-01 00:00:00

Mirrors schema/001_init.sql. Run with:
  alembic upgrade head
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260101_0000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_scene", sa.String(), nullable=False),
        sa.Column("business_ref", sa.String(), nullable=False),
        sa.Column("data_classification", sa.String(), nullable=False, server_default="internal"),
        sa.Column("source_uri", sa.String(), nullable=False),
        sa.Column("doc_type", sa.String(), nullable=False),
        sa.Column("engine", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="queued"),
        sa.Column("result_uri", sa.String(), nullable=True),
        sa.Column("error_code", sa.String(), nullable=True),
        sa.Column("error_msg", sa.String(), nullable=True),
        sa.Column("priority", sa.SmallInteger(), nullable=False, server_default="5"),
        sa.Column("submit_by", sa.String(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_jobs_status_created", "jobs", ["status", "created_at"])
    op.create_index("idx_jobs_business_ref", "jobs", ["tenant_scene", "business_ref"])
    op.create_index(
        "idx_jobs_idempotency",
        "jobs",
        ["tenant_scene", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("trace_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_audit_job", "audit_events", ["job_id", "created_at"])
    op.create_index("idx_audit_trace", "audit_events", ["trace_id"])
    op.create_index("idx_audit_event_type", "audit_events", ["event_type"])

    op.create_table(
        "model_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("image_digest", sa.String(), nullable=False),
        sa.Column("license", sa.String(), nullable=False),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="staging"),
        sa.Column("notes", sa.String(), nullable=True),
        sa.UniqueConstraint("name", "version", name="uq_model_name_version"),
    )

    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_scene", sa.String(), nullable=False),
        sa.Column("callback_url", sa.String(), nullable=False),
        sa.Column("secret_id", sa.String(), nullable=False),
        sa.Column("event_filter", postgresql.JSONB(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "idx_webhook_scene_active", "webhook_subscriptions", ["tenant_scene", "active"]
    )


def downgrade() -> None:
    op.drop_index("idx_webhook_scene_active", table_name="webhook_subscriptions")
    op.drop_table("webhook_subscriptions")
    op.drop_table("model_registry")
    op.drop_index("idx_audit_event_type", table_name="audit_events")
    op.drop_index("idx_audit_trace", table_name="audit_events")
    op.drop_index("idx_audit_job", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("idx_jobs_idempotency", table_name="jobs")
    op.drop_index("idx_jobs_business_ref", table_name="jobs")
    op.drop_index("idx_jobs_status_created", table_name="jobs")
    op.drop_table("jobs")
