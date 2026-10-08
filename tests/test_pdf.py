"""Tests for PDF generation."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.pdf.template import generate_certificate


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "certs"


def test_generate_certificate(output_dir: Path) -> None:
    """A single certificate PDF is generated."""
    path = generate_certificate(
        recipient_name="Alice Johnson",
        job_id="test-job",
        cert_id="CERT-001",
        issue_date="2025-06-15",
        event_name="Test Event",
        template_style="modern",
        output_dir=str(output_dir),
    )
    assert Path(path).exists()
    assert Path(path).stat().st_size > 0
    assert path.endswith(".pdf")