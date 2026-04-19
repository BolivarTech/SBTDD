#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Immutable registries for sbtdd-workflow plugin.

Single source of truth for commit prefixes, MAGI verdict ranks, and the
list of valid subcommand names. All registries are exposed as
MappingProxyType or tuple to prevent runtime mutation (sec.S.8.5).
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

_COMMIT_PREFIX_MAP_MUTABLE: dict[str, str] = {
    "red": "test",
    "green_feat": "feat",
    "green_fix": "fix",
    "refactor": "refactor",
    "task_close": "chore",
}

#: Read-only TDD phase → git commit prefix mapping (sec.M.5).
COMMIT_PREFIX_MAP: Mapping[str, str] = MappingProxyType(_COMMIT_PREFIX_MAP_MUTABLE)
