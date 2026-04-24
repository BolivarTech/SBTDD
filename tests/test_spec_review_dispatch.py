"""Tests for skills/sbtdd/scripts/spec_review_dispatch.py — dataclasses."""

from __future__ import annotations

import pytest


def test_spec_review_result_is_frozen() -> None:
    from spec_review_dispatch import SpecReviewResult, SpecIssue  # type: ignore[import-not-found]  # noqa: F401

    r = SpecReviewResult(approved=True, issues=(), reviewer_iter=1, artifact_path=None)
    with pytest.raises((AttributeError, Exception)):
        r.approved = False


def test_spec_issue_carries_severity_and_text() -> None:
    from spec_review_dispatch import SpecIssue  # type: ignore[import-not-found]

    i = SpecIssue(severity="MISSING", text="Scenario 4 not covered")
    assert i.severity == "MISSING"
