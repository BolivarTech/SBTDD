# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for /sbtdd close-task subcomando (sec.S.5.4)."""

from __future__ import annotations

import pytest


def test_close_task_cmd_module_importable() -> None:
    import close_task_cmd

    assert hasattr(close_task_cmd, "main")
    assert hasattr(close_task_cmd, "run")


def test_close_task_cmd_help_exits_zero() -> None:
    import close_task_cmd

    with pytest.raises(SystemExit) as ei:
        close_task_cmd.main(["--help"])
    assert ei.value.code == 0
