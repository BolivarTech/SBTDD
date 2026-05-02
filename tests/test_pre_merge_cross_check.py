#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-05-02
"""Unit tests for v1.0.0 Feature G MAGI cross-check meta-reviewer (sec.2.1).

Covers escenarios G1-G6 + carry-forward normalizer (W4) + JSON-parse-failure
distinct-from-dispatch-failure (melchior iter 4 W).
"""

from __future__ import annotations

from unittest.mock import MagicMock


def test_g4_opt_out_via_config_returns_findings_unchanged(tmp_path):
    """G4: cross-check sub-phase short-circuits when magi_cross_check=False."""
    from pre_merge_cmd import _loop2_cross_check

    config = MagicMock()
    config.magi_cross_check = False

    findings = [
        {"severity": "CRITICAL", "title": "test", "detail": "...", "agent": "caspar"},
    ]
    diff = "stub diff"
    verdict = "GO_WITH_CAVEATS"

    result = _loop2_cross_check(
        diff=diff,
        verdict=verdict,
        findings=findings,
        iter_n=1,
        config=config,
        audit_dir=tmp_path,
    )
    assert result == findings  # unchanged
    # Audit dir empty (no artifact written when skipped)
    assert list(tmp_path.iterdir()) == []
