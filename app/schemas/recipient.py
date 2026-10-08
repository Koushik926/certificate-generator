from __future__ import annotations

from uuid import UUID, uuid4
from pydantic import BaseModel, EmailStr, Field, field_validator


class RecipientCreate(BaseModel):
    """Input for a single recipient in a bulk job."""

    name: str = Field(..., min_length=1, max_length=255, examples=["Alice Johnson"])
    email: str | None = Field(
        default=None,
        max_length=320,
        examples=["alice@example.com"],
    )
    certificate_id: str | None = Field(
        default=None,
        max_length=120,
        examples=["CERT-001"],
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        if v:
            return v.strip().lower()
        return v


class RecipientResult(BaseModel):
    """Per-recipient outcome after generation."""

    recipient_id: UUID
    name: str
    email: str | None
    certificate_id: str | None
    status: str  # success | failed
    error_message: str | None = None
    certificate_path: str | None = None


class RecipientStatus(BaseModel):
    """Aggregate status for a job."""

    total: int
    successful: int
    failed: int
    pending: int