"""Business logic for certificate generation jobs.

Each service function receives the request-scoped session from
FastAPI dependency injection, which makes the functions trivially
testable — tests can override the ``get_db`` dependency with an
in-memory database.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.models import Job, Recipient
from app.schemas.job import JobCreate, JobListResponse, JobResponse, JobStatusResponse
from app.schemas.recipient import RecipientResult
from app.utils.validation import validate_recipient


async def create_job(payload: JobCreate, db: AsyncSession) -> Job:
    """Create a job and its recipient records. Returns the persisted Job."""
    if len(payload.recipients) > settings.MAX_RECIPIENTS_PER_JOB:
        raise ValueError(f"Max recipients per job is {settings.MAX_RECIPIENTS_PER_JOB}")

    # Idempotency check
    if payload.idempotency_key:
        stmt = select(Job).where(Job.idempotency_key == payload.idempotency_key)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

    job = Job(
        status="pending",
        total_recipients=len(payload.recipients),
        template_style=payload.template_style,
        event_name=payload.event_name,
        idempotency_key=payload.idempotency_key,
    )
    db.add(job)
    await db.flush()

    for r in payload.recipients:
        errs = validate_recipient(r.name, r.email, r.certificate_id)
        db.add(
            Recipient(
                job_id=job.id,
                name=r.name,
                email=r.email,
                certificate_id=r.certificate_id,
                status="failed" if errs else "pending",
                error_message="; ".join(errs) if errs else None,
            )
        )
    await db.commit()
    await db.refresh(job)
    return job


async def get_job_status(job_id: uuid.UUID, db: AsyncSession) -> JobStatusResponse | None:
    """Retrieve full job status with per-recipient breakdown."""
    job = (await db.execute(select(Job).where(Job.id == job_id))).scalar_one_or_none()
    if not job:
        return None

    recipients = (
        await db.execute(select(Recipient).where(Recipient.job_id == job.id))
    ).scalars().all()

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        total_recipients=job.total_recipients,
        successful=job.successful,
        failed=job.failed,
        error_message=job.error_message,
        template_style=job.template_style,
        event_name=job.event_name,
        created_at=job.created_at,
        result_zip_path=job.result_zip_path,
        recipients=[
            RecipientResult(
                recipient_id=r.id,
                name=r.name,
                email=r.email,
                certificate_id=r.certificate_id,
                status=r.status,
                error_message=r.error_message,
                certificate_path=r.certificate_path,
            )
            for r in recipients
        ],
    )


async def list_jobs(page: int, size: int, db: AsyncSession) -> JobListResponse:
    """Paginated list of jobs."""
    size = min(size, settings.MAX_PAGE_SIZE)
    total = (await db.execute(select(func.count()).select_from(Job))).scalar()

    jobs = (
        await db.execute(
            select(Job).order_by(Job.created_at.desc()).offset((page - 1) * size).limit(size)
        )
    ).scalars().all()

    return JobListResponse(
        jobs=[_job_to_response(j) for j in jobs],
        page=page,
        size=size,
        total=total or 0,
    )


async def update_job_progress(job_id: uuid.UUID, db: AsyncSession) -> None:
    """Recalculate job counters from recipient statuses."""
    recipients = (
        await db.execute(select(Recipient).where(Recipient.job_id == job_id))
    ).scalars().all()

    total = len(recipients)
    successful = sum(1 for r in recipients if r.status == "success")
    failed = sum(1 for r in recipients if r.status == "failed")
    pending = total - successful - failed
    status = (
        "completed" if pending == 0 and failed < total
        else "failed" if failed == total and total > 0
        else "processing"
    )

    error_msgs = [r.error_message for r in recipients if r.error_message]
    await db.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(
            status=status,
            successful=successful,
            failed=failed,
            error_message="; ".join(error_msgs) if error_msgs else None,
        )
    )
    await db.commit()


async def set_job_result_path(job_id: uuid.UUID, zip_path: str, db: AsyncSession) -> None:
    """Record the ZIP file path after generation."""
    await db.execute(
        update(Job).where(Job.id == job_id).values(result_zip_path=zip_path)
    )
    await db.commit()


async def download_job_certificates(job_id: uuid.UUID, db: AsyncSession) -> bytes | None:
    """Read and return the ZIP file bytes for a job."""
    status = await get_job_status(job_id, db)
    if not status or not status.result_zip_path:
        return None

    path = Path(status.result_zip_path)
    if not path.exists():
        return None
    return path.read_bytes()


def _job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        job_id=job.id,
        status=job.status,
        total_recipients=job.total_recipients,
        created_at=job.created_at,
        idempotency_key=job.idempotency_key,
    )