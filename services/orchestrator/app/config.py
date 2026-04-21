"""Configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://dph:dph_dev_password@localhost:5432/dph"

    # Celery
    celery_broker_url: str = "amqp://dph:dph_dev_password@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/0"

    # MinIO / S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "dph"
    minio_secret_key: str = "dph_dev_password"
    minio_secure: bool = False
    minio_bucket_raw: str = "dph-raw"
    minio_bucket_parsed: str = "dph-parsed"

    # Auth
    auth_mode: str = "trust-all"  # "trust-all" | "oidc"
    oidc_issuer_url: str | None = None
    oidc_audience: str | None = None

    # Observability
    otel_exporter_otlp_endpoint: str | None = None
    otel_service_name: str = "orchestrator-api"
    log_level: str = "INFO"

    # Business rules
    max_document_bytes: int = 500 * 1024 * 1024  # 500 MB
    presigned_url_ttl_seconds: int = 300


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
