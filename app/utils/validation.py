"""Validation utilities for recipient data."""
from __future__ import annotations

import re
from typing import Optional

EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
NAME_RE = re.compile(r"^[a-zA-Z0-9 .,'-]{2,255}$")
CERT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,120}$")


def validate_recipient(
    name: str, email: Optional[str], cert_id: Optional[str]
) -> list[str]:
    """Return a list of validation errors for a recipient record."""
    errors: list[str] = []

    if not NAME_RE.match(name):
        errors.append("Name must be 2-255 printable characters.")

    if email and not EMAIL_RE.match(email):
        errors.append(f"Invalid email format: {email!r}")

    if cert_id and not CERT_ID_RE.match(cert_id):
        errors.append(f"Invalid certificate ID: {cert_id!r}")

    return errors