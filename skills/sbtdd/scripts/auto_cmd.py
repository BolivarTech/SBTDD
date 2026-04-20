#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""/sbtdd auto -- shoot-and-forget full-cycle (sec.S.5.8, INV-22..26).

Five-phase flow:

1. Phase 1 -- pre-flight dependency check + state / plan_approved_at
   validation (Task 27).
2. Phase 2 -- sequential task loop with TDD cycles per task (Task 28).
3. Phase 3 -- pre-merge with elevated MAGI budget (Task 29).
4. Phase 4 -- sec.M.7 checklist validation (Task 30).
5. Phase 5 -- report + ``.claude/auto-run.json`` audit trail (Task 30).

Design invariants enforced here:

- **INV-22** (sequential only): never spawn parallel subprocesses.
- **INV-23** (TDD-Guard inviolable): never writes to
  ``.claude/settings.json`` (spied in Task 31 test).
- **INV-24** (conservative): verification retries exhaust -> exit 6.
- **INV-25** (branch-scoped): never invokes
  ``/finishing-a-development-branch`` -- leaves the branch clean for
  the user to merge/PR manually.
- **INV-26** (audit trail): writes ``.claude/auto-run.json`` with
  per-phase timestamps and verdict.

Dry-run short-circuits BEFORE any subprocess work (Finding 4) so a
preview works even when git / tdd-guard / plugins are unavailable.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config import PluginConfig, load_plugin_local
from dependency_check import check_environment
from errors import DependencyError, PreconditionError
from state_file import SessionState
from state_file import load as load_state


def _build_parser() -> argparse.ArgumentParser:
    """Return the argparse parser for ``sbtdd auto``."""
    p = argparse.ArgumentParser(prog="sbtdd auto")
    p.add_argument("--project-root", type=Path, default=Path.cwd())
    p.add_argument(
        "--plugins-root",
        type=Path,
        default=Path.home() / ".claude" / "plugins",
    )
    p.add_argument("--magi-max-iterations", type=int, default=None)
    p.add_argument("--magi-threshold", type=str, default=None)
    p.add_argument("--verification-retries", type=int, default=None)
    p.add_argument("--dry-run", action="store_true")
    return p


def _print_dry_run_preview(ns: argparse.Namespace) -> None:
    """Emit the dry-run plan without reading any subprocess/tool output.

    Keeps dry-run stdlib-only and side-effect-free so it works even
    when git/tdd-guard/plugins are unavailable.
    """
    sys.stdout.write(
        "/sbtdd auto --dry-run:\n"
        f"  project_root: {ns.project_root}\n"
        f"  magi_max_iterations (override): {ns.magi_max_iterations}\n"
        f"  magi_threshold (override): {ns.magi_threshold}\n"
        f"  verification_retries (override): {ns.verification_retries}\n"
        "  Would execute phases 1-5 sequentially (preflight, task loop,\n"
        "  pre-merge, checklist, report). No commits, no subprocess calls.\n"
    )


def _phase1_preflight(ns: argparse.Namespace) -> tuple[SessionState, PluginConfig]:
    """Run Phase 1 -- pre-flight dependency + state + plan_approved_at check.

    Precondition order (deterministic for the user):

    1. ``.claude/session-state.json`` exists (``PreconditionError`` otherwise).
    2. ``state.plan_approved_at`` is not ``None`` -- auto requires an
       approved plan so the "Excepcion bajo plan aprobado" from template
       sec.5 is in effect.
    3. All dependency checks green (Rust/Python/C++ toolchain, git,
       tdd-guard, superpowers + magi plugins). Failures are reported in
       full -- no short-circuit (INV-12 / sec.S.5.1.1).

    Args:
        ns: Parsed argparse namespace (provides ``project_root`` +
            ``plugins_root``).

    Returns:
        A tuple ``(SessionState, PluginConfig)`` consumed by the
        downstream phases.

    Raises:
        PreconditionError: Missing state file or ``plan_approved_at is None``.
        DependencyError: Any pre-flight check reported non-OK status.
    """
    root: Path = ns.project_root
    state_path = root / ".claude" / "session-state.json"
    if not state_path.exists():
        raise PreconditionError(f"state file not found: {state_path}")
    state = load_state(state_path)
    if state.plan_approved_at is None:
        raise PreconditionError(
            "plan_approved_at is null - run /sbtdd spec to approve a plan before /sbtdd auto"
        )
    cfg = load_plugin_local(root / ".claude" / "plugin.local.md")
    report = check_environment(cfg.stack, root, ns.plugins_root)
    if not report.ok():
        sys.stderr.write(report.format_report() + "\n")
        raise DependencyError(f"{len(report.failed())} pre-flight checks failed")
    return state, cfg


def main(argv: list[str] | None = None) -> int:
    """Entry point for /sbtdd auto (shoot-and-forget full-cycle)."""
    parser = _build_parser()
    ns = parser.parse_args(argv)
    # Dry-run short-circuit BEFORE any subprocess work (Finding 4). The
    # cheap parser.parse_args above does not touch the filesystem;
    # stopping here guarantees a preview never invokes preflight,
    # git, or plugin dispatchers.
    if ns.dry_run:
        _print_dry_run_preview(ns)
        return 0
    _phase1_preflight(ns)
    return 0


run = main
