"""Background PDF generation service."""
from __future__ import annotations

import uuid
import zipfile
from pathlib import Path

from sqlalchemy import select, update

from app.config import settings
from app.db.session import async_session_factory
from app.models.models import Job, Recipient
from app.pdf.template import generate_certificate
from app.services.job_service import (
    update_job_progress,
    set_job_result_path,
)


async def process_job(job_id: uuid.UUID, db_factory) -> None:
    """Generate certificates for all pending recipients in the job.

    Per-recipient error isolation: one failure does not prevent
    other certificates in the same job from being generated.
    """
    async with db_factory() as db:
        job = (
            await db.execute(
                select(Job).where(Job.id == job_id)
            )
        ).scalar_one_or_none()
        if not job or job.status not in ("pending", "processing"):
            return

        await db.execute(
            update(Job).where(Job.id == job_id).values(status="processing")
        )
        await db.commit()

        recipients = (
            await db.execute(
                select(Recipient).where(Recipient.job_id == job_id)
            )
        ).scalars().all()

    pending = [r for r in recipients if r.status == "pending"]
    output_dir = Path(settings.CERTIFICATE_STORAGE_DIR) / str(job_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    for recipient in pending:
        try:
            issue_date = (
                job.created_at.strftime("%Y-%m-%d")
                if job and job.created_at
                else "today"
            )
            cert_path = generate_certificate(
                recipient_name=recipient.name,
                job_id=str(job_id),
                cert_id=recipient.certificate_id or str(recipient.id)[:8],
                issue_date=issue_date,
                event_name=job.event_name if job else "Event",
                template_style=job.template_style if job else "modern",
                output_dir=str(output_dir),
            )
            recipient.status = "success"
            recipient.certificate_path = cert_path
        except Exception as exc:  # noqa: BLE001
            recipient.status = "failed"
            recipient.error_message = str(exc)

    # Commit status changes
    async with db_factory() as db:
        await db.commit()

    # Update progress counters
    async with db_factory() as db:
        await update_job_progress(job_id, db)

    # Build ZIP archive
    zip_path = str(output_dir / f"certificates_{job_id}.zip")
    await _build_zip(job_id, str(output_dir), zip_path)

    # Record result path
    async with db_factory() as db:
        await set_job_result_path(job_id, zip_path, db)


async def _build_zip(
    job_id: uuid.UUID, out_dir: str, zip_path: str,
) -> None:
    """Create a ZIP archive of all successful certificates."""
    async with async_session_factory() as db:
        recipients = (
            await db.execute(
                select(Recipient).where(Recipient.job_id == job_id)
            )
        ).scalars().all()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in recipients:
            if r.certificate_path and Path(r.certificate_path).exists():
                zf.write(r.certificate_path, arcname=Path(r.certificate_path).name)