# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-25
"""Tests for v0.2.1 B6 auto-feedback loop in ``auto_cmd._phase2_task_loop``.

Spec-base §2.2 promised that on spec-reviewer ``issues`` the loop routes
through ``/receiving-code-review`` + a mini-cycle TDD fix
(``test:`` -> ``fix:`` -> ``refactor:``) per accepted finding + a
re-dispatch of the reviewer up to a 3-iter outer safety valve. v0.2.0
shipped the scope-relaxed version (``SpecReviewError`` raises immediately).
v0.2.1 lands the full feedback loop; these tests pin the new behavior.

Test taxonomy:

* Accepted finding -> mini-cycle dispatched -> 3 commits land -> re-dispatch
  approves -> task closes.
* Rejected finding -> no mini-cycle -> re-dispatch with feedback context ->
  eventually approves OR exhausts.
* Outer safety valve exhausts -> SpecReviewError raised with rejected
  history.
* ``--skip-spec-review`` flag bypasses the new helper entirely (v0.2 path).
* Mini-cycle commits use ``test:`` / ``fix:`` / ``refactor:`` prefixes
  (per ``commits.create`` validation).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Shared environment seeding (parallel to ``test_auto_cmd_spec_review.py``).
# ---------------------------------------------------------------------------


def _seed_plugin_local(tmp_path: Path) -> None:
    import shutil

    (tmp_path / ".claude").mkdir(exist_ok=True)
    fixture = Path(__file__).parent / "fixtures" / "plugin-locals" / "valid-python.md"
    shutil.copy(fixture, tmp_path / ".claude" / "plugin.local.md")


def _seed_state(
    tmp_path: Path,
    *,
    current_phase: str = "red",
    current_task_id: str | None = "1",
    current_task_title: str | None = "First task",
    plan_approved_at: str | None = "2026-04-20T03:30:00Z",
) -> Path:
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


def _setup_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True, capture_output=True)
    for cfg in (
        ("user.email", "tester@example.com"),
        ("user.name", "Tester"),
        ("commit.gpgsign", "false"),
    ):
        subprocess.run(["git", "config", *cfg], cwd=str(tmp_path), check=True, capture_output=True)
    (tmp_path / "README.md").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: initial"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )


def _seed_plan(tmp_path: Path, task_count: int) -> Path:
    planning = tmp_path / "planning"
    planning.mkdir(parents=True, exist_ok=True)
    plan = planning / "claude-plan-tdd.md"
    body = "# Plan\n\n"
    for i in range(1, task_count + 1):
        body += f"### Task {i}: Task {i} title\n- [ ] step 1\n\n"
    plan.write_text(body, encoding="utf-8")
    return plan


def _seed_auto_env(
    tmp_path: Path,
    *,
    task_count: int = 1,
    task_id: str = "1",
    current_phase: str = "red",
) -> None:
    _setup_git_repo(tmp_path)
    _seed_plugin_local(tmp_path)
    _seed_plan(tmp_path, task_count)
    _seed_state(
        tmp_path,
        current_phase=current_phase,
        current_task_id=task_id,
        current_task_title=f"Task {task_id} title",
    )


def _install_auto_loop_patches(
    monkeypatch: pytest.MonkeyPatch,
    auto_cmd_mod: Any,
    superpowers_dispatch_mod: Any,
) -> None:
    """Patch noisy dependencies so tests focus on the feedback loop."""
    monkeypatch.setattr(
        superpowers_dispatch_mod,
        "test_driven_development",
        lambda **kw: None,
        raising=False,
    )
    monkeypatch.setattr(
        superpowers_dispatch_mod,
        "verification_before_completion",
        lambda **kw: None,
        raising=False,
    )
    monkeypatch.setattr(
        superpowers_dispatch_mod,
        "systematic_debugging",
        lambda **kw: None,
        raising=False,
    )
    monkeypatch.setattr(auto_cmd_mod, "detect_drift", lambda *a, **kw: None, raising=False)


# ---------------------------------------------------------------------------
# Happy path -- accepted finding -> mini-cycle -> re-dispatch approves.
# ---------------------------------------------------------------------------


def test_b6_accepted_finding_runs_mini_cycle_and_re_dispatches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reviewer raises issues, /receiving-code-review accepts one, mini-cycle
    runs (3 commits), re-dispatch approves -> task closes.
    """
    import auto_cmd
    import spec_review_dispatch
    import superpowers_dispatch
    from config import load_plugin_local
    from errors import SpecReviewError
    from spec_review_dispatch import SpecReviewResult
    from state_file import load as load_state

    _seed_auto_env(tmp_path, task_count=1, task_id="1", current_phase="red")
    cfg = load_plugin_local(tmp_path / ".claude" / "plugin.local.md")
    _install_auto_loop_patches(monkeypatch, auto_cmd, superpowers_dispatch)

    # Reviewer dispatch sequence:
    #   call 1 -> issues (one MISSING finding)
    #   call 2 -> approved (mini-cycle resolved the finding)
    dispatch_calls = {"n": 0}

    def fake_dispatch(**kwargs: Any) -> SpecReviewResult:
        dispatch_calls["n"] += 1
        if dispatch_calls["n"] == 1:
            raise SpecReviewError(
                "stub reviewer raised issues",
                task_id=kwargs["task_id"],
                iteration=1,
                issues=("Scenario X not covered",),
            )
        return SpecReviewResult(approved=True, issues=(), reviewer_iter=1, artifact_path=None)

    monkeypatch.setattr(spec_review_dispatch, "dispatch_spec_reviewer", fake_dispatch)

    # /receiving-code-review accepts the lone finding.
    accepted_findings: list[str] = ["Scenario X not covered"]

    def fake_receiving_review(**kwargs: Any) -> Any:
        class R:
            stdout = f"## Accepted\n- {accepted_findings[0]}\n## Rejected\n"

        return R()

    monkeypatch.setattr(
        superpowers_dispatch, "receiving_code_review", fake_receiving_review, raising=False
    )

    # Track mini-cycle: each mini-cycle phase invokes test_driven_development
    # then commits via commits.create. We need the commit subjects to verify
    # prefixes were correct.
    commits_log: list[tuple[str, str]] = []
    import commits as commits_mod

    real_create = commits_mod.create

    def spy_create(prefix: str, message: str, cwd: str | None = None) -> str:
        commits_log.append((prefix, message))
        return real_create(prefix, message, cwd=cwd)

    monkeypatch.setattr(commits_mod, "create", spy_create)

    # The mini-cycle helper invokes test_driven_development for each phase.
    # In a real flow the implementer subagent edits files and commits;
    # here the noisy patch above neuters test_driven_development. We must
    # provide enough scaffolding for commits.create to find a stage-able
    # change. Approach: patch the mini-cycle helper to write a stub file
    # before each commit so ``git commit`` succeeds.
    cycle_phase_calls: list[str] = []

    real_tdd = superpowers_dispatch.test_driven_development

    def fake_tdd(**kwargs: Any) -> Any:
        # Extract the phase from args=[f"--phase=red", ...] or marker text.
        args = kwargs.get("args") or []
        phase_arg = next((a for a in args if a.startswith("--phase=")), "")
        phase = phase_arg.split("=", 1)[1] if phase_arg else "unknown"
        cycle_phase_calls.append(phase)
        # Create a stub file change so commits.create has work to commit.
        stub = tmp_path / f"b6_stub_{len(cycle_phase_calls)}.txt"
        stub.write_text(f"phase {phase} pass {len(cycle_phase_calls)}\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", str(stub)],
            cwd=str(tmp_path),
            check=True,
            capture_output=True,
        )
        return real_tdd

    monkeypatch.setattr(superpowers_dispatch, "test_driven_development", fake_tdd, raising=False)

    ns = auto_cmd._build_parser().parse_args(["--project-root", str(tmp_path)])
    state = load_state(tmp_path / ".claude" / "session-state.json")
    final = auto_cmd._phase2_task_loop(ns, state, cfg)

    # Task closed.
    assert final.current_phase == "done"
    assert final.current_task_id is None
    # Reviewer dispatched twice: initial + post-mini-cycle.
    assert dispatch_calls["n"] == 2
    # Mini-cycle ran for one accepted finding -> 3 phases (red/green/refactor).
    mini_cycle_phases = [p for p in cycle_phase_calls if p in {"red", "green", "refactor"}]
    # The first three task-loop calls (red/green/refactor of the task itself)
    # plus the mini-cycle three -> at least 6.
    assert len(mini_cycle_phases) >= 6, (
        f"expected the task's 3 phases + mini-cycle 3 phases, got {cycle_phase_calls}"
    )
    # Commit prefixes recorded by commits.create include test/fix/refactor
    # for the mini-cycle (commits.create is invoked once per phase commit).
    prefixes = [p for (p, _msg) in commits_log]
    # Mini-cycle commits MUST follow test->fix->refactor sequence.
    test_idx = [i for i, p in enumerate(prefixes) if p == "test"]
    fix_idx = [i for i, p in enumerate(prefixes) if p == "fix"]
    refactor_idx = [i for i, p in enumerate(prefixes) if p == "refactor"]
    # At least one of each prefix from the mini-cycle.
    assert test_idx, f"no test: commits in {prefixes}"
    assert fix_idx, f"no fix: commits in {prefixes}"
    assert refactor_idx, f"no refactor: commits in {prefixes}"
    # The fix index must be after at least one test index (mini-cycle order).
    assert min(fix_idx) > min(test_idx)


# ---------------------------------------------------------------------------
# All rejections -> no mini-cycle -> re-dispatch -> eventually approves.
# ---------------------------------------------------------------------------


def test_b6_all_rejected_findings_skip_mini_cycle_and_re_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reviewer issues + all rejected by /receiving-code-review -> no
    mini-cycle commits, re-dispatch reviewer until approved.
    """
    import auto_cmd
    import commits as commits_mod
    import spec_review_dispatch
    import superpowers_dispatch
    from config import load_plugin_local
    from errors import SpecReviewError
    from spec_review_dispatch import SpecReviewResult
    from state_file import load as load_state

    _seed_auto_env(tmp_path, task_count=1, task_id="1", current_phase="red")
    cfg = load_plugin_local(tmp_path / ".claude" / "plugin.local.md")
    _install_auto_loop_patches(monkeypatch, auto_cmd, superpowers_dispatch)

    dispatch_calls = {"n": 0}

    def fake_dispatch(**kwargs: Any) -> SpecReviewResult:
        dispatch_calls["n"] += 1
        if dispatch_calls["n"] == 1:
            raise SpecReviewError(
                "stub reviewer raised issues",
                task_id=kwargs["task_id"],
                iteration=1,
                issues=("Subjective concern A",),
            )
        return SpecReviewResult(approved=True, issues=(), reviewer_iter=1, artifact_path=None)

    monkeypatch.setattr(spec_review_dispatch, "dispatch_spec_reviewer", fake_dispatch)

    # All findings rejected -> no Accepted bullets in output.
    def fake_receiving_review(**kwargs: Any) -> Any:
        class R:
            stdout = (
                "## Accepted\n## Rejected\n- Subjective concern A (rationale: orthogonal to spec)\n"
            )

        return R()

    monkeypatch.setattr(
        superpowers_dispatch, "receiving_code_review", fake_receiving_review, raising=False
    )

    real_create = commits_mod.create
    mini_cycle_commits: list[str] = []

    def spy_create(prefix: str, message: str, cwd: str | None = None) -> str:
        # Track only commits with mini-cycle-like messages (referencing
        # the finding), not the task's own phase commits.
        if "Subjective concern" in message:
            mini_cycle_commits.append(prefix)
        return real_create(prefix, message, cwd=cwd)

    monkeypatch.setattr(commits_mod, "create", spy_create)

    ns = auto_cmd._build_parser().parse_args(["--project-root", str(tmp_path)])
    state = load_state(tmp_path / ".claude" / "session-state.json")
    final = auto_cmd._phase2_task_loop(ns, state, cfg)

    assert final.current_phase == "done"
    assert final.current_task_id is None
    # Reviewer re-dispatched after rejection.
    assert dispatch_calls["n"] == 2
    # NO mini-cycle commits because all findings were rejected.
    assert mini_cycle_commits == []


# ---------------------------------------------------------------------------
# Outer safety valve exhausts -> SpecReviewError raised.
# ---------------------------------------------------------------------------


def test_b6_outer_safety_valve_exhausts_after_three_iters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reviewer keeps raising issues that get rejected -> 3 outer iters
    burn -> SpecReviewError propagates.
    """
    import auto_cmd
    import spec_review_dispatch
    import superpowers_dispatch
    from config import load_plugin_local
    from errors import SpecReviewError
    from state_file import load as load_state

    _seed_auto_env(tmp_path, task_count=1, task_id="1", current_phase="red")
    cfg = load_plugin_local(tmp_path / ".claude" / "plugin.local.md")
    _install_auto_loop_patches(monkeypatch, auto_cmd, superpowers_dispatch)

    dispatch_calls = {"n": 0}

    def fake_dispatch(**kwargs: Any) -> Any:
        dispatch_calls["n"] += 1
        raise SpecReviewError(
            "stub reviewer raised issues",
            task_id=kwargs["task_id"],
            iteration=1,
            issues=("persistent finding",),
        )

    monkeypatch.setattr(spec_review_dispatch, "dispatch_spec_reviewer", fake_dispatch)

    # All rejected so no commits land.
    def fake_receiving_review(**kwargs: Any) -> Any:
        class R:
            stdout = "## Accepted\n## Rejected\n- persistent finding (rationale: subjective)\n"

        return R()

    monkeypatch.setattr(
        superpowers_dispatch, "receiving_code_review", fake_receiving_review, raising=False
    )

    ns = auto_cmd._build_parser().parse_args(["--project-root", str(tmp_path)])
    state = load_state(tmp_path / ".claude" / "session-state.json")

    with pytest.raises(SpecReviewError):
        auto_cmd._phase2_task_loop(ns, state, cfg)

    # Outer cap is _B6_MAX_FEEDBACK_ITERATIONS = 3 -> reviewer dispatched
    # 3 times before raising (initial + 2 retries).
    assert dispatch_calls["n"] == 3
    # Audit recorded the failure.
    audit = json.loads((tmp_path / ".claude" / "auto-run.json").read_text(encoding="utf-8"))
    assert audit["error"] == "SpecReviewError"


def test_b6_outer_max_feedback_iterations_constant_is_three() -> None:
    """The outer feedback-loop cap is fixed at 3 (mirrors INV-11 cadence)."""
    from auto_cmd import _B6_MAX_FEEDBACK_ITERATIONS  # type: ignore[import-not-found]

    assert _B6_MAX_FEEDBACK_ITERATIONS == 3


# ---------------------------------------------------------------------------
# Mini-cycle commits use correct prefixes per commits.create validation.
# ---------------------------------------------------------------------------


def test_b6_mini_cycle_uses_test_fix_refactor_prefixes_via_commits_create(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each accepted finding's mini-cycle commits MUST go through
    ``commits.create`` with prefixes ``test:``, ``fix:``, ``refactor:``
    in that order so prefix validation + English-only + no-AI guards
    fire.
    """
    import auto_cmd
    import commits as commits_mod
    import spec_review_dispatch
    import superpowers_dispatch
    from config import load_plugin_local
    from errors import SpecReviewError
    from spec_review_dispatch import SpecReviewResult
    from state_file import load as load_state

    _seed_auto_env(tmp_path, task_count=1, task_id="1", current_phase="red")
    cfg = load_plugin_local(tmp_path / ".claude" / "plugin.local.md")
    _install_auto_loop_patches(monkeypatch, auto_cmd, superpowers_dispatch)

    dispatch_calls = {"n": 0}

    def fake_dispatch(**kwargs: Any) -> SpecReviewResult:
        dispatch_calls["n"] += 1
        if dispatch_calls["n"] == 1:
            raise SpecReviewError(
                "stub",
                task_id=kwargs["task_id"],
                iteration=1,
                issues=("F1",),
            )
        return SpecReviewResult(approved=True, issues=(), reviewer_iter=1, artifact_path=None)

    monkeypatch.setattr(spec_review_dispatch, "dispatch_spec_reviewer", fake_dispatch)

    def fake_receiving_review(**kwargs: Any) -> Any:
        class R:
            stdout = "## Accepted\n- F1\n## Rejected\n"

        return R()

    monkeypatch.setattr(
        superpowers_dispatch, "receiving_code_review", fake_receiving_review, raising=False
    )

    # Stub test_driven_development to stage one file per call so commits.create
    # has stage-able content.
    call_idx = {"n": 0}

    def fake_tdd(**kwargs: Any) -> Any:
        call_idx["n"] += 1
        stub = tmp_path / f"b6_prefix_stub_{call_idx['n']}.txt"
        stub.write_text(f"pass {call_idx['n']}\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", str(stub)], cwd=str(tmp_path), check=True, capture_output=True
        )
        return None

    monkeypatch.setattr(superpowers_dispatch, "test_driven_development", fake_tdd, raising=False)

    real_create = commits_mod.create
    mini_cycle_prefix_log: list[str] = []

    def spy_create(prefix: str, message: str, cwd: str | None = None) -> str:
        if "F1" in message:
            mini_cycle_prefix_log.append(prefix)
        return real_create(prefix, message, cwd=cwd)

    monkeypatch.setattr(commits_mod, "create", spy_create)

    ns = auto_cmd._build_parser().parse_args(["--project-root", str(tmp_path)])
    state = load_state(tmp_path / ".claude" / "session-state.json")
    auto_cmd._phase2_task_loop(ns, state, cfg)

    assert mini_cycle_prefix_log == ["test", "fix", "refactor"], (
        f"expected mini-cycle prefixes test->fix->refactor, got {mini_cycle_prefix_log}"
    )
