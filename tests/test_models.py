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


def test_verdict_rank_ordering():
    from models import VERDICT_RANK

    assert VERDICT_RANK["STRONG_NO_GO"] < VERDICT_RANK["HOLD"]
    assert VERDICT_RANK["HOLD"] < VERDICT_RANK["HOLD_TIE"]
    assert VERDICT_RANK["HOLD_TIE"] < VERDICT_RANK["GO_WITH_CAVEATS"]
    assert VERDICT_RANK["GO_WITH_CAVEATS"] < VERDICT_RANK["GO"]
    assert VERDICT_RANK["GO"] < VERDICT_RANK["STRONG_GO"]


def test_verdict_meets_threshold_positive():
    from models import verdict_meets_threshold

    assert verdict_meets_threshold("GO", "GO_WITH_CAVEATS") is True
    assert verdict_meets_threshold("GO_WITH_CAVEATS", "GO_WITH_CAVEATS") is True


def test_verdict_meets_threshold_negative():
    from models import verdict_meets_threshold

    assert verdict_meets_threshold("HOLD", "GO_WITH_CAVEATS") is False
    assert verdict_meets_threshold("STRONG_NO_GO", "GO") is False


def test_verdict_rank_is_mapping_proxy():
    from models import VERDICT_RANK

    assert isinstance(VERDICT_RANK, MappingProxyType)
