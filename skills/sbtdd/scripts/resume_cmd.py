#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""/sbtdd resume -- diagnostic wrapper (sec.S.5.10, INV-30).

Recovery path for any SBTDD run interrupted by quota exhaustion, crash,
reboot, or explicit Ctrl+C. The state file + atomic commits form the
checkpoint chain; worst-case loss is uncommitted work in the current
phase only.

Flow (phases):

1. Phase 1 -- diagnostic read: state + git HEAD + working tree + runtime
   artifacts (auto-run.json, magi-verdict.json) are reported to stdout
   WITHOUT mutation.
2. Phase 2 -- dependency + drift re-check (same contract as init's
   pre-flight; runs before any delegation).
3. Phase 3 -- delegation decision tree. Based on state/phase/artifacts,
   choose the downstream subcommand (``auto_cmd`` / ``pre_merge_cmd`` /
   ``finalize_cmd``) or flag uncommitted-resolution.
4. Phase 4 -- uncommitted work resolution with INV-24 conservative
   default (CONTINUE preserves user work; ``--discard-uncommitted`` is
   the explicit escape valve; interactive `R`/`A` also available).

Default behaviour on uncommitted work: CONTINUE. Any destructive action
(git checkout + clean) requires either ``--discard-uncommitted`` or an
explicit ``R`` response in interactive mode.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from errors import PreconditionError


def _build_parser() -> argparse.ArgumentParser:
    """Return the argparse parser for ``sbtdd resume``."""
    p = argparse.ArgumentParser(prog="sbtdd resume")
    p.add_argument("--project-root", type=Path, default=Path.cwd())
    p.add_argument("--auto", action="store_true")
    p.add_argument("--discard-uncommitted", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    """Entry point for /sbtdd resume (diagnostic + delegation wrapper)."""
    parser = _build_parser()
    ns = parser.parse_args(argv)
    root: Path = ns.project_root
    plugin_local = root / ".claude" / "plugin.local.md"
    if not plugin_local.exists():
        raise PreconditionError(
            f"plugin.local.md not found at {plugin_local}. Run /sbtdd init first."
        )
    state_path = root / ".claude" / "session-state.json"
    if not state_path.exists():
        sys.stdout.write(
            "No active SBTDD session to resume.\n"
            "Project is in manual mode. Invoke /sbtdd spec to bootstrap a feature.\n"
        )
        return 0
    return 0


run = main
