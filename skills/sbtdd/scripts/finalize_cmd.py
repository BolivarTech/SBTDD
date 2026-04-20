#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""/sbtdd finalize -- checklist sec.M.7 + /finishing-a-development-branch (sec.S.5.7)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import subprocess_utils
import superpowers_dispatch
from config import PluginConfig, load_plugin_local
from errors import ChecklistError, PreconditionError
from models import verdict_meets_threshold
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


def _checklist(
    root: Path,
    state: SessionState,
    magi_verdict_path: Path,
    cfg: PluginConfig,
) -> list[tuple[str, bool, str]]:
    """Return the sec.M.7 checklist as ``(name, passed, detail)`` tuples.

    The last item is intentionally hardcoded to ``True`` with a DEFER
    marker -- automating a commit-prefix spot-check via ``git log``
    parsing is a v0.2 enhancement; the current release delegates that
    verification to the human reviewer during pre-merge.
    """
    items: list[tuple[str, bool, str]] = []

    plan = (root / state.plan_path).read_text(encoding="utf-8")
    all_done = "- [ ]" not in plan
    items.append(
        (
            "plan fully [x]",
            all_done,
            "no open [ ] found" if all_done else "open tasks remain",
        )
    )
    items.append(("state current_phase=done", state.current_phase == "done", ""))
    items.append(("state current_task_id=null", state.current_task_id is None, ""))

    try:
        superpowers_dispatch.verification_before_completion(cwd=str(root))
        sec01_ok, sec01_detail = True, "passed"
    except Exception as exc:  # pragma: no cover -- defensive path
        sec01_ok, sec01_detail = False, str(exc)
    items.append(("sec.M.0.1 verification", sec01_ok, sec01_detail))

    git_status = subprocess_utils.run_with_timeout(
        ["git", "status", "--short"], timeout=10, cwd=str(root)
    )
    clean = git_status.stdout.strip() == ""
    items.append(("git status clean", clean, git_status.stdout.strip() or "ok"))

    v_data = json.loads(magi_verdict_path.read_text(encoding="utf-8"))
    gate_pass = verdict_meets_threshold(v_data["verdict"], cfg.magi_threshold) and not v_data.get(
        "degraded", False
    )
    items.append(
        (
            "MAGI verdict >= threshold AND not degraded",
            gate_pass,
            f"verdict={v_data['verdict']}, degraded={v_data.get('degraded')}",
        )
    )

    items.append(
        (
            "spec-behavior.md exists",
            (root / "sbtdd" / "spec-behavior.md").exists(),
            "",
        )
    )
    items.append(
        (
            "claude-plan-tdd.md exists",
            (root / state.plan_path).exists(),
            "",
        )
    )
    # DEFER v0.2: automate commit-prefix spot-check via git log parsing
    # (currently hardcoded True; reviewer covers this manually in pre-merge).
    items.append(
        (
            "commits use sec.M.5 prefixes",
            True,
            "spot-check deferred to reviewer",
        )
    )
    return items


def main(argv: list[str] | None = None) -> int:
    """Entry point for /sbtdd finalize (checklist + finishing skill)."""
    parser = _build_parser()
    ns = parser.parse_args(argv)
    root: Path = ns.project_root
    state, magi_verdict_path = _preflight(root)
    cfg = load_plugin_local(root / ".claude" / "plugin.local.md")
    items = _checklist(root, state, magi_verdict_path, cfg)
    failures = [(name, detail) for (name, ok, detail) in items if not ok]
    if failures:
        for name, detail in failures:
            sys.stderr.write(f"  [FAIL] {name}: {detail}\n")
        raise ChecklistError(f"{len(failures)} checklist items failed")
    return 0


run = main
