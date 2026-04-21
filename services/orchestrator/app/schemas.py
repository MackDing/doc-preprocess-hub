"""Pydantic request/response schemas (API surface).

This is the v1 public API contract. Changes here are BREAKING — bump to v2
and keep v1 responding for compatibility.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class SourceSpec(BaseModel):
    type: Literal["presigned_url", "direct_upload", "inner_oss_ref"]
    url_or_ref: str


class CallbackSpec(BaseModel):
    url: HttpUrl
    event_filter: dict = Field(
        default_factory=lambda: {"status": ["succeeded", "failed"]}
    )


class CreateJobRequest(BaseModel):
    business_ref: str = Field(..., min_length=1, max_length=256)
    source: SourceSpec
    priority: int = Field(default=5, ge=1, le=9)
    callback: CallbackSpec | None = None


class CreateJobResponse(BaseModel):
    jobId: uuid.UUID
    status: str
    createdAt: datetime


class ResultUrls(BaseModel):
    md: str | None = None
    json_: str | None = Field(default=None, alias="json")
    chunks: str | None = None

    model_config = {"populate_by_name": True}


class JobStatusResponse(BaseModel):
    jobId: uuid.UUID
    status: str
    progress: int | None = None
    resultUrls: ResultUrls | None = None
    errorCode: str | None = None
    errorMsg: str | None = None
    createdAt: datetime
    startedAt: datetime | None = None
    finishedAt: datetime | None = None


class CancelJobResponse(BaseModel):
    cancelled: bool


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    existingJobId: uuid.UUID | None = None


class CreateWebhookRequest(BaseModel):
    tenantScene: str
    callbackUrl: HttpUrl
    eventFilter: dict = Field(default_factory=lambda: {"status": ["succeeded", "failed"]})
    secretId: str


class CreateWebhookResponse(BaseModel):
    subscriptionId: uuid.UUID
