"""API endpoint handlers for certificate generation."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, async_session_factory
from app.schemas.job import JobCreate, JobListResponse, JobResponse, JobStatusResponse
from app.services import (
    create_job,
    download_job_certificates,
    get_job_status,
    list_jobs,
)
from app.services.pdf_service import process_job
from app.core.background import dispatch_job

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.post("/generate", response_model=JobResponse, status_code=201)
async def generate_certificates(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Submit a bulk certificate generation job.

    Returns immediately with a job_id. Generation runs in the background.
    """
    job = await create_job(payload, db)
    background_tasks.add_task(
        dispatch_job, job.id, process_job, lambda: async_session_factory()
    )
    return _job_to_response(job)


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_status(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get detailed status of a job."""
    status = await get_job_status(job_id, db)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.get("/jobs", response_model=JobListResponse)
async def list_all_jobs(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List all jobs with pagination."""
    return await list_jobs(page, size, db)


@router.get("/jobs/{job_id}/download")
async def download_certificates(
    job_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    """Download a ZIP of all generated certificates."""
    data = await download_job_certificates(job_id, db)
    if data is None:
        raise HTTPException(status_code=404, detail="ZIP not found or job incomplete")
    return data


def _job_to_response(job) -> JobResponse:
    return JobResponse(
        job_id=job.id,
        status=job.status,
        total_recipients=job.total_recipients,
        created_at=job.created_at,
        idempotency_key=job.idempotency_key,
    )