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
    _RootCause,
)


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
