#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-24
"""Guard: no literal ``...`` placeholder statements land in committed tests.

MAGI Loop 2 iter 1 CRITICAL finding (2026-04-24, three concurring agents):
plans emitted by ``/writing-plans`` sometimes decompose test bodies into
``...  # skeleton; concretize ...`` markers that the implementer is
expected to replace before the red commit. Python's ``Ellipsis`` is a
valid expression, so ruff/mypy never flag it and pytest collects the
test — at which point any call site hits ``TypeError`` or silent pass.

This test walks every Python file under ``tests/`` (including fixtures
and helpers but excluding this file itself to avoid a self-match), parses
it via :mod:`ast`, and asserts no function body contains a standalone
``...`` expression statement (``ast.Expr(value=ast.Constant(value=Ellipsis))``).
Docstrings are safe because ``ast.Expr`` around a string literal is
distinct from one around ``Ellipsis``. Type-stub annotations using
``...`` in function signatures (e.g. ``def f(x: int = ...)``) are
handled by ast.arguments and never show up as an ``ast.Expr`` inside a
body, so they are out of scope.

When this test fails, the message lists the offending file + line numbers
so the implementer can replace each placeholder with either a concrete
fixture invocation or a ``pytest.skip("<reason>")`` call that fails
loudly instead of silently passing.
"""

from __future__ import annotations

import ast
from pathlib import Path


_TESTS_DIR = Path(__file__).resolve().parent
_SELF = Path(__file__).resolve()


def _walk_function_bodies(tree: ast.AST) -> list[tuple[int, ast.stmt]]:
    """Yield (lineno, stmt) for every statement inside a function body.

    Recurses into nested functions and class methods. Module-level
    statements are excluded because a bare ``...`` at module scope is
    usually a type-stub pattern (``.pyi``-style), not an unfinished test.
    """
    collected: list[tuple[int, ast.stmt]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for stmt in node.body:
                collected.append((stmt.lineno, stmt))
    return collected


def _find_ellipsis_placeholders(path: Path) -> list[int]:
    """Return line numbers of standalone ``...`` expression statements.

    A placeholder is ``ast.Expr(value=ast.Constant(value=Ellipsis))``
    appearing as a function-body statement (not a module-level stmt,
    not a docstring, not an annotation default).
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    hits: list[int] = []
    for lineno, stmt in _walk_function_bodies(tree):
        if (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and stmt.value.value is ...
        ):
            hits.append(lineno)
    return hits


def test_no_literal_ellipsis_placeholders_in_tests() -> None:
    offenders: dict[str, list[int]] = {}
    for path in _TESTS_DIR.rglob("*.py"):
        if path.resolve() == _SELF:
            continue
        hits = _find_ellipsis_placeholders(path)
        if hits:
            rel = path.relative_to(_TESTS_DIR.parent)
            offenders[str(rel)] = hits
    assert not offenders, (
        "Literal ``...`` placeholder statements found in test files.\n"
        "These are almost always unfinished ``# skeleton; concretize ...``\n"
        "markers from plan scaffolding that were never replaced with real\n"
        "fixture calls or ``pytest.skip('<reason>')``. Replace each hit\n"
        "before landing.\n\n"
        + "\n".join(f"  {file}: {lines}" for file, lines in sorted(offenders.items()))
    )
