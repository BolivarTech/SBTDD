"""Tests for skills/sbtdd/scripts/models.py — immutable registries."""

from __future__ import annotations

from types import MappingProxyType

import pytest


def test_commit_prefix_map_is_mapping_proxy():
    from models import COMMIT_PREFIX_MAP

    assert isinstance(COMMIT_PREFIX_MAP, MappingProxyType)


def test_commit_prefix_map_rejects_mutation():
    from models import COMMIT_PREFIX_MAP

    with pytest.raises(TypeError):
        COMMIT_PREFIX_MAP["new"] = "whatever"  # type: ignore[index]


def test_commit_prefix_map_has_required_keys():
    from models import COMMIT_PREFIX_MAP

    assert COMMIT_PREFIX_MAP["red"] == "test"
    assert COMMIT_PREFIX_MAP["green_feat"] == "feat"
    assert COMMIT_PREFIX_MAP["green_fix"] == "fix"
    assert COMMIT_PREFIX_MAP["refactor"] == "refactor"
    assert COMMIT_PREFIX_MAP["task_close"] == "chore"
