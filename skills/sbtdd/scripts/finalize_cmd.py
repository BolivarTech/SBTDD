#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""/sbtdd finalize -- checklist sec.M.7 + /finishing-a-development-branch (sec.S.5.7)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from errors import PreconditionError
from state_file import SessionState
from state_file import load as load_state


def _verdict_is_stale(state: SessionState, magi_verdict_path: Path) -> bool:
    """Return True iff the verdict artifact predates ``plan_approved_at``.

    Used by :func:`_preflight` to reject verdicts that belong to a
    previous feature's ``pre-merge`` run (state file advanced, new plan
    approved, but stale ``magi-verdict.json`` still on disk).
    """
    data = json.loads(magi_verdict_path.read_text(encoding="utf-8"))
    ts = data.get("timestamp")
    if not ts or not state.plan_approved_at:
        return False
    return bool(ts < state.plan_approved_at)


def _build_parser() -> argparse.ArgumentParser:
    """Return the argparse parser for ``sbtdd finalize``."""
    p = argparse.ArgumentParser(prog="sbtdd finalize")
    p.add_argument("--project-root", type=Path, default=Path.cwd())
    return p


def _preflight(root: Path) -> tuple[SessionState, Path]:
    """Verify preconditions for /sbtdd finalize.

    Preconditions (sec.S.5.7):
      - ``.claude/session-state.json`` exists and ``current_phase == 'done'``.
      - ``.claude/magi-verdict.json`` exists (pre-merge was run).

    Args:
        root: Project root directory.

    Returns:
        A tuple of ``(SessionState, magi_verdict_path)``.

    Raises:
        PreconditionError: Missing state file, ``current_phase != done``,
            or missing ``magi-verdict.json``.
    """
    state_path = root / ".claude" / "session-state.json"
    if not state_path.exists():
        raise PreconditionError(f"state file not found: {state_path}")
    state = load_state(state_path)
    if state.current_phase != "done":
        raise PreconditionError(
            f"finalize requires current_phase='done', got '{state.current_phase}'"
        )
    magi_verdict = root / ".claude" / "magi-verdict.json"
    if not magi_verdict.exists():
        raise PreconditionError(
            f"magi-verdict.json not found: {magi_verdict}. Run /sbtdd pre-merge first."
        )
    if _verdict_is_stale(state, magi_verdict):
        data = json.loads(magi_verdict.read_text(encoding="utf-8"))
        raise PreconditionError(
            f"magi-verdict.json (timestamp={data.get('timestamp')}) predates "
            f"plan_approved_at={state.plan_approved_at} -- belongs to previous "
            f"feature. Run /sbtdd pre-merge for the current feature."
        )
    return state, magi_verdict


def main(argv: list[str] | None = None) -> int:
    """Entry point for /sbtdd finalize (scaffold, preconditions only)."""
    parser = _build_parser()
    ns = parser.parse_args(argv)
    _preflight(ns.project_root)
    return 0


run = main
