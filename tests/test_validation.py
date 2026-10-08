"""Unit tests for validation and service logic."""
from __future__ import annotations

import pytest

from app.utils.validation import validate_recipient


class TestValidateRecipient:
    def test_valid_recipient(self) -> None:
        errs = validate_recipient("Alice Johnson", "alice@example.com", "CERT-001")
        assert errs == []

    def test_empty_name(self) -> None:
        errs = validate_recipient("", "alice@example.com", None)
        assert len(errs) > 0

    def test_invalid_email(self) -> None:
        errs = validate_recipient("Alice", "not-an-email", None)
        assert any("email" in e.lower() for e in errs)

    def test_invalid_cert_id(self) -> None:
        errs = validate_recipient("Alice", None, "!!!invalid!!!")
        assert any("certificate" in e.lower() for e in errs)

    def test_long_name(self) -> None:
        errs = validate_recipient("A" * 300, None, None)
        assert len(errs) > 0