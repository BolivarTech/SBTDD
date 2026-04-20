#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""C++ stack TDD-Guard reporter: parse ctest JUnit XML -> test.json.

Invoked as the second command in ``verification_commands`` for
``--stack cpp`` (sec.S.4.2). Reads the file produced by
``ctest --output-junit <path>`` and writes the TDD-Guard JSON via
:mod:`reporters.tdd_guard_schema`.

v0.1 only supports the JUnit XML emitted by ``ctest`` itself; other
runners (GoogleTest direct, Catch2, bazel, meson) are out of scope
(sec.S.13 item 8).

XXE / entity expansion risk (MAGI Checkpoint 2 iter 1 WARNING -- caspar):
ctest JUnit output is trusted local input produced by the project's own
build, NOT network-received content. We use stdlib
:mod:`xml.etree.ElementTree` without ``defusedxml`` because (1) adding a
runtime dependency contradicts INV-20 ("stdlib-only on hot paths"), (2)
the input is under the same trust boundary as the source tree, and (3)
``ET.parse`` in CPython 3.9+ does not resolve external entities by default.
If v0.2 adds support for runner output received across trust boundaries
(CI agents, remote builders), swap to ``defusedxml.ElementTree.parse`` and
pin ``defusedxml>=0.7``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from errors import ValidationError
from reporters.tdd_guard_schema import (
    TestEntry,
    TestError,
    TestJSON,
    TestModule,
    write_test_json,
)


def _collect_errors(testcase: ET.Element) -> tuple[TestError, ...]:
    """Extract <failure> and <error> children as TestError entries."""
    errors: list[TestError] = []
    for tag in ("failure", "error"):
        for node in testcase.findall(tag):
            message = node.attrib.get("message", "").strip()
            body = (node.text or "").strip()
            errors.append(TestError(message=message or tag, stack=body))
    return tuple(errors)


def _state_for(testcase: ET.Element) -> str:
    """Map JUnit XML testcase children to TDD-Guard state."""
    if testcase.find("failure") is not None or testcase.find("error") is not None:
        return "failed"
    if testcase.find("skipped") is not None:
        return "skipped"
    return "passed"


def _resolve_classname(testcase: ET.Element, fallback_suite_name: str) -> str:
    """Return a non-empty classname for ``testcase`` (MAGI ckpt2 WARNING -- melchior).

    ctest ``--output-junit`` usually emits ``<testcase classname="X" ...>``,
    but some toolchains emit ``classname=""`` or omit the attribute
    entirely. In those cases fall back to the enclosing ``<testsuite>``'s
    ``name`` attribute (already available as ``module_id``).

    Args:
        testcase: The ``<testcase>`` element.
        fallback_suite_name: The enclosing suite's ``name`` attribute.

    Returns:
        A non-empty classname. ``"unknown"`` only if both classname AND
        suite name are missing/empty (pathological input).
    """
    classname = testcase.attrib.get("classname", "").strip()
    if classname:
        return classname
    if fallback_suite_name and fallback_suite_name != "unknown":
        return fallback_suite_name
    return "unknown"


def parse_junit(path: Path) -> TestJSON:
    """Parse a ctest JUnit XML file into a :class:`TestJSON` document.

    Args:
        path: Path to the JUnit XML file (typically produced by
            ``ctest --output-junit``).

    Returns:
        Fully populated :class:`TestJSON`.

    Raises:
        ValidationError: If ``path`` does not exist or the XML is malformed.
    """
    if not path.exists():
        raise ValidationError(f"JUnit XML file not found: {path}")
    if path.stat().st_size == 0:
        raise ValidationError(
            f"JUnit XML file is empty (0 bytes): {path}. "
            f"Ensure `ctest --output-junit` ran successfully before invoking "
            f"the reporter."
        )
    try:
        # Trusted local input -- see module docstring "XXE / entity expansion
        # risk" section for rationale on not using defusedxml here.
        tree = ET.parse(path)  # noqa: S314
    except ET.ParseError as exc:
        raise ValidationError(f"invalid JUnit XML in {path}: {exc}") from exc
    root = tree.getroot()
    # ctest emits <testsuites> at root; tolerate a single-<testsuite> root too.
    suites: list[ET.Element] = (
        list(root.findall("testsuite")) if root.tag == "testsuites" else [root]
    )
    modules: list[TestModule] = []
    any_failed = False
    for suite in suites:
        module_id = suite.attrib.get("name", "unknown")
        entries: list[TestEntry] = []
        for tc in suite.findall("testcase"):
            classname = _resolve_classname(tc, module_id)
            name = tc.attrib.get("name", "unknown")
            full_name = f"{classname}.{name}" if classname else name
            state = _state_for(tc)
            if state == "failed":
                any_failed = True
            entries.append(
                TestEntry(
                    name=full_name,
                    full_name=f"{module_id}::{full_name}",
                    state=state,
                    errors=_collect_errors(tc),
                )
            )
        modules.append(TestModule(module_id=module_id, tests=tuple(entries)))
    reason = "failed" if any_failed else "passed"
    return TestJSON(test_modules=tuple(modules), reason=reason)


def run(junit_path: Path, target: Path) -> int:
    """Parse JUnit XML at ``junit_path`` and write test.json at ``target``.

    Returns:
        0 on success. Non-zero reserved for future error paths; currently
        every failure raises :class:`ValidationError` which the caller
        (verification runner) catches.
    """
    doc = parse_junit(junit_path)
    write_test_json(doc, target)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point when invoked as a standalone script.

    Usage: ``python ctest_reporter.py <junit.xml> <test.json>``
    """
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        sys.stderr.write("usage: ctest_reporter.py <junit.xml> <test.json>\n")
        return 1
    return run(Path(args[0]), Path(args[1]))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
