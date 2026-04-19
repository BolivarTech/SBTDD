#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Idempotent merge of .claude/settings.json (sec.S.5.1 Fase 3, sec.S.7.2).

When init runs on a project that already has settings.json with user
hooks, we must preserve those hooks and ADD ours — never overwrite.
Subsequent runs with identical inputs must produce byte-identical
output (idempotency invariant).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_existing(path: Path | str) -> dict[str, Any]:
    """Read existing settings.json or return {} if missing.

    Args:
        path: Path to settings.json.

    Returns:
        Parsed dict, or empty dict if the file does not exist.

    Raises:
        json.JSONDecodeError: If the file exists but is malformed.
    """
    p = Path(path)
    if not p.exists():
        return {}
    data: dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    return data
