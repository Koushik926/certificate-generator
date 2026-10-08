from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.recipient import RecipientCreate, RecipientResult


class JobCreate(BaseModel):
    """Request payload for creating a new certificate generation job."""

    event_name: str = Field(..., min_length=1, max_length=255)
    issue_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    recipients: list[RecipientCreate] = Field(..., min_length=1, max_length=5000)
    template_style: str = Field(default="modern", pattern=r"^(modern|classic)$")
    idempotency_key: str | None = Field(default=None, max_length=128)

    @field_validator("issue_date")
    @classmethod
    def parse_issue_date(cls, v: str) -> str:
        # Keep raw string; services parse it if needed.
        return v


class JobResponse(BaseModel):
    """Read model returned when a job is created."""

    job_id: UUID
    status: str
    total_recipients: int
    created_at: datetime
    idempotency_key: str | None = None


class JobStatusResponse(BaseModel):
    """Detailed job status with per-recipient breakdown."""

    job_id: UUID
    status: str
    total_recipients: int
    successful: int
    failed: int
    error_message: str | None = None
    template_style: str
    event_name: str
    created_at: datetime
    result_zip_path: str | None = None
    recipients: list[RecipientResult] = []


class JobListResponse(BaseModel):
    """Paginated list of jobs."""

    jobs: list[JobResponse]
    page: int
    size: int
    total: int