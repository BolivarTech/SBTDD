# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-24
"""Tests for /sbtdd review-spec-compliance <task-id> subcommand (Feature B, H7).

v0.2 Feature B, Task H7: exposes ``spec_review_dispatch.dispatch_spec_reviewer``
as a manual subcommand for ``executing-plans`` / ad-hoc flows. The subcommand:

* Reads ``.claude/session-state.json`` to resolve ``plan_path`` and accepts
  ``--project-root`` (defaults to ``Path.cwd()``).
* Delegates to :func:`spec_review_dispatch.dispatch_spec_reviewer` with the
  resolved task id, plan path, and project root.
* Returns ``0`` on approval; ``12`` when the dispatcher returns a non-approved
  :class:`SpecReviewResult` without raising (defensive path: ``max_iterations=1``
  scenarios where issues are reported without retry).
* Surfaces :class:`PreconditionError` when the state file or plan file is
  missing — exit-code mapping to ``2`` happens at ``run_sbtdd.main``.

Tests use :class:`tests.fixtures.skill_stubs.StubSpecReviewer` and
``monkeypatch.setattr`` per the conftest.py test-isolation policy.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from tests.fixtures.skill_stubs import StubSpecReviewer


def _seed_state(
    tmp_path: Path,
    *,
    current_task_id: str = "2",
    current_task_title: str = "Second task (in-progress)",
    current_phase: str = "refactor",
) -> None:
    """Seed ``.claude/session-state.json`` + the three-tasks-mixed plan fixture."""
    claude = tmp_path / ".claude"
    claude.mkdir()
    planning = tmp_path / "planning"
    planning.mkdir()
    fixtures_root = Path(__file__).parent / "fixtures"
    shutil.copy(
        fixtures_root / "plans" / "three-tasks-mixed.md",
        planning / "claude-plan-tdd.md",
    )
    payload = {
        "plan_path": "planning/claude-plan-tdd.md",
        "current_task_id": current_task_id,
        "current_task_title": current_task_title,
        "current_phase": current_phase,
        "phase_started_at_commit": "abc1234",
        "last_verification_at": None,
        "last_verification_result": None,
        "plan_approved_at": "2026-04-24T10:00:00Z",
    }
    (claude / "session-state.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_review_spec_compliance_module_is_importable() -> None:
    """H7 contract: the cmd module is importable under its conventional name."""
    import review_spec_compliance_cmd  # type: ignore[import-not-found]  # noqa: F401


def test_review_spec_compliance_main_alias_exists() -> None:
    """H7 contract: module exposes both ``main`` and ``run`` (``run = main``)."""
    import review_spec_compliance_cmd  # type: ignore[import-not-found]

    assert callable(review_spec_compliance_cmd.main)
    assert review_spec_compliance_cmd.run is review_spec_compliance_cmd.main


def test_review_spec_compliance_approved_exits_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Approved dispatch => cmd.main returns 0 and does NOT print to stderr."""
    import review_spec_compliance_cmd  # type: ignore[import-not-found]
    import spec_review_dispatch

    _seed_state(tmp_path)
    stub = StubSpecReviewer(sequence=[True])
    monkeypatch.setattr(
        spec_review_dispatch,
        "dispatch_spec_reviewer",
        stub.dispatch_spec_reviewer,
    )

    code = review_spec_compliance_cmd.main(["--project-root", str(tmp_path), "3"])

    assert code == 0
    assert len(stub.calls) == 1
    assert stub.calls[0]["task_id"] == "3"


def test_review_spec_compliance_issues_exits_12(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-approved SpecReviewResult (max_iterations=1) => cmd.main returns 12."""
    import review_spec_compliance_cmd  # type: ignore[import-not-found]
    import spec_review_dispatch
    from spec_review_dispatch import SpecIssue, SpecReviewResult

    _seed_state(tmp_path)

    def fake_dispatch(**kwargs: Any) -> SpecReviewResult:  # type: ignore[no-untyped-def]
        return SpecReviewResult(
            approved=False,
            issues=(SpecIssue(severity="MISSING", text="scenario 4 not covered"),),
            reviewer_iter=1,
            artifact_path=None,
        )

    monkeypatch.setattr(spec_review_dispatch, "dispatch_spec_reviewer", fake_dispatch)

    code = review_spec_compliance_cmd.main(
        ["--project-root", str(tmp_path), "--max-iterations", "1", "3"]
    )

    assert code == 12


def test_review_spec_compliance_forwards_task_id_and_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Positional task id + resolved plan path + repo root pass through to dispatch."""
    import review_spec_compliance_cmd  # type: ignore[import-not-found]
    import spec_review_dispatch
    from spec_review_dispatch import SpecReviewResult

    _seed_state(tmp_path)
    observed: dict[str, Any] = {}

    def fake_dispatch(
        *,
        task_id: str,
        plan_path: Path,
        repo_root: Path,
        max_iterations: int = 3,
        timeout: int = 900,
    ) -> SpecReviewResult:
        observed["task_id"] = task_id
        observed["plan_path"] = plan_path
        observed["repo_root"] = repo_root
        observed["max_iterations"] = max_iterations
        return SpecReviewResult(approved=True, issues=(), reviewer_iter=1, artifact_path=None)

    monkeypatch.setattr(spec_review_dispatch, "dispatch_spec_reviewer", fake_dispatch)

    code = review_spec_compliance_cmd.main(["--project-root", str(tmp_path), "2"])

    assert code == 0
    assert observed["task_id"] == "2"
    assert Path(observed["plan_path"]) == tmp_path / "planning" / "claude-plan-tdd.md"
    assert Path(observed["repo_root"]) == tmp_path
    assert observed["max_iterations"] == 3


def test_review_spec_compliance_missing_state_file_raises_precondition(
    tmp_path: Path,
) -> None:
    """No ``.claude/session-state.json`` => PreconditionError (exit 2 via run_sbtdd)."""
    import review_spec_compliance_cmd  # type: ignore[import-not-found]
    from errors import PreconditionError

    with pytest.raises(PreconditionError):
        review_spec_compliance_cmd.main(["--project-root", str(tmp_path), "3"])


def test_review_spec_compliance_missing_plan_file_raises_precondition(
    tmp_path: Path,
) -> None:
    """State file exists but the referenced plan is missing => PreconditionError."""
    import review_spec_compliance_cmd  # type: ignore[import-not-found]
    from errors import PreconditionError

    claude = tmp_path / ".claude"
    claude.mkdir()
    payload = {
        "plan_path": "planning/missing-plan.md",
        "current_task_id": "2",
        "current_task_title": "Task 2",
        "current_phase": "refactor",
        "phase_started_at_commit": "abc1234",
        "last_verification_at": None,
        "last_verification_result": None,
        "plan_approved_at": "2026-04-24T10:00:00Z",
    }
    (claude / "session-state.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with pytest.raises(PreconditionError):
        review_spec_compliance_cmd.main(["--project-root", str(tmp_path), "3"])


def test_review_spec_compliance_spec_review_error_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Safety-valve exhaustion inside dispatch => SpecReviewError bubbles up.

    Exit-code mapping to 12 happens at ``run_sbtdd.main`` (see
    ``tests/test_run_sbtdd.py``). The cmd itself does not swallow the
    exception — let the dispatcher decide.
    """
    import review_spec_compliance_cmd  # type: ignore[import-not-found]
    import spec_review_dispatch
    from errors import SpecReviewError

    _seed_state(tmp_path)

    def failing_dispatch(**kwargs: Any) -> None:
        raise SpecReviewError(
            "spec-reviewer safety valve exhausted for task 3",
            task_id="3",
            iteration=3,
            issues=("stub finding",),
        )

    monkeypatch.setattr(spec_review_dispatch, "dispatch_spec_reviewer", failing_dispatch)

    with pytest.raises(SpecReviewError):
        review_spec_compliance_cmd.main(["--project-root", str(tmp_path), "3"])


def test_review_spec_compliance_help_mentions_task_id_argument(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--help` surfaces the positional ``task_id`` argument (usability guard)."""
    import review_spec_compliance_cmd  # type: ignore[import-not-found]

    with pytest.raises(SystemExit) as ei:
        review_spec_compliance_cmd.main(["--help"])
    assert ei.value.code == 0
    out = capsys.readouterr().out
    assert "task_id" in out or "task-id" in out


def test_review_spec_compliance_issue_text_surfaces_on_stderr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exit-12 path writes each issue severity + text to stderr for operator triage."""
    import review_spec_compliance_cmd  # type: ignore[import-not-found]
    import spec_review_dispatch
    from spec_review_dispatch import SpecIssue, SpecReviewResult

    _seed_state(tmp_path)

    def fake_dispatch(**kwargs: Any) -> SpecReviewResult:  # type: ignore[no-untyped-def]
        return SpecReviewResult(
            approved=False,
            issues=(
                SpecIssue(severity="MISSING", text="scenario 4 not covered"),
                SpecIssue(severity="EXTRA", text="unused helper introduced"),
            ),
            reviewer_iter=1,
            artifact_path=None,
        )

    monkeypatch.setattr(spec_review_dispatch, "dispatch_spec_reviewer", fake_dispatch)

    review_spec_compliance_cmd.main(["--project-root", str(tmp_path), "--max-iterations", "1", "3"])

    err = capsys.readouterr().err
    assert "MISSING" in err
    assert "scenario 4 not covered" in err
    assert "EXTRA" in err
    assert "unused helper introduced" in err
