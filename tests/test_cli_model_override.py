#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-25
"""Tests for v0.3.0 Feature E --model-override CLI flag on auto."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "sbtdd" / "scripts"))

import auto_cmd
from errors import ValidationError


def test_model_override_valid_skill_accepts() -> None:
    """E4.1: implementer:claude-haiku-4-5 parses to {implementer: ...}."""
    result = auto_cmd._parse_model_overrides(["implementer:claude-haiku-4-5"])
    assert result == {"implementer": "claude-haiku-4-5"}


def test_model_override_invalid_skill_rejects() -> None:
    """E4.2: foo:claude-haiku-4-5 raises ValidationError exit 1."""
    with pytest.raises(ValidationError) as ei:
        auto_cmd._parse_model_overrides(["foo:claude-haiku-4-5"])
    assert "invalid --model-override skill name 'foo'" in str(ei.value)
    assert "implementer" in str(ei.value)
    assert "spec_reviewer" in str(ei.value)


def test_model_override_multi_flag_accumulates() -> None:
    """E4.3: multiple --model-override flags merge into one dict."""
    result = auto_cmd._parse_model_overrides(
        [
            "implementer:claude-haiku-4-5",
            "spec_reviewer:claude-sonnet-4-6",
        ]
    )
    assert result == {
        "implementer": "claude-haiku-4-5",
        "spec_reviewer": "claude-sonnet-4-6",
    }


def test_model_override_missing_separator_rejects() -> None:
    """E4.5: implementerhaiku4-5 (no colon) raises ValidationError."""
    with pytest.raises(ValidationError) as ei:
        auto_cmd._parse_model_overrides(["implementerhaiku4-5"])
    assert "expects '<skill>:<model>'" in str(ei.value)


def test_resolve_model_cli_override_wins() -> None:
    """CLI override > config field for the same skill."""
    from config import PluginConfig

    cfg = PluginConfig(
        stack="python",
        author="t",
        error_type=None,
        verification_commands=("pytest",),
        plan_path="planning/claude-plan-tdd.md",
        plan_org_path="planning/claude-plan-tdd-org.md",
        spec_base_path="sbtdd/spec-behavior-base.md",
        spec_path="sbtdd/spec-behavior.md",
        state_file_path=".claude/session-state.json",
        magi_threshold="GO_WITH_CAVEATS",
        magi_max_iterations=3,
        auto_magi_max_iterations=5,
        auto_verification_retries=2,
        auto_max_spec_review_seconds=3600,
        tdd_guard_enabled=True,
        worktree_policy="optional",
        implementer_model="claude-sonnet-4-6",
    )
    result = auto_cmd._resolve_model(
        "implementer", cfg, {"implementer": "claude-haiku-4-5"}
    )
    assert result == "claude-haiku-4-5"


def test_resolve_model_falls_back_to_config() -> None:
    """No CLI override -> config field wins."""
    from config import PluginConfig

    cfg = PluginConfig(
        stack="python",
        author="t",
        error_type=None,
        verification_commands=("pytest",),
        plan_path="planning/claude-plan-tdd.md",
        plan_org_path="planning/claude-plan-tdd-org.md",
        spec_base_path="sbtdd/spec-behavior-base.md",
        spec_path="sbtdd/spec-behavior.md",
        state_file_path=".claude/session-state.json",
        magi_threshold="GO_WITH_CAVEATS",
        magi_max_iterations=3,
        auto_magi_max_iterations=5,
        auto_verification_retries=2,
        auto_max_spec_review_seconds=3600,
        tdd_guard_enabled=True,
        worktree_policy="optional",
        implementer_model="claude-sonnet-4-6",
    )
    result = auto_cmd._resolve_model("implementer", cfg, {})
    assert result == "claude-sonnet-4-6"


def test_resolve_model_returns_none_when_no_config_no_cli() -> None:
    """No CLI override + no config -> None (inherit session)."""
    from config import PluginConfig

    cfg = PluginConfig(
        stack="python",
        author="t",
        error_type=None,
        verification_commands=("pytest",),
        plan_path="planning/claude-plan-tdd.md",
        plan_org_path="planning/claude-plan-tdd-org.md",
        spec_base_path="sbtdd/spec-behavior-base.md",
        spec_path="sbtdd/spec-behavior.md",
        state_file_path=".claude/session-state.json",
        magi_threshold="GO_WITH_CAVEATS",
        magi_max_iterations=3,
        auto_magi_max_iterations=5,
        auto_verification_retries=2,
        auto_max_spec_review_seconds=3600,
        tdd_guard_enabled=True,
        worktree_policy="optional",
    )
    result = auto_cmd._resolve_model("implementer", cfg, {})
    assert result is None


def test_argparse_model_override_flag_present() -> None:
    """auto's argparse exposes --model-override repeatable flag."""
    parser = auto_cmd._build_parser()
    ns = parser.parse_args(
        [
            "--model-override",
            "implementer:claude-haiku-4-5",
            "--model-override",
            "spec_reviewer:claude-sonnet-4-6",
        ]
    )
    assert ns.model_override == [
        "implementer:claude-haiku-4-5",
        "spec_reviewer:claude-sonnet-4-6",
    ]


def test_argparse_model_override_default_empty() -> None:
    """No --model-override flags -> empty list (default)."""
    parser = auto_cmd._build_parser()
    ns = parser.parse_args([])
    assert ns.model_override == []
