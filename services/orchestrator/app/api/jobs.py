"""Jobs API: submit, poll, cancel.

This is a scaffold. Real production logic (presigned URL validation,
OIDC auth, rate limiting, OTel spans, MinIO ref resolution) will be filled
in as the project matures. Contracts and error shapes are stable.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..celery_app import send_parse_task
from ..db import get_db
from ..models import AuditEvent, Job
from ..router import queue_for_engine, select_engine
from ..schemas import (
    CancelJobResponse,
    CreateJobRequest,
    CreateJobResponse,
    ErrorResponse,
    JobStatusResponse,
    ResultUrls,
)

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


TERMINAL_STATUSES = {"succeeded", "failed", "cancelled"}


def _current_user(authorization: str | None) -> str:
    """Extract userId from the Authorization header.

    TRUST-ALL mode: accept anything, default to 'anonymous-dev'.
    OIDC mode: verify JWT signature, extract sub.  (TODO)
    """
    if not authorization:
        return "anonymous-dev"
    # TODO(oidc): verify bearer token and extract sub claim
    return "anonymous-dev"


def _infer_doc_type(url_or_ref: str) -> str:
    """Very naive type inference from the file extension."""
    path = urlparse(url_or_ref).path.lower() if "://" in url_or_ref else url_or_ref.lower()
    if path.endswith(".pdf"):
        return "pdf-native"  # caller can override if it's a scan
    if path.endswith(".docx"):
        return "docx"
    if path.endswith(".xlsx"):
        return "xlsx"
    if path.endswith(".pptx"):
        return "pptx"
    if path.endswith((".html", ".htm")):
        return "html"
    if path.endswith((".md", ".markdown")):
        return "md"
    if path.endswith((".eml", ".msg")):
        return "email"
    return "unknown"


@router.post(
    "",
    response_model=CreateJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={409: {"model": ErrorResponse}},
)
def create_job(
    body: CreateJobRequest,
    db: Annotated[Session, Depends(get_db)],
    x_tenant_scene: Annotated[str, Header()] = "default",
    x_idempotency_key: Annotated[str | None, Header()] = None,
    x_data_classification: Annotated[str, Header()] = "internal",
    authorization: Annotated[str | None, Header()] = None,
) -> CreateJobResponse:
    """Submit a document for processing.

    The response is 202 Accepted — the job is queued, not done.
    Poll GET /v1/jobs/{jobId} for status, or configure a webhook.
    """
    actor = _current_user(authorization)
    doc_type = _infer_doc_type(body.source.url_or_ref)
    engine = select_engine(doc_type)

    # Idempotency: return the existing job if the same key was seen.
    if x_idempotency_key:
        existing = db.scalar(
            select(Job).where(
                Job.tenant_scene == x_tenant_scene,
                Job.idempotency_key == x_idempotency_key,
            )
        )
        if existing:
            return CreateJobResponse(
                jobId=existing.id,
                status=existing.status,
                createdAt=existing.created_at,
            )

    job = Job(
        id=uuid.uuid4(),
        tenant_scene=x_tenant_scene,
        business_ref=body.business_ref,
        data_classification=x_data_classification,
        source_uri=body.source.url_or_ref,
        doc_type=doc_type,
        engine=engine,
        status="queued",
        priority=body.priority,
        submit_by=actor,
        idempotency_key=x_idempotency_key,
    )
    db.add(job)

    try:
        db.flush()
    except IntegrityError:
        # Race: another request with the same idempotency key won.
        db.rollback()
        existing = db.scalar(
            select(Job).where(
                Job.tenant_scene == x_tenant_scene,
                Job.idempotency_key == x_idempotency_key,
            )
        )
        if existing:
            return CreateJobResponse(
                jobId=existing.id,
                status=existing.status,
                createdAt=existing.created_at,
            )
        raise HTTPException(status_code=500, detail="idempotency race")

    db.add(
        AuditEvent(
            job_id=job.id,
            event_type="submitted",
            actor=actor,
            payload={"engine": engine, "doc_type": doc_type, "priority": body.priority},
        )
    )
    db.commit()

    # Dispatch to the worker queue.
    send_parse_task(
        queue=queue_for_engine(engine),
        job_id=str(job.id),
        source_uri=job.source_uri,
        doc_type=doc_type,
    )

    return CreateJobResponse(jobId=job.id, status=job.status, createdAt=job.created_at)


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]) -> JobStatusResponse:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    result_urls: ResultUrls | None = None
    if job.result_uri:
        # TODO(minio): sign URLs with short TTL. For now return raw references.
        result_urls = ResultUrls(
            md=f"{job.result_uri}/result.md",
            json=f"{job.result_uri}/result.json",
            chunks=f"{job.result_uri}/chunks.json",
        )

    return JobStatusResponse(
        jobId=job.id,
        status=job.status,
        resultUrls=result_urls,
        errorCode=job.error_code,
        errorMsg=job.error_msg,
        createdAt=job.created_at,
        startedAt=job.started_at,
        finishedAt=job.finished_at,
    )


@router.post(
    "/{job_id}/cancel",
    response_model=CancelJobResponse,
    responses={409: {"model": ErrorResponse}},
)
def cancel_job(
    job_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> CancelJobResponse:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.status in TERMINAL_STATUSES:
        raise HTTPException(
            status_code=409,
            detail={"error": "already_terminal", "status": job.status},
        )

    actor = _current_user(authorization)
    job.status = "cancelled"
    job.finished_at = datetime.now(timezone.utc)
    db.add(
        AuditEvent(
            job_id=job.id,
            event_type="cancelled",
            actor=actor,
        )
    )
    db.commit()
    # TODO(celery): revoke the pending task by id if it hasn't started yet.
    return CancelJobResponse(cancelled=True)
