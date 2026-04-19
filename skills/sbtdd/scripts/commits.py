#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Git commit helpers enforcing sec.M.5 prefixes + INV-0/5-7 rules.

All plugin commits go through this module so validation is centralized:
- Only allowed prefixes (sec.M.5).
- English-only messages (Code Standards Git section).
- No Co-Authored-By lines (INV-7).
- No Claude/AI references (INV-7).
"""

from __future__ import annotations

from errors import ValidationError

_ALLOWED_PREFIXES: frozenset[str] = frozenset({"test", "feat", "fix", "refactor", "chore"})


def validate_prefix(prefix: str) -> None:
    """Raise ValidationError if prefix is not in the allowed set."""
    if prefix not in _ALLOWED_PREFIXES:
        raise ValidationError(
            f"commit prefix '{prefix}' not in {sorted(_ALLOWED_PREFIXES)} (sec.M.5)"
        )
