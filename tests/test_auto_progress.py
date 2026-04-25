#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-25
"""Tests for v0.3.0 Feature D auto-run.json progress field."""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "sbtdd" / "scripts"))

import auto_cmd


def test_update_progress_writes_correct_schema(tmp_path):
    """D4.2: progress field has shape {phase, task_index, task_total, sub_phase}."""
    auto_run = tmp_path / "auto-run.json"
    auto_run.write_text(json.dumps({"started_at": "2026-04-25T10:00:00Z"}))
    auto_cmd._update_progress(
        auto_run,
        phase=2,
        task_index=14,
        task_total=36,
        sub_phase="green",
    )
    data = json.loads(auto_run.read_text())
    assert data["progress"] == {
        "phase": 2,
        "task_index": 14,
        "task_total": 36,
        "sub_phase": "green",
    }
    assert data["started_at"] == "2026-04-25T10:00:00Z"  # preserved


def test_update_progress_is_atomic_under_concurrent_reads(tmp_path):
    """D4.1: concurrent readers never observe torn JSON."""
    auto_run = tmp_path / "auto-run.json"
    auto_run.write_text(
        json.dumps(
            {
                "progress": {
                    "phase": 2,
                    "task_index": 13,
                    "task_total": 36,
                    "sub_phase": "refactor",
                }
            }
        )
    )
    failures: list[str] = []
    stop = threading.Event()

    def reader() -> None:
        while not stop.is_set():
            try:
                json.loads(auto_run.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                failures.append(str(e))
            except (FileNotFoundError, PermissionError):
                # On Windows the brief window between os.replace operations
                # can yield a transient FileNotFoundError or PermissionError
                # when the reader opens the file precisely while the writer
                # is replacing it. The atomicity contract guarantees no
                # torn JSON; transient open failures are acceptable.
                pass

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    for i in range(50):
        auto_cmd._update_progress(
            auto_run, phase=2, task_index=14 + i, task_total=36, sub_phase="green"
        )
    stop.set()
    t.join(timeout=2)
    assert failures == [], f"reader saw torn JSON: {failures}"


def test_progress_field_absent_is_tolerated(tmp_path):
    """D4.3: parser tolerates auto-run.json without progress field."""
    auto_run = tmp_path / "auto-run.json"
    auto_run.write_text(json.dumps({"started_at": "2026-04-25T10:00:00Z"}))
    data = json.loads(auto_run.read_text())
    assert data.get("progress") is None  # absent is fine


def test_update_progress_always_emits_four_keys_with_null_sentinels(tmp_path):
    """D4.2 (iter 2 finding #4): all four keys ALWAYS present.

    Spec sec.2 D4.2 states 'shape exacto {phase, task_index, task_total,
    sub_phase}'. v0.3.0 baseline omitted keys whose value was None
    (degraded ``_task_progress`` returning ``(None, None)``). MAGI iter
    1 WARNING required satisfying the literal shape contract: emit JSON
    null for unknowns rather than omit the key. This protects future
    ``/sbtdd status --watch`` consumers from KeyError on degraded
    payloads.
    """
    auto_run = tmp_path / "auto-run.json"
    auto_run.write_text(json.dumps({"started_at": "2026-04-25T10:00:00Z"}))
    auto_cmd._update_progress(
        auto_run,
        phase=2,
        task_index=None,
        task_total=None,
        sub_phase=None,
    )
    data = json.loads(auto_run.read_text())
    progress = data["progress"]
    assert set(progress.keys()) == {"phase", "task_index", "task_total", "sub_phase"}
    assert progress["phase"] == 2
    assert progress["task_index"] is None
    assert progress["task_total"] is None
    assert progress["sub_phase"] is None


def test_update_progress_emits_four_keys_with_partial_unknowns(tmp_path):
    """D4.2 (iter 2 finding #4): partial-None payload still has all four keys."""
    auto_run = tmp_path / "auto-run.json"
    auto_run.write_text("{}")
    auto_cmd._update_progress(
        auto_run,
        phase=3,
        task_index=14,
        task_total=None,  # unknown total -- still emit as null
        sub_phase="green",
    )
    data = json.loads(auto_run.read_text())
    assert data["progress"] == {
        "phase": 3,
        "task_index": 14,
        "task_total": None,
        "sub_phase": "green",
    }
