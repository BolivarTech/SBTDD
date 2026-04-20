# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for /sbtdd auto subcommand (sec.S.5.8, INV-22..26)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def test_auto_cmd_module_importable() -> None:
    import auto_cmd

    assert hasattr(auto_cmd, "main")


def test_auto_dry_run_short_circuits_before_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dry-run must return 0 WITHOUT invoking subprocess/preflight (Finding 4).

    Guards against wasted time when the user only wants a plan preview
    on a machine where toolchain checks are slow or unavailable.
    """
    import auto_cmd

    original_run = subprocess.run

    def _boom(*a: object, **k: object) -> object:
        raise AssertionError("dry-run must not invoke subprocess.run")

    monkeypatch.setattr(subprocess, "run", _boom)
    rc = auto_cmd.main(["--project-root", str(tmp_path), "--dry-run"])
    assert rc == 0
    assert not (tmp_path / ".claude" / "auto-run.json").exists()
    # Restore for downstream tests.
    monkeypatch.setattr(subprocess, "run", original_run)


def test_auto_parses_magi_max_iterations_flag() -> None:
    import auto_cmd

    ns = auto_cmd._build_parser().parse_args(["--magi-max-iterations", "7"])
    assert ns.magi_max_iterations == 7


# ---------------------------------------------------------------------------
# Task 27 -- Phase 1 pre-flight + state validation.
# ---------------------------------------------------------------------------


def _seed_plugin_local(tmp_path: Path) -> None:
    """Copy the valid-python plugin.local.md fixture into tmp_path/.claude."""
    import shutil

    (tmp_path / ".claude").mkdir(exist_ok=True)
    fixture = Path(__file__).parent / "fixtures" / "plugin-locals" / "valid-python.md"
    shutil.copy(fixture, tmp_path / ".claude" / "plugin.local.md")


def _seed_state(
    tmp_path: Path,
    *,
    current_phase: str = "done",
    current_task_id: str | None = None,
    current_task_title: str | None = None,
    plan_approved_at: str | None = "2026-04-20T03:30:00Z",
) -> Path:
    """Write a minimal valid state file into tmp_path/.claude."""
    import json as _json

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
    state_path.write_text(_json.dumps(state), encoding="utf-8")
    return state_path


def _ok_report() -> object:
    """Return a DependencyReport with a single synthetic OK check."""
    from dependency_check import DependencyCheck, DependencyReport

    return DependencyReport(
        checks=(DependencyCheck(name="stub", status="OK", detail="ok", remediation=None),)
    )


def _broken_report() -> object:
    """Return a DependencyReport with one failing check (for abort path)."""
    from dependency_check import DependencyCheck, DependencyReport

    return DependencyReport(
        checks=(
            DependencyCheck(name="stub", status="MISSING", detail="nope", remediation="install"),
        )
    )


def test_auto_runs_preflight_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import auto_cmd

    _seed_plugin_local(tmp_path)
    _seed_state(tmp_path, current_phase="done")

    calls = {"preflight": 0}

    def fake_check(stack: str, root: object, plugins_root: object) -> object:
        calls["preflight"] += 1
        return _ok_report()

    monkeypatch.setattr(auto_cmd, "check_environment", fake_check)
    auto_cmd._phase1_preflight(
        auto_cmd._build_parser().parse_args(["--project-root", str(tmp_path)])
    )
    assert calls["preflight"] == 1


def test_auto_aborts_when_preflight_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import auto_cmd
    from errors import DependencyError

    _seed_plugin_local(tmp_path)
    _seed_state(tmp_path, current_phase="done")
    monkeypatch.setattr(auto_cmd, "check_environment", lambda *a, **k: _broken_report())
    with pytest.raises(DependencyError):
        auto_cmd._phase1_preflight(
            auto_cmd._build_parser().parse_args(["--project-root", str(tmp_path)])
        )


def test_auto_aborts_when_state_missing(tmp_path: Path) -> None:
    import auto_cmd
    from errors import PreconditionError

    _seed_plugin_local(tmp_path)
    # no state file seeded
    with pytest.raises(PreconditionError):
        auto_cmd._phase1_preflight(
            auto_cmd._build_parser().parse_args(["--project-root", str(tmp_path)])
        )


def test_auto_aborts_when_plan_not_approved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import auto_cmd
    from errors import PreconditionError

    _seed_plugin_local(tmp_path)
    _seed_state(tmp_path, current_phase="red", plan_approved_at=None)
    monkeypatch.setattr(auto_cmd, "check_environment", lambda *a, **k: _ok_report())
    with pytest.raises(PreconditionError):
        auto_cmd._phase1_preflight(
            auto_cmd._build_parser().parse_args(["--project-root", str(tmp_path)])
        )
