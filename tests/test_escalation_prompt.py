#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-23
"""Unit tests for escalation_prompt module (Feature A)."""

from __future__ import annotations

import pytest

from escalation_prompt import (
    EscalationContext,
    EscalationOption,
    UserDecision,
    _classify_root_cause,
    _RootCause,
    build_escalation_context,
)
from magi_dispatch import MAGIVerdict


def test_escalation_context_is_frozen() -> None:
    ctx = EscalationContext(
        iterations=(),
        plan_id="A",
        context="checkpoint2",
        per_agent_verdicts=(),
        findings=(),
        root_cause=_RootCause.INFRA_TRANSIENT,
    )
    with pytest.raises((AttributeError, Exception)):
        ctx.plan_id = "B"  # frozen


def test_user_decision_is_frozen_and_carries_reason() -> None:
    d = UserDecision(chosen_option="a", action="override", reason="caspar JSON bug again")
    assert d.chosen_option == "a"
    assert d.reason == "caspar JSON bug again"
    with pytest.raises((AttributeError, Exception)):
        d.reason = "changed"


def test_escalation_option_has_letter_action_rationale() -> None:
    opt = EscalationOption(letter="a", action="override", rationale="INV-0 user authority")
    assert opt.letter == "a"
    assert opt.action == "override"


def _mkv(
    verdict: str, degraded: bool = False, findings: tuple = (), conds: tuple = ()
) -> MAGIVerdict:
    return MAGIVerdict(
        verdict=verdict, degraded=degraded, conditions=conds, findings=findings, raw_output=""
    )


def test_classify_infra_transient_when_degraded_repeats() -> None:
    iters = [
        _mkv("HOLD", degraded=True),
        _mkv("GO", degraded=False),
        _mkv("HOLD", degraded=True),
    ]
    assert _classify_root_cause(iters) == _RootCause.INFRA_TRANSIENT


def test_classify_structural_defect_when_strong_no_go_present() -> None:
    iters = [_mkv("STRONG_NO_GO")]
    assert _classify_root_cause(iters) == _RootCause.STRUCTURAL_DEFECT


def test_classify_plan_vs_spec_when_critical_findings_persist() -> None:
    critical = ({"severity": "CRITICAL", "text": "f"},)
    iters = [_mkv("HOLD", findings=critical), _mkv("HOLD", findings=critical)]
    assert _classify_root_cause(iters) == _RootCause.PLAN_VS_SPEC


def test_build_escalation_context_checkpoint2_returns_frozen_struct() -> None:
    iters = [_mkv("HOLD_TIE"), _mkv("HOLD"), _mkv("HOLD_TIE")]
    ctx = build_escalation_context(iterations=iters, plan_id="A", context="checkpoint2")
    assert ctx.plan_id == "A"
    assert ctx.context == "checkpoint2"
    assert len(ctx.iterations) == 3
    assert ctx.root_cause in set(_RootCause)
