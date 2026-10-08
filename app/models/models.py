"""SQLAlchemy ORM models."""
from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, DateTime, func, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    total_recipients: Mapped[int] = mapped_column(default=0, nullable=False)
    successful: Mapped[int] = mapped_column(default=0, nullable=False)
    failed: Mapped[int] = mapped_column(default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_style: Mapped[str] = mapped_column(String(32), default="modern")
    event_name: Mapped[str] = mapped_column(String(255), default="")
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
    result_zip_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    recipients: Mapped[list["Recipient"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_jobs_status", "status"),
    )


class Recipient(Base, TimestampMixin):
    __tablename__ = "recipients"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    certificate_id: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certificate_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    job: Mapped["Job"] = relationship(back_populates="recipients")

    __table_args__ = (
        Index("idx_recipients_job_id", "job_id"),
    )