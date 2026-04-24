# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-24
"""Tests for Task G9 — ``resume_cmd`` detects ``.claude/magi-escalation-pending.md``.

Two orthogonal concerns covered:

1. ``escalation_prompt.prompt_user`` writes a pending-marker file BEFORE the
   first ``input()`` call and removes it after the decision (success OR EOF),
   so a Ctrl+C between "marker written" and "decision returned" leaves the
   marker on disk as a recoverable checkpoint.
2. ``resume_cmd`` detects the marker at entry, reconstructs the escalation
   context from the serialized JSON, re-enters ``prompt_user`` +
   ``apply_decision``, deletes the marker, and delegates to the original
   subcommand (``spec_cmd`` for ``context == "checkpoint2"``,
   ``pre_merge_cmd`` for ``context == "pre-merge"``).

Spec ref: plan Task G9, sec.1 (Feature A resumability requirement R5 of
``sbtdd/spec-behavior-base.md``).
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest


# ---------------------------------------------------------------------------
# Helpers -------------------------------------------------------------------
# ---------------------------------------------------------------------------


def _mkv(verdict: str, degraded: bool = False):
    """Build a minimal ``MAGIVerdict`` for tests."""
    from magi_dispatch import MAGIVerdict

    return MAGIVerdict(
        verdict=verdict,
        degraded=degraded,
        conditions=(),
        findings=(),
        raw_output="",
    )


def _setup_repo(tmp_path: Path) -> None:
    """Init a git repo with one commit so ``resume_cmd`` HEAD probes succeed.

    Seeds ``.gitignore`` with ``.claude/`` + ``planning/`` so runtime artefacts
    placed by the tests do not trip ``git status`` into DIRTY (which would
    route ``main`` to ``uncommitted-resolution`` rather than the escalation
    path under test).
    """
    import subprocess as _sp

    _sp.run(["git", "init", "-q"], cwd=str(tmp_path), check=True, capture_output=True)
    _sp.run(
        ["git", "config", "user.email", "t@example.com"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    _sp.run(
        ["git", "config", "user.name", "t"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    _sp.run(
        ["git", "config", "commit.gpgsign", "false"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    (tmp_path / ".gitignore").write_text(".claude/\nplanning/\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("x\n", encoding="utf-8")
    _sp.run(
        ["git", "add", ".gitignore", "README.md"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    _sp.run(
        ["git", "commit", "-m", "chore: initial"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )


def _seed_plugin_local(tmp_path: Path) -> None:
    """Minimal ``plugin.local.md`` so the ``resume`` precondition passes."""
    import shutil

    claude = tmp_path / ".claude"
    claude.mkdir(exist_ok=True)
    fixture = Path(__file__).parent / "fixtures" / "plugin-locals" / "valid-python.md"
    shutil.copy(fixture, claude / "plugin.local.md")


def _seed_state(tmp_path: Path) -> None:
    """Minimal valid state file so ``_report_diagnostic`` works."""
    claude = tmp_path / ".claude"
    claude.mkdir(parents=True, exist_ok=True)
    (claude / "session-state.json").write_text(
        json.dumps(
            {
                "plan_path": "planning/claude-plan-tdd.md",
                "current_task_id": None,
                "current_task_title": None,
                "current_phase": "done",
                "phase_started_at_commit": "abc1234",
                "last_verification_at": "2026-04-24T01:00:00Z",
                "last_verification_result": "passed",
                "plan_approved_at": "2026-04-24T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )


def _write_pending_marker(tmp_path: Path, context: str = "checkpoint2") -> Path:
    """Simulate a prior ``prompt_user`` that wrote the marker and then died."""
    claude = tmp_path / ".claude"
    claude.mkdir(parents=True, exist_ok=True)
    pending = claude / "magi-escalation-pending.md"
    pending.write_text(
        json.dumps(
            {
                "plan_id": "G",
                "context": context,
                "root_cause": "infra_transient",
                "iterations": [
                    {
                        "verdict": "HOLD",
                        "degraded": True,
                        "n_conditions": 0,
                        "n_findings": 0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return pending


# ---------------------------------------------------------------------------
# Group 1: ``prompt_user`` marker write/remove protocol -------------------
# ---------------------------------------------------------------------------


def test_prompt_user_writes_pending_marker_before_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Marker must be on disk *at the moment* ``input()`` is called.

    Simulates the Ctrl+C window: the spy reads the filesystem mid-input, so
    if the marker is not written before ``input()``, the assertion fails.
    Ctrl+C (process kill) leaves the marker in place for ``resume_cmd`` to
    pick up.
    """
    from escalation_prompt import _compose_options, build_escalation_context, prompt_user

    ctx = build_escalation_context(
        iterations=[_mkv("HOLD", degraded=True)] * 3,
        plan_id="G",
        context="checkpoint2",
    )
    opts = _compose_options(ctx)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    pending = tmp_path / ".claude" / "magi-escalation-pending.md"
    seen = {"existed_during_input": False, "payload": None}

    def fake_input(prompt: str = "") -> str:
        seen["existed_during_input"] = pending.is_file()
        if pending.is_file():
            seen["payload"] = json.loads(pending.read_text(encoding="utf-8"))
        return "d"  # abandon: no reason prompt follow-up

    monkeypatch.setattr("builtins.input", fake_input)
    decision = prompt_user(ctx, opts, non_interactive=False, project_root=tmp_path)
    assert decision.action == "abandon"
    assert seen["existed_during_input"], "marker file must exist on disk BEFORE input() is awaited"
    assert isinstance(seen["payload"], dict)
    assert seen["payload"]["plan_id"] == "G"
    assert seen["payload"]["context"] == "checkpoint2"
    assert seen["payload"]["root_cause"] == "infra_transient"
    assert seen["payload"]["iterations"]  # non-empty


def test_prompt_user_removes_pending_marker_after_decision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Normal decision path: marker cleaned up so next session doesn't re-fire.

    Pre-seeds a dummy marker to prove the test fires on *removal*, not on
    mere absence — a stub ``prompt_user`` that never touched the filesystem
    would leave the pre-seeded marker in place and fail this assertion.
    """
    from escalation_prompt import _compose_options, build_escalation_context, prompt_user

    claude = tmp_path / ".claude"
    claude.mkdir(exist_ok=True)
    pending = claude / "magi-escalation-pending.md"
    pending.write_text("{}", encoding="utf-8")

    ctx = build_escalation_context(
        iterations=[_mkv("HOLD", degraded=True)] * 3,
        plan_id="G",
        context="pre-merge",
    )
    opts = _compose_options(ctx)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    inputs = iter(["a", "overriding for test"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    decision = prompt_user(ctx, opts, non_interactive=False, project_root=tmp_path)
    assert decision.action == "override"
    assert not pending.exists(), "marker must be removed after a successful decision"


def test_prompt_user_removes_pending_marker_after_eof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """EOF fallback still cleans up the marker (end-of-stream is a decision).

    Pre-seeds the marker so the assertion fires on *removal* rather than
    on the mere absence it would have had without any pre-seeding.
    """
    from escalation_prompt import _compose_options, build_escalation_context, prompt_user

    claude = tmp_path / ".claude"
    claude.mkdir(exist_ok=True)
    pending = claude / "magi-escalation-pending.md"
    pending.write_text("{}", encoding="utf-8")

    ctx = build_escalation_context(
        iterations=[_mkv("HOLD", degraded=True)] * 3,
        plan_id="G",
        context="checkpoint2",
    )
    opts = _compose_options(ctx)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)

    def raise_eof(prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    decision = prompt_user(ctx, opts, non_interactive=False, project_root=tmp_path)
    assert decision.action == "abandon"
    assert not pending.exists(), "marker must be removed after EOF fallback"


def test_prompt_user_non_tty_path_does_not_create_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Headless policy path skips the marker entirely (no input() is called)."""
    from escalation_prompt import _compose_options, build_escalation_context, prompt_user

    ctx = build_escalation_context(
        iterations=[_mkv("HOLD", degraded=True)] * 3,
        plan_id="G",
        context="checkpoint2",
    )
    opts = _compose_options(ctx)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    decision = prompt_user(ctx, opts, non_interactive=True, project_root=tmp_path)
    assert decision.action == "abandon"
    pending = tmp_path / ".claude" / "magi-escalation-pending.md"
    assert not pending.exists(), "headless policy path must not leave a marker"


# ---------------------------------------------------------------------------
# Group 2: ``resume_cmd`` detects marker + re-enters flow -----------------
# ---------------------------------------------------------------------------


def test_decide_delegation_returns_escalation_pending_sentinel(
    tmp_path: Path,
) -> None:
    """Decision tree must surface a dedicated sentinel for the pending marker.

    The existing ``magi-conditions.md`` path uses ``magi-conditions-pending``;
    this adds the symmetrical ``magi-escalation-pending`` branch so the
    dispatcher can route the flow to Feature A recovery instead of the
    fallthrough ``pre_merge_cmd``.
    """
    import resume_cmd

    state = SimpleNamespace(current_phase="done", current_task_id=None)
    runtime = {
        "auto-run.json": False,
        "magi-verdict.json": False,
        "magi-conditions.md": False,
        "magi-escalation-pending.md": True,
    }
    module_name, extra = resume_cmd._decide_delegation(state, tree_dirty=False, runtime=runtime)
    assert module_name == "magi-escalation-pending"
    assert extra == []


def test_report_diagnostic_includes_escalation_pending_marker(
    tmp_path: Path,
) -> None:
    """``_report_diagnostic`` exposes the pending-marker existence flag.

    Without the flag in the runtime snapshot, ``_decide_delegation`` has
    nothing to match against. Mirrors the existing ``magi-conditions.md``
    entry.
    """
    import resume_cmd

    _setup_repo(tmp_path)
    _seed_plugin_local(tmp_path)
    _seed_state(tmp_path)
    _write_pending_marker(tmp_path, context="checkpoint2")
    report = resume_cmd._report_diagnostic(tmp_path)
    assert report["runtime"].get("magi-escalation-pending.md") is True


def test_resume_main_reprompts_and_delegates_to_spec_for_checkpoint2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When marker's ``context == "checkpoint2"``, resume delegates to ``spec_cmd``.

    Flow:
      1. Marker present → ``_decide_delegation`` returns
         ``magi-escalation-pending``.
      2. ``main`` reads marker JSON, calls ``prompt_user`` + ``apply_decision``.
      3. Marker file is removed.
      4. Delegates to ``spec_cmd.main``.
    """
    import resume_cmd

    _setup_repo(tmp_path)
    _seed_plugin_local(tmp_path)
    _seed_state(tmp_path)
    pending = _write_pending_marker(tmp_path, context="checkpoint2")

    monkeypatch.setattr(resume_cmd, "_recheck_environment", lambda root: None)

    calls = {"prompt_user": 0, "apply_decision": 0, "spec_cmd": 0, "pre_merge_cmd": 0}

    def fake_prompt_user(ctx, options, *, non_interactive=False, project_root=None):
        from escalation_prompt import UserDecision

        calls["prompt_user"] += 1
        return UserDecision(chosen_option="a", action="override", reason="test")

    def fake_apply_decision(decision, ctx, project_root):
        calls["apply_decision"] += 1
        return 0

    def fake_delegate(module_name: str, root: Path, extra: list[str]) -> int:
        calls[module_name] = calls.get(module_name, 0) + 1
        return 0

    # Patch the escalation_prompt symbols where resume_cmd imports them.
    import escalation_prompt as ep

    monkeypatch.setattr(ep, "prompt_user", fake_prompt_user)
    monkeypatch.setattr(ep, "apply_decision", fake_apply_decision)
    monkeypatch.setattr(resume_cmd, "_delegate", fake_delegate)

    rc = resume_cmd.main(["--project-root", str(tmp_path)])
    assert rc == 0
    assert calls["prompt_user"] == 1
    assert calls["apply_decision"] == 1
    assert calls["spec_cmd"] == 1
    assert calls["pre_merge_cmd"] == 0
    assert not pending.exists(), "marker must be removed after recovery flow completes"


def test_resume_main_reprompts_and_delegates_to_pre_merge_for_pre_merge_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``context == "pre-merge"`` → delegates to ``pre_merge_cmd``."""
    import resume_cmd

    _setup_repo(tmp_path)
    _seed_plugin_local(tmp_path)
    _seed_state(tmp_path)
    pending = _write_pending_marker(tmp_path, context="pre-merge")

    monkeypatch.setattr(resume_cmd, "_recheck_environment", lambda root: None)

    calls = {"spec_cmd": 0, "pre_merge_cmd": 0}

    def fake_prompt_user(ctx, options, *, non_interactive=False, project_root=None):
        from escalation_prompt import UserDecision

        return UserDecision(chosen_option="d", action="abandon", reason="test")

    def fake_apply_decision(decision, ctx, project_root):
        return 8  # abandon

    def fake_delegate(module_name: str, root: Path, extra: list[str]) -> int:
        calls[module_name] = calls.get(module_name, 0) + 1
        return 0

    import escalation_prompt as ep

    monkeypatch.setattr(ep, "prompt_user", fake_prompt_user)
    monkeypatch.setattr(ep, "apply_decision", fake_apply_decision)
    monkeypatch.setattr(resume_cmd, "_delegate", fake_delegate)

    rc = resume_cmd.main(["--project-root", str(tmp_path)])
    # abandon path returns 8 (matches Feature A v0.1 behavior semantics);
    # either way, delegation to pre_merge_cmd must NOT happen after abandon.
    assert rc == 8
    assert calls["pre_merge_cmd"] == 0
    assert calls["spec_cmd"] == 0
    # Marker is cleaned up regardless of decision outcome.
    assert not pending.exists()


def test_resume_main_dry_run_does_not_consume_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--dry-run`` prints what would happen but leaves the marker in place."""
    import resume_cmd

    _setup_repo(tmp_path)
    _seed_plugin_local(tmp_path)
    _seed_state(tmp_path)
    pending = _write_pending_marker(tmp_path, context="checkpoint2")

    monkeypatch.setattr(resume_cmd, "_recheck_environment", lambda root: None)

    def should_not_run(*a, **kw):
        raise AssertionError("prompt_user must not be invoked under --dry-run")

    import escalation_prompt as ep

    monkeypatch.setattr(ep, "prompt_user", should_not_run)

    rc = resume_cmd.main(["--project-root", str(tmp_path), "--dry-run"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "magi-escalation-pending" in out or "escalation" in out.lower()
    assert pending.exists(), "dry-run must not delete the marker"
