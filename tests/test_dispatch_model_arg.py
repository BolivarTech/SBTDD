#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-25
"""Tests for v0.3.0 Feature E dispatch model arg propagation + INV-0."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "sbtdd" / "scripts"))

import superpowers_dispatch


def test_dispatch_with_model_none_byte_identical_to_v02() -> None:
    """E3.1: default model=None preserves v0.2.x argv shape."""
    argv = superpowers_dispatch._build_skill_cmd(
        "test-driven-development", ["--phase=red"], model=None
    )
    assert argv == ["claude", "-p", "/test-driven-development --phase=red"]
    assert "--model" not in argv


def test_dispatch_with_model_injects_flag() -> None:
    """E3.2: model=claude-haiku-4-5 inserts --model BEFORE -p."""
    argv = superpowers_dispatch._build_skill_cmd(
        "test-driven-development", ["--phase=red"], model="claude-haiku-4-5"
    )
    assert argv == [
        "claude",
        "--model",
        "claude-haiku-4-5",
        "-p",
        "/test-driven-development --phase=red",
    ]


def test_inv0_precedence_pinned_model_wins(
    tmp_path: Path, capfd: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """E3.3: CLAUDE.md pinned model wins, breadcrumb emitted."""
    fake_home = tmp_path
    (fake_home / ".claude").mkdir()
    (fake_home / ".claude" / "CLAUDE.md").write_text("Use claude-opus-4-7 for all sessions.\n")
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    effective = superpowers_dispatch._apply_inv0_model_check(
        configured_model="claude-sonnet-4-6", skill_field_name="implementer_model"
    )
    captured = capfd.readouterr()
    assert effective is None  # config ignored
    assert "[sbtdd inv-0]" in captured.err
    assert "claude-opus-4-7" in captured.err
    assert "implementer_model=claude-sonnet-4-6" in captured.err


def test_inv0_no_pinned_model_config_respected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """E3.4: when CLAUDE.md does not pin, configured model passes through."""
    fake_home = tmp_path
    (fake_home / ".claude").mkdir()
    (fake_home / ".claude" / "CLAUDE.md").write_text(
        "Code Standards. Prefer OOP. Use snake_case.\n"
    )
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    effective = superpowers_dispatch._apply_inv0_model_check(
        configured_model="claude-sonnet-4-6", skill_field_name="implementer_model"
    )
    captured = capfd.readouterr()
    assert effective == "claude-sonnet-4-6"
    assert "[sbtdd inv-0]" not in captured.err


def test_inv0_with_none_configured_returns_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When configured_model is None (default), return None without scanning."""
    fake_home = tmp_path
    (fake_home / ".claude").mkdir()
    (fake_home / ".claude" / "CLAUDE.md").write_text("Use claude-opus-4-7 for all sessions.\n")
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    effective = superpowers_dispatch._apply_inv0_model_check(
        configured_model=None, skill_field_name="implementer_model"
    )
    assert effective is None


def test_spec_review_dispatch_module_imports_apply_inv0() -> None:
    """E3 mirror: spec_review_dispatch wiring exists."""
    import spec_review_dispatch

    # The dispatch_spec_reviewer signature must accept model + skill_field_name.
    import inspect

    sig = inspect.signature(spec_review_dispatch.dispatch_spec_reviewer)
    assert "model" in sig.parameters
    assert "skill_field_name" in sig.parameters


def test_magi_dispatch_build_with_model_inserts_flag() -> None:
    """E3 mirror: magi_dispatch._build_magi_cmd accepts model kwarg."""
    import magi_dispatch

    argv = magi_dispatch._build_magi_cmd(
        ["spec-behavior.md"], output_dir="/tmp/x", model="claude-sonnet-4-6"
    )
    # --model should appear BEFORE -p (claude CLI flag ordering convention).
    assert "--model" in argv
    model_idx = argv.index("--model")
    p_idx = argv.index("-p")
    assert model_idx < p_idx
    assert argv[model_idx + 1] == "claude-sonnet-4-6"


def test_magi_dispatch_build_with_model_none_byte_identical_to_v02() -> None:
    """E3 mirror: magi_dispatch._build_magi_cmd with model=None preserves v0.2 shape."""
    import magi_dispatch

    argv = magi_dispatch._build_magi_cmd(["spec-behavior.md"], output_dir="/tmp/x", model=None)
    assert "--model" not in argv
