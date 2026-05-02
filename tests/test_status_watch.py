#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-05-02
"""Unit tests for /sbtdd status --watch (sec.2.2 W1-W6)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_w3_watch_exits_zero_when_auto_run_missing(tmp_path, capsys):
    """W3: missing auto-run.json -> exit 0 with operator-friendly message."""
    from status_cmd import _watch_loop_once

    rc = _watch_loop_once(tmp_path / "missing.json", json_mode=False)
    assert rc == 0
    captured = capsys.readouterr()
    assert "no auto run in progress" in captured.err.lower()


def test_w1_watch_render_tty_contains_progress_fields():
    """W1: TTY render packs iter / phase / task / dispatch into one line."""
    from status_cmd import _watch_render_tty

    progress = {
        "iter_num": 2,
        "phase": 3,
        "task_index": 14,
        "task_total": 36,
        "dispatch_label": "magi-loop2-iter2",
        "started_at": "2026-05-01T12:00:00Z",
    }
    output = _watch_render_tty(progress)
    assert "iter 2" in output
    assert "phase 3" in output
    assert "task 14/36" in output
    assert "magi-loop2-iter2" in output


def test_w6_validates_interval_minimum():
    """W6: --interval below 0.1s rejected (sub-100ms spins CPU)."""
    from errors import ValidationError
    from status_cmd import validate_watch_interval

    with pytest.raises(ValidationError, match=">= 0.1"):
        validate_watch_interval(0.05)
    validate_watch_interval(0.1)
    validate_watch_interval(5.0)
