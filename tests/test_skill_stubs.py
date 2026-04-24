#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for the shared ``tests/fixtures/skill_stubs.py`` integration fixture.

Guarantees the stubs consumed by Tasks 47-50 behave as their contract
promises: StubSuperpowers records invocations, StubMAGI consumes its
FIFO verdict sequence, make_verdict is a convenience factory.
"""

from __future__ import annotations

import pytest


def test_skill_stubs_module_importable():
    from tests.fixtures import skill_stubs

    assert hasattr(skill_stubs, "StubSuperpowers")
    assert hasattr(skill_stubs, "StubMAGI")


def test_stub_superpowers_records_invocations(tmp_path):
    from tests.fixtures.skill_stubs import StubSuperpowers

    stub = StubSuperpowers()
    stub.brainstorming(args=["@x.md"], cwd=str(tmp_path))
    assert stub.calls == [("brainstorming", ["@x.md"], str(tmp_path))]


def test_stub_magi_returns_scripted_verdict_sequence():
    from tests.fixtures.skill_stubs import StubMAGI, make_verdict

    stub = StubMAGI(
        sequence=[
            make_verdict("HOLD", degraded=True),
            make_verdict("GO", degraded=False),
        ]
    )
    v1 = stub.invoke_magi(context_paths=[], cwd="/tmp")
    v2 = stub.invoke_magi(context_paths=[], cwd="/tmp")
    assert v1.verdict == "HOLD" and v1.degraded is True
    assert v2.verdict == "GO" and v2.degraded is False


def test_stub_magi_raises_on_exhausted_sequence():
    from tests.fixtures.skill_stubs import StubMAGI, make_verdict

    stub = StubMAGI(sequence=[make_verdict("GO")])
    stub.invoke_magi(context_paths=[], cwd="/tmp")
    with pytest.raises(IndexError):
        stub.invoke_magi(context_paths=[], cwd="/tmp")


def test_stub_spec_reviewer_sequence_consumed_fifo() -> None:
    from tests.fixtures.skill_stubs import StubSpecReviewer

    stub = StubSpecReviewer(sequence=[True, False, True])
    r1 = stub.dispatch_spec_reviewer(task_id="1", plan_path=None, repo_root=None)
    r2 = stub.dispatch_spec_reviewer(task_id="2", plan_path=None, repo_root=None)
    r3 = stub.dispatch_spec_reviewer(task_id="3", plan_path=None, repo_root=None)
    assert r1.approved is True
    assert r1.issues == ()
    assert r2.approved is False
    assert len(r2.issues) == 1
    assert r2.issues[0].severity == "MISSING"
    assert r3.approved is True


def test_stub_spec_reviewer_empty_raises() -> None:
    from tests.fixtures.skill_stubs import StubSpecReviewer

    stub = StubSpecReviewer(sequence=[])
    with pytest.raises(IndexError):
        stub.dispatch_spec_reviewer(task_id="1", plan_path=None, repo_root=None)
