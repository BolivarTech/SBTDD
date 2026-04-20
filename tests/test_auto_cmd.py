# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for /sbtdd auto subcommand (sec.S.5.8, INV-22..26)."""

from __future__ import annotations

import subprocess

import pytest


def test_auto_cmd_module_importable() -> None:
    import auto_cmd

    assert hasattr(auto_cmd, "main")


def test_auto_dry_run_short_circuits_before_preflight(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dry-run must return 0 WITHOUT invoking subprocess/preflight (Finding 4).

    Guards against wasted time when the user only wants a plan preview
    on a machine where toolchain checks are slow or unavailable.
    """
    import auto_cmd

    original_run = subprocess.run

    def _boom(*a: object, **k: object) -> object:
        raise AssertionError("dry-run must not invoke subprocess.run")

    monkeypatch.setattr(subprocess, "run", _boom)
    rc = auto_cmd.main(["--project-root", str(tmp_path), "--dry-run"])
    assert rc == 0
    assert not (tmp_path / ".claude" / "auto-run.json").exists()  # type: ignore[operator]
    # Restore for downstream tests.
    monkeypatch.setattr(subprocess, "run", original_run)


def test_auto_parses_magi_max_iterations_flag() -> None:
    import auto_cmd

    ns = auto_cmd._build_parser().parse_args(["--magi-max-iterations", "7"])
    assert ns.magi_max_iterations == 7
