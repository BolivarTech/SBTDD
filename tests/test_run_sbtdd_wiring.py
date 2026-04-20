#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for Milestone C dispatcher wiring in ``run_sbtdd.py``.

Each test verifies that ``SUBCOMMAND_DISPATCH`` routes a given subcomando
to the real ``*_cmd.main`` function, replacing the Milestone B placeholder
handlers. See plan Tasks 37-45 + Task 46 cleanup.
"""

from __future__ import annotations


def test_dispatcher_routes_status_to_status_cmd():
    import run_sbtdd
    import status_cmd

    assert run_sbtdd.SUBCOMMAND_DISPATCH["status"] is status_cmd.main


def test_dispatcher_status_returns_0_with_no_state(tmp_path):
    import run_sbtdd

    rc = run_sbtdd.main(["status", "--project-root", str(tmp_path)])
    assert rc == 0


def test_dispatcher_routes_close_task_to_close_task_cmd():
    import close_task_cmd
    import run_sbtdd

    assert run_sbtdd.SUBCOMMAND_DISPATCH["close-task"] is close_task_cmd.main


def test_dispatcher_routes_close_phase_to_close_phase_cmd():
    import close_phase_cmd
    import run_sbtdd

    assert run_sbtdd.SUBCOMMAND_DISPATCH["close-phase"] is close_phase_cmd.main


def test_dispatcher_routes_init_to_init_cmd():
    import init_cmd
    import run_sbtdd

    assert run_sbtdd.SUBCOMMAND_DISPATCH["init"] is init_cmd.main


def test_dispatcher_routes_spec_to_spec_cmd():
    import run_sbtdd
    import spec_cmd

    assert run_sbtdd.SUBCOMMAND_DISPATCH["spec"] is spec_cmd.main


def test_dispatcher_routes_pre_merge_to_pre_merge_cmd():
    import pre_merge_cmd
    import run_sbtdd

    assert run_sbtdd.SUBCOMMAND_DISPATCH["pre-merge"] is pre_merge_cmd.main


def test_dispatcher_routes_finalize_to_finalize_cmd():
    import finalize_cmd
    import run_sbtdd

    assert run_sbtdd.SUBCOMMAND_DISPATCH["finalize"] is finalize_cmd.main


def test_dispatcher_routes_auto_to_auto_cmd():
    import auto_cmd
    import run_sbtdd

    assert run_sbtdd.SUBCOMMAND_DISPATCH["auto"] is auto_cmd.main


def test_dispatcher_routes_resume_to_resume_cmd():
    import resume_cmd
    import run_sbtdd

    assert run_sbtdd.SUBCOMMAND_DISPATCH["resume"] is resume_cmd.main


def test_default_handler_factory_is_removed():
    import run_sbtdd

    assert not hasattr(run_sbtdd, "_default_handler_factory")


def test_replace_point_marker_is_removed():
    import inspect

    import run_sbtdd

    src = inspect.getsource(run_sbtdd)
    assert "MILESTONE-C-REPLACE-POINT" not in src


def test_all_cmd_modules_reference_spec_section_in_docstring():
    """Every *_cmd module must cite its spec section (sec.S.*) in the module docstring."""
    import ast
    import importlib

    for mod_name in (
        "status_cmd",
        "close_task_cmd",
        "close_phase_cmd",
        "init_cmd",
        "spec_cmd",
        "pre_merge_cmd",
        "finalize_cmd",
        "auto_cmd",
        "resume_cmd",
    ):
        mod = importlib.import_module(mod_name)
        assert mod.__file__ is not None
        with open(mod.__file__, encoding="utf-8") as f:
            src = f.read()
        doc = ast.get_docstring(ast.parse(src))
        assert doc is not None, f"{mod_name}: missing module docstring"
        assert "sec.S." in doc, f"{mod_name}: docstring lacks sec.S. reference"
