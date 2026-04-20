#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""INV-26 audit trail completeness regression pin (Milestone D Task 3)."""

from __future__ import annotations

import json
from pathlib import Path

import auto_cmd


def test_auto_run_json_conforms_to_schema_on_dry_run(tmp_path: Path) -> None:
    # Dry-run short-circuits before Phase 1; no auto-run.json is
    # written. Pin that behavior: dry-run MUST not create the file
    # (Finding 4 regression).
    auto_cmd.main(["--project-root", str(tmp_path), "--dry-run"])
    assert not (tmp_path / ".claude" / "auto-run.json").exists()


def test_auto_run_audit_from_dict_on_happy_path_fixture() -> None:
    fixture_path = Path("tests/fixtures/auto-run/happy-path.json")
    data = json.loads(fixture_path.read_text("utf-8"))
    audit = auto_cmd.AutoRunAudit.from_dict(data)
    audit.validate_schema()
    assert audit.status == "success"
    assert audit.tasks_completed == 3


def test_auto_run_audit_from_dict_on_gate_blocked_fixture() -> None:
    fixture_path = Path("tests/fixtures/auto-run/gate-blocked.json")
    data = json.loads(fixture_path.read_text("utf-8"))
    audit = auto_cmd.AutoRunAudit.from_dict(data)
    audit.validate_schema()
    assert audit.status == "magi_gate_blocked"
    assert audit.accepted_conditions == 2
    assert audit.rejected_conditions == 1


def test_gate_blocked_write_records_counts(tmp_path: Path) -> None:
    # Simulate the MAGIGateError branch: _write_auto_run_audit receives
    # an AutoRunAudit with status=magi_gate_blocked + non-zero counts.
    # Validate the file shape.
    target = tmp_path / ".claude" / "auto-run.json"
    audit = auto_cmd.AutoRunAudit(
        schema_version=1,
        auto_started_at="2026-04-19T10:00:00Z",
        auto_finished_at="2026-04-19T10:20:00Z",
        status="magi_gate_blocked",
        verdict="GO_WITH_CAVEATS",
        degraded=False,
        accepted_conditions=2,
        rejected_conditions=1,
        tasks_completed=3,
        error="MAGI iter 1 produced 2 accepted condition(s).",
    )
    auto_cmd._write_auto_run_audit(target, audit)
    data = json.loads(target.read_text("utf-8"))
    assert data["accepted_conditions"] == 2
    assert data["rejected_conditions"] == 1
    assert data["tasks_completed"] == 3
    assert data["status"] == "magi_gate_blocked"
