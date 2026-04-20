#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for superpowers_dispatch module."""

from __future__ import annotations

import subprocess

import pytest


def test_skill_result_is_frozen_dataclass():
    from dataclasses import FrozenInstanceError

    from superpowers_dispatch import SkillResult

    res = SkillResult(skill="brainstorming", returncode=0, stdout="ok", stderr="")
    with pytest.raises(FrozenInstanceError):
        res.returncode = 1  # type: ignore[misc]


def test_invoke_skill_returns_skill_result_on_success(monkeypatch):
    from superpowers_dispatch import SkillResult, invoke_skill

    class FakeProc:
        returncode = 0
        stdout = "hello"
        stderr = ""

    calls: dict = {}

    def fake_run(cmd, timeout, capture=True, cwd=None):
        calls["cmd"] = cmd
        calls["timeout"] = timeout
        return FakeProc()

    monkeypatch.setattr("subprocess_utils.run_with_timeout", fake_run)
    result = invoke_skill("brainstorming", args=["arg1"], timeout=42)
    assert isinstance(result, SkillResult)
    assert result.skill == "brainstorming"
    assert result.returncode == 0
    assert result.stdout == "hello"
    assert calls["timeout"] == 42
    # Must use shell=False (as list), no shell=True risk.
    assert isinstance(calls["cmd"], list)
    # Command must include skill invocation marker.
    assert any("brainstorming" in t for t in calls["cmd"])


def test_invoke_skill_raises_quota_on_quota_pattern(monkeypatch):
    from errors import QuotaExhaustedError
    from superpowers_dispatch import invoke_skill

    class FakeProc:
        returncode = 1
        stdout = ""
        stderr = "Request rejected (429)"

    monkeypatch.setattr(
        "subprocess_utils.run_with_timeout",
        lambda cmd, timeout, capture=True, cwd=None: FakeProc(),
    )
    with pytest.raises(QuotaExhaustedError) as exc_info:
        invoke_skill("brainstorming")
    assert "429" in str(exc_info.value) or "rate_limit" in str(exc_info.value)


def test_invoke_skill_non_quota_nonzero_raises_validation_error(monkeypatch):
    from errors import ValidationError
    from superpowers_dispatch import invoke_skill

    class FakeProc:
        returncode = 2
        stdout = ""
        stderr = "some unrelated error"

    monkeypatch.setattr(
        "subprocess_utils.run_with_timeout",
        lambda cmd, timeout, capture=True, cwd=None: FakeProc(),
    )
    with pytest.raises(ValidationError) as exc_info:
        invoke_skill("brainstorming")
    assert "returncode=2" in str(exc_info.value) or "returncode" in str(exc_info.value)


def test_invoke_skill_wraps_timeout_as_validation_error(monkeypatch):
    from errors import ValidationError
    from superpowers_dispatch import invoke_skill

    def fake_run(cmd, timeout, capture=True, cwd=None):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr("subprocess_utils.run_with_timeout", fake_run)
    with pytest.raises(ValidationError, match="timed out"):
        invoke_skill("writing-plans")
