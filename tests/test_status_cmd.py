# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for /sbtdd status read-only subcomando (sec.S.5.5)."""

from __future__ import annotations

import pytest  # noqa: F401  (used later tasks)


def test_status_cmd_module_importable() -> None:
    import status_cmd

    assert hasattr(status_cmd, "main")
    assert hasattr(status_cmd, "run")


def test_status_cmd_run_is_main_alias() -> None:
    import status_cmd

    assert callable(status_cmd.main) and callable(status_cmd.run)
