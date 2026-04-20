# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for /sbtdd close-phase subcomando (sec.S.5.3)."""

from __future__ import annotations

import pytest


def test_close_phase_cmd_module_importable() -> None:
    import close_phase_cmd

    assert hasattr(close_phase_cmd, "main")


def test_close_phase_cmd_parses_help() -> None:
    import close_phase_cmd

    with pytest.raises(SystemExit):
        close_phase_cmd.main(["--help"])
