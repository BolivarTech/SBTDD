# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for /sbtdd finalize subcommand (sec.S.5.7)."""

from __future__ import annotations

import json
import subprocess
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


def test_finalize_aborts_when_verdict_predates_plan_approved_at(tmp_path: Path) -> None:
    import finalize_cmd
    from errors import PreconditionError

    _seed_state(tmp_path, current_phase="done", plan_approved_at="2026-04-20T00:00:00Z")
    _seed_magi_verdict(tmp_path, timestamp="2026-04-10T00:00:00Z")
    with pytest.raises(PreconditionError):
        finalize_cmd.main(["--project-root", str(tmp_path)])


def test_finalize_accepts_verdict_after_plan_approved_at(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verdict timestamp later than plan_approved_at passes staleness check."""
    import finalize_cmd

    _seed_state(tmp_path, current_phase="done", plan_approved_at="2026-04-20T00:00:00Z")
    _seed_magi_verdict(tmp_path, timestamp="2026-04-21T00:00:00Z")

    # Staleness guard must not raise; checklist and downstream logic come in Task 24.
    finalize_cmd._preflight(tmp_path)


# ---------------------------------------------------------------------------
# Task 24 -- checklist validation + ChecklistError.
# ---------------------------------------------------------------------------


def _setup_git_repo(tmp_path: Path) -> None:
    """Init a git repo with an initial commit so HEAD resolves cleanly."""
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "tester@example.com"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Tester"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    (tmp_path / "README.md").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: initial"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )


def _seed_plugin_local(tmp_path: Path) -> None:
    """Copy the valid-python plugin.local.md fixture into tmp_path/.claude."""
    import shutil

    (tmp_path / ".claude").mkdir(exist_ok=True)
    fixture = Path(__file__).parent / "fixtures" / "plugin-locals" / "valid-python.md"
    shutil.copy(fixture, tmp_path / ".claude" / "plugin.local.md")


def _seed_plan_all_done(tmp_path: Path) -> Path:
    """Write a plan where every task is marked complete."""
    planning = tmp_path / "planning"
    planning.mkdir(parents=True, exist_ok=True)
    plan = planning / "claude-plan-tdd.md"
    plan.write_text(
        "# Plan\n\n### Task 1: done\n- [x] step\n\n### Task 2: done\n- [x] step\n",
        encoding="utf-8",
    )
    return plan


def _seed_plan_with_open_task(tmp_path: Path) -> Path:
    """Write a plan that still has an open task checkbox."""
    planning = tmp_path / "planning"
    planning.mkdir(parents=True, exist_ok=True)
    plan = planning / "claude-plan-tdd.md"
    plan.write_text(
        "# Plan\n\n### Task 1: open\n- [ ] step\n",
        encoding="utf-8",
    )
    return plan


def _seed_spec_files(tmp_path: Path) -> None:
    """Write minimal sbtdd/spec-behavior.md so the checklist item passes."""
    spec_dir = tmp_path / "sbtdd"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec-behavior.md").write_text("# behavior\n", encoding="utf-8")


def _seed_clean_env(
    tmp_path: Path,
    *,
    verdict: str = "GO",
    degraded: bool = False,
    plan_open: bool = False,
) -> None:
    """Seed a clean environment where all checklist items pass by default."""
    _setup_git_repo(tmp_path)
    _seed_plugin_local(tmp_path)
    _seed_spec_files(tmp_path)
    if plan_open:
        _seed_plan_with_open_task(tmp_path)
    else:
        _seed_plan_all_done(tmp_path)
    # Commit plan + spec so ``git status`` stays clean -- in real workflow
    # these artifacts are tracked (CLAUDE.local.md sec.1 Jerarquia).
    # ``.claude/`` remains untracked; exclude it via .gitignore for cleanliness.
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", ".gitignore", "sbtdd", "planning"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "chore: seed spec and plan"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    # State file + magi-verdict written AFTER the commit so they remain in
    # the ignored ``.claude/`` directory without dirtying the tree.
    _seed_state(tmp_path, current_phase="done")
    _seed_magi_verdict(tmp_path, verdict=verdict, degraded=degraded)


def test_finalize_rejects_verdict_below_threshold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """HOLD full (below GO_WITH_CAVEATS threshold) -> ChecklistError."""
    import finalize_cmd
    import superpowers_dispatch
    from errors import ChecklistError

    _seed_clean_env(tmp_path, verdict="HOLD", degraded=False)
    monkeypatch.setattr(superpowers_dispatch, "verification_before_completion", lambda **kw: None)
    monkeypatch.setattr(superpowers_dispatch, "finishing_a_development_branch", lambda **kw: None)
    with pytest.raises(ChecklistError):
        finalize_cmd.main(["--project-root", str(tmp_path)])


def test_finalize_rejects_degraded_verdict_even_above_threshold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """INV-28 defense-in-depth: GO degraded -> ChecklistError."""
    import finalize_cmd
    import superpowers_dispatch
    from errors import ChecklistError

    _seed_clean_env(tmp_path, verdict="GO", degraded=True)
    monkeypatch.setattr(superpowers_dispatch, "verification_before_completion", lambda **kw: None)
    monkeypatch.setattr(superpowers_dispatch, "finishing_a_development_branch", lambda **kw: None)
    with pytest.raises(ChecklistError):
        finalize_cmd.main(["--project-root", str(tmp_path)])


def test_finalize_accepts_go_full(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """9 checklist items pass -> rc=0."""
    import finalize_cmd
    import superpowers_dispatch

    _seed_clean_env(tmp_path, verdict="GO", degraded=False)
    monkeypatch.setattr(superpowers_dispatch, "verification_before_completion", lambda **kw: None)
    monkeypatch.setattr(superpowers_dispatch, "finishing_a_development_branch", lambda **kw: None)
    rc = finalize_cmd.main(["--project-root", str(tmp_path)])
    assert rc == 0


def test_finalize_aborts_on_dirty_working_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dirty tree -> ChecklistError."""
    import finalize_cmd
    import superpowers_dispatch
    from errors import ChecklistError

    _seed_clean_env(tmp_path, verdict="GO", degraded=False)
    # Introduce an untracked file to dirty the tree.
    (tmp_path / "stray.txt").write_text("x", encoding="utf-8")
    monkeypatch.setattr(superpowers_dispatch, "verification_before_completion", lambda **kw: None)
    monkeypatch.setattr(superpowers_dispatch, "finishing_a_development_branch", lambda **kw: None)
    with pytest.raises(ChecklistError):
        finalize_cmd.main(["--project-root", str(tmp_path)])


def test_finalize_aborts_on_plan_with_open_tasks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Open - [ ] checkbox in plan -> ChecklistError."""
    import finalize_cmd
    import superpowers_dispatch
    from errors import ChecklistError

    _seed_clean_env(tmp_path, verdict="GO", degraded=False, plan_open=True)
    monkeypatch.setattr(superpowers_dispatch, "verification_before_completion", lambda **kw: None)
    monkeypatch.setattr(superpowers_dispatch, "finishing_a_development_branch", lambda **kw: None)
    with pytest.raises(ChecklistError):
        finalize_cmd.main(["--project-root", str(tmp_path)])
