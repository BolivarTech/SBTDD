#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-24
"""/sbtdd review-spec-compliance <task-id> — manual spec-reviewer dispatch (Feature B, H7).

Exposes :func:`spec_review_dispatch.dispatch_spec_reviewer` as a user-facing
subcommand for ``executing-plans`` / ad-hoc flows where the ``auto_cmd``
per-task gate does not run. The subcommand:

* Reads ``.claude/session-state.json`` to resolve the approved plan path and
  accepts ``--project-root`` (default :func:`pathlib.Path.cwd`).
* Delegates to :func:`spec_review_dispatch.dispatch_spec_reviewer` with the
  resolved task id, plan path, and project root.
* Returns ``0`` on approval.
* Returns ``12`` (``SPEC_REVIEW_ISSUES``) when the dispatcher returns a
  non-approved :class:`SpecReviewResult` without raising — the
  ``max_iterations=1`` defensive path where issues surface without retry.
* Lets :class:`SpecReviewError` propagate so ``run_sbtdd.main`` maps it via
  :data:`errors.EXIT_CODES` (also exit 12, carrying the safety-valve context).
* Raises :class:`PreconditionError` when the state file or the plan file is
  missing (maps to exit 2 via ``run_sbtdd``).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import spec_review_dispatch
from errors import PreconditionError
from state_file import load as load_state


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sbtdd review-spec-compliance",
        description="Dispatch the spec-reviewer for one task (manual mode).",
    )
    p.add_argument("task_id", help="Plan task id to review (e.g. '3', 'H7').")
    p.add_argument("--project-root", type=Path, default=Path.cwd())
    p.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Reviewer safety valve cap (default: 3).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    """Parse argv, resolve paths, dispatch the reviewer, map its result to an exit code."""
    ns = _build_parser().parse_args(argv)
    root: Path = ns.project_root
    state_path = root / ".claude" / "session-state.json"
    if not state_path.is_file():
        raise PreconditionError(f"state file not found: {state_path}")
    state = load_state(state_path)
    plan_path = root / state.plan_path
    if not plan_path.is_file():
        raise PreconditionError(f"plan file not found: {plan_path}")
    result = spec_review_dispatch.dispatch_spec_reviewer(
        task_id=ns.task_id,
        plan_path=plan_path,
        repo_root=root,
        max_iterations=ns.max_iterations,
    )
    if result.approved:
        return 0
    for issue in result.issues:
        sys.stderr.write(f"[{issue.severity}] {issue.text}\n")
    return 12


run = main
