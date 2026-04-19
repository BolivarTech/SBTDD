#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for quota_detector module."""

from __future__ import annotations

from types import MappingProxyType


def test_quota_patterns_is_mapping_proxy():
    from quota_detector import QUOTA_PATTERNS

    assert isinstance(QUOTA_PATTERNS, MappingProxyType)


def test_quota_patterns_has_four_kinds():
    from quota_detector import QUOTA_PATTERNS

    assert set(QUOTA_PATTERNS.keys()) == {
        "rate_limit_429",
        "session_limit",
        "credit_exhausted",
        "server_throttle",
    }


def test_quota_patterns_are_compiled_regex():
    import re

    from quota_detector import QUOTA_PATTERNS

    for pattern in QUOTA_PATTERNS.values():
        assert isinstance(pattern, re.Pattern)
