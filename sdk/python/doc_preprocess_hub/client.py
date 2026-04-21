"""Thin Python client for the orchestrator API.

Example::

    from doc_preprocess_hub import Client

    client = Client(base_url="https://dph.example.com", token="…")
    job = client.submit(
        business_ref="DD-2026-001",
        source_url="s3://my-bucket/docs/report.pdf",
        tenant_scene="credit",
        idempotency_key="unique-client-uuid",
    )
    print(job.job_id, job.status)

    result = client.wait(job.job_id, timeout=300)
    print(result.result_urls.md)
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

import httpx


class DphError(RuntimeError):
    """Base exception for SDK errors."""


class TimeoutError(DphError):
    """wait() exceeded the timeout."""


@dataclass
class Job:
    job_id: str
    status: str
    created_at: str


@dataclass
class ResultUrls:
    md: str | None = None
    json_: str | None = None
    chunks: str | None = None


@dataclass
class JobStatus:
    job_id: str
    status: str
    progress: int | None = None
    result_urls: ResultUrls | None = None
    error_code: str | None = None
    error_msg: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


TERMINAL_STATUSES = {"succeeded", "failed", "cancelled"}


class Client:
    """Synchronous client. For async, wrap with httpx.AsyncClient."""

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._http = httpx.Client(base_url=self._base_url, headers=headers, timeout=timeout)

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_: Any) -> None:
        self._http.close()

    # --- Jobs ----------------------------------------------------------

    def submit(
        self,
        *,
        business_ref: str,
        source_url: str,
        source_type: str = "presigned_url",
        tenant_scene: str = "default",
        data_classification: str = "internal",
        priority: int = 5,
        idempotency_key: str | None = None,
        callback_url: str | None = None,
    ) -> Job:
        """Submit a document for processing.

        `source_type` is one of `presigned_url`, `direct_upload`, `inner_oss_ref`.
        """
        body: dict[str, Any] = {
            "business_ref": business_ref,
            "source": {"type": source_type, "url_or_ref": source_url},
            "priority": priority,
        }
        if callback_url:
            body["callback"] = {"url": callback_url}

        headers = {
            "X-Tenant-Scene": tenant_scene,
            "X-Data-Classification": data_classification,
            "X-Idempotency-Key": idempotency_key or str(uuid.uuid4()),
        }
        r = self._http.post("/v1/jobs", json=body, headers=headers)
        r.raise_for_status()
        data = r.json()
        return Job(job_id=data["jobId"], status=data["status"], created_at=data["createdAt"])

    def get(self, job_id: str) -> JobStatus:
        r = self._http.get(f"/v1/jobs/{job_id}")
        r.raise_for_status()
        d = r.json()
        urls = None
        if d.get("resultUrls"):
            ru = d["resultUrls"]
            urls = ResultUrls(md=ru.get("md"), json_=ru.get("json"), chunks=ru.get("chunks"))
        return JobStatus(
            job_id=d["jobId"],
            status=d["status"],
            progress=d.get("progress"),
            result_urls=urls,
            error_code=d.get("errorCode"),
            error_msg=d.get("errorMsg"),
            created_at=d.get("createdAt"),
            started_at=d.get("startedAt"),
            finished_at=d.get("finishedAt"),
        )

    def cancel(self, job_id: str) -> bool:
        r = self._http.post(f"/v1/jobs/{job_id}/cancel")
        if r.status_code == 409:
            return False
        r.raise_for_status()
        return bool(r.json().get("cancelled"))

    def wait(
        self,
        job_id: str,
        *,
        timeout: float = 300.0,
        poll_interval: float = 3.0,
    ) -> JobStatus:
        """Poll until the job reaches a terminal state or timeout."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self.get(job_id)
            if status.status in TERMINAL_STATUSES:
                return status
            time.sleep(poll_interval)
        raise TimeoutError(f"job {job_id} did not finish within {timeout}s")
