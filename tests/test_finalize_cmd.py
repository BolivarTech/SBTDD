# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for /sbtdd finalize subcommand (sec.S.5.7)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _seed_state(
    tmp_path: Path,
    *,
    current_phase: str = "done",
    current_task_id: str | None = None,
    current_task_title: str | None = None,
    plan_approved_at: str | None = "2026-04-20T03:30:00Z",
) -> Path:
    """Write a minimal valid state file into tmp_path/.claude."""
    claude = tmp_path / ".claude"
    claude.mkdir(parents=True, exist_ok=True)
    state = {
        "plan_path": "planning/claude-plan-tdd.md",
        "current_task_id": current_task_id,
        "current_task_title": current_task_title,
        "current_phase": current_phase,
        "phase_started_at_commit": "abc1234",
        "last_verification_at": "2026-04-20T03:30:00Z",
        "last_verification_result": "passed",
        "plan_approved_at": plan_approved_at,
    }
    state_path = claude / "session-state.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    return state_path


def _seed_magi_verdict(
    tmp_path: Path,
    *,
    verdict: str = "GO",
    degraded: bool = False,
    timestamp: str = "2026-04-21T00:00:00Z",
    conditions: list[str] | None = None,
) -> Path:
    """Write a magi-verdict.json artifact."""
    path = tmp_path / ".claude" / "magi-verdict.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": timestamp,
        "verdict": verdict,
        "degraded": degraded,
        "conditions": conditions or [],
        "findings": [],
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_finalize_cmd_module_importable() -> None:
    import finalize_cmd

    assert hasattr(finalize_cmd, "main")


def test_finalize_aborts_when_magi_verdict_missing(tmp_path: Path) -> None:
    import finalize_cmd
    from errors import PreconditionError

    _seed_state(tmp_path, current_phase="done")
    with pytest.raises(PreconditionError):
        finalize_cmd.main(["--project-root", str(tmp_path)])


def test_finalize_aborts_when_state_not_done(tmp_path: Path) -> None:
    import finalize_cmd
    from errors import PreconditionError

    _seed_state(tmp_path, current_phase="red", current_task_id="1", current_task_title="t")
    _seed_magi_verdict(tmp_path)
    with pytest.raises(PreconditionError):
        finalize_cmd.main(["--project-root", str(tmp_path)])
