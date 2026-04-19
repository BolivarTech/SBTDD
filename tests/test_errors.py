"""Tests for skills/sbtdd/scripts/errors.py — exception hierarchy."""

from __future__ import annotations

import pytest


def test_sbtdd_error_base_class():
    from errors import SBTDDError

    assert issubclass(SBTDDError, Exception)
    err = SBTDDError("generic failure")
    assert str(err) == "generic failure"


def test_validation_error_is_sbtdd_error():
    from errors import SBTDDError, ValidationError

    assert issubclass(ValidationError, SBTDDError)


def test_validation_error_caught_by_sbtdd_error():
    from errors import SBTDDError, ValidationError

    with pytest.raises(SBTDDError):
        raise ValidationError("schema invalid")
