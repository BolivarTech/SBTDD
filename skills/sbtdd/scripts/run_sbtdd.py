#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""sbtdd-workflow single entrypoint (sec.S.2.3, sec.S.5, sec.S.11.1-11.2).

Invoked as ``python run_sbtdd.py <subcommand> [args...]`` from the skill.
Validates the subcommand name against :data:`models.VALID_SUBCOMMANDS`,
then dispatches to the matching ``{subcommand}_cmd.main`` function.

Exit codes are derived from :data:`errors.EXIT_CODES` via an MRO walk --
unregistered :class:`errors.SBTDDError` subclasses inherit the closest
registered ancestor's code, falling through to exit 1 only when no
ancestor is registered (MAGI Loop 2 Milestone B iter 1 Finding 1).
``KeyboardInterrupt`` becomes exit 130 (sec.S.11.3). All other uncaught
exceptions surface with traceback and exit 1 (bug report channel per
sec.S.11.2).

In Milestone C, all 9 entries point to the real subcomando implementations.
"""

from __future__ import annotations

import sys
from typing import Callable, MutableMapping

import auto_cmd
import close_phase_cmd
import close_task_cmd
import finalize_cmd
import init_cmd
import pre_merge_cmd
import resume_cmd
import spec_cmd
import status_cmd
from errors import EXIT_CODES, SBTDDError
from models import VALID_SUBCOMMANDS

#: Handler signature: consumes the subcommand's argv tail and returns an exit code.
SubcommandHandler = Callable[[list[str]], int]

#: Subcommand name -> handler. All 9 entries point to the real
#: ``{subcommand}_cmd.main`` functions as of Milestone C.
SUBCOMMAND_DISPATCH: MutableMapping[str, SubcommandHandler] = {
    "init": init_cmd.main,
    "spec": spec_cmd.main,
    "close-phase": close_phase_cmd.main,
    "close-task": close_task_cmd.main,
    "status": status_cmd.main,
    "pre-merge": pre_merge_cmd.main,
    "finalize": finalize_cmd.main,
    "auto": auto_cmd.main,
    "resume": resume_cmd.main,
}


def _print_usage() -> None:
    sys.stderr.write(
        "usage: run_sbtdd.py <subcommand> [args...]\n"
        f"  subcommands: {', '.join(VALID_SUBCOMMANDS)}\n"
    )


def _exit_code_for(exc: SBTDDError) -> int:
    """Walk ``type(exc).__mro__`` and return the first registered exit code.

    Direct ``type(exc)`` lookup misses SBTDDError subclasses that are not
    themselves registered (eg. future ``GitCommitError(CommitError)`` or
    ``DerivedDriftError(DriftError)``), silently falling back to exit 1
    and erasing the ancestor's semantics. Walking the MRO returns the
    closest registered ancestor instead, preserving the taxonomy as the
    hierarchy grows (MAGI Loop 2 Milestone B iter 1, Finding 1).
    """
    for cls in type(exc).__mro__:
        if cls in EXIT_CODES:
            return EXIT_CODES[cls]
    return 1


def main(argv: list[str] | None = None) -> int:
    """Parse argv, dispatch to the matching subcommand, map exceptions to codes.

    Args:
        argv: Tokens after the program name. When ``None`` uses ``sys.argv[1:]``.

    Returns:
        Exit code per sec.S.11.1 taxonomy.
    """
    tokens = list(sys.argv[1:]) if argv is None else list(argv)
    if not tokens:
        _print_usage()
        return 1
    name, rest = tokens[0], tokens[1:]
    if name not in SUBCOMMAND_DISPATCH:
        sys.stderr.write(f"unknown subcommand: '{name}'\n")
        _print_usage()
        return 1
    handler = SUBCOMMAND_DISPATCH[name]
    try:
        return handler(rest)
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted by user (SIGINT). Exiting.\n")
        return 130
    except SBTDDError as exc:
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        return _exit_code_for(exc)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
