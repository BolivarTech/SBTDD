#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""/sbtdd status - read-only report of state + git + plan + drift (sec.S.5.5).

Exit codes: 0 success, 1 state file corrupt (StateFileError), 3 drift detected.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sbtdd status",
        description="Read-only status report of active SBTDD session.",
    )
    p.add_argument("--project-root", type=Path, default=Path.cwd())
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    parser.parse_args(argv)
    return 0


run = main
