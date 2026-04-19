#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Exception hierarchy for sbtdd-workflow plugin.

All plugin exceptions derive from :class:`SBTDDError` so dispatchers can
catch the whole hierarchy with a single except clause (sec.S.8.4). Each
subclass maps to a specific exit code per sec.S.11.1 taxonomy.
"""

from __future__ import annotations


class SBTDDError(Exception):
    """Base exception for all plugin errors. Subclasses map to exit codes."""


class ValidationError(SBTDDError):
    """Schema or input validation failed (exit 1, USER_ERROR)."""
