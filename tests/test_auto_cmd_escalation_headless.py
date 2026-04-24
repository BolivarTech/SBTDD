# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-24
"""Task G9b: A8 invariant -- Feature A never invoked from ``auto_cmd``.

Two orthogonal guarantees:

1. **Static import check** -- ``auto_cmd.py`` must not import the TTY-driven
   entry point ``prompt_user`` from ``escalation_prompt``. Importing the
   headless-safe helpers (``build_escalation_context``, ``apply_decision``)
   is permitted.
2. **Behavioral check** -- driving ``auto_cmd`` through a MAGI non-convergence
   path (Loop 2 exhaustion) must never call ``prompt_user``. The function is
   patched to raise on invocation; the run must abort via the headless policy
   / ``MAGIGateError`` path instead.

Spec refs: ``spec-behavior-base.md:282`` (A8), ``~/.claude/CLAUDE.md`` INV-22.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "sbtdd" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


def _names_imported_by(module_path: Path, from_module: str) -> set[str]:
    """Return the set of names imported from ``from_module`` by the given file."""
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == from_module:
            names.update(alias.name for alias in node.names)
    return names


def test_auto_cmd_does_not_import_prompt_user() -> None:
    """A8 static guarantee: ``auto_cmd.py`` must not import any TTY-driven
    entry point from ``escalation_prompt``. Importing
    ``build_escalation_context`` / ``apply_decision`` is permitted (both are
    headless-safe); ``prompt_user`` is not."""
    imported = _names_imported_by(SCRIPTS_DIR / "auto_cmd.py", "escalation_prompt")
    assert "prompt_user" not in imported, (
        "INV-22 / A8 violation: auto_cmd imports escalation_prompt.prompt_user. "
        "auto_cmd must remain headless; use apply_decision with a headless "
        "UserDecision synthesized from .claude/magi-auto-policy.json instead."
    )


def test_auto_cmd_magi_exhaustion_never_calls_prompt_user(tmp_path: Path) -> None:
    """A8 behavioral guarantee: drive ``auto_cmd`` through a MAGI
    non-convergence path with a stubbed pre-merge loop that returns HOLD on
    every iter. ``prompt_user`` is patched to raise on invocation. The run
    must abort with ``MAGIGateError`` (or the headless policy verdict) without
    ever calling ``prompt_user``.

    **Red-phase note**: the stage helper below is a placeholder (``...``) that
    will be concretized in Step 4 (Green) using the real staging code lifted
    from ``tests/test_auto_cmd.py``. The ``...`` here makes this test FAIL at
    Red as required -- it is not a passing stub.
    """
    from tests.fixtures.skill_stubs import StubMAGI  # noqa: F401  # used by Green
    import auto_cmd  # noqa: F401  # used by Green
    import escalation_prompt

    # Stage a minimal project: state file done-with-plan, plan approved, one
    # pre-merge Loop 2 non-convergence path. Reuse existing
    # tests/fixtures/auto-runs staging helpers (lifted from
    # tests/test_auto_cmd.py setup). Concretized in Green.
    ...  # concretize: reuse _stage_auto_run(tmp_path) helper, approved plan, all tasks [x]

    def _boom(*a: object, **kw: object) -> None:
        raise AssertionError("prompt_user invoked inside auto_cmd -- INV-22 violated")

    with patch.object(escalation_prompt, "prompt_user", _boom):
        with pytest.raises(Exception):  # MAGIGateError or SystemExit
            auto_cmd.main(["--dry-run=false"])
