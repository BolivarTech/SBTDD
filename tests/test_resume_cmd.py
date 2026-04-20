# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for /sbtdd resume subcommand (sec.S.5.10, INV-30)."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_resume_cmd_module_importable() -> None:
    import resume_cmd

    assert hasattr(resume_cmd, "main")


def test_resume_prints_no_session_and_exits_0_when_state_absent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import resume_cmd

    # Create plugin.local.md so plugin_local precondition passes.
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "plugin.local.md").write_text(
        "---\nstack: python\n---\n", encoding="utf-8"
    )
    rc = resume_cmd.main(["--project-root", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "no active" in out.lower() or "manual" in out.lower()


def test_resume_aborts_when_plugin_local_md_missing(tmp_path: Path) -> None:
    import resume_cmd
    from errors import PreconditionError

    with pytest.raises(PreconditionError):
        resume_cmd.main(["--project-root", str(tmp_path)])
