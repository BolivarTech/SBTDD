#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-23
"""Interactive MAGI escalation prompt (Feature A, v0.2.0).

Fires when INV-11 safety valve exhausts in `/sbtdd spec` (Checkpoint 2) or
`/sbtdd pre-merge` (Loop 2). INV-22 forbids running inside `/sbtdd auto`:
auto invocations consult `.claude/magi-auto-policy.json` instead.

Public API:
    build_escalation_context(iterations, plan_id, context) -> EscalationContext
    format_escalation_message(ctx) -> str
    prompt_user(ctx, options) -> UserDecision
    apply_decision(decision, ctx, root) -> int  # writes audit artifact

Precedent: Milestone D Checkpoint 2 iter 3 chat escalation (commit 5d7bfc4).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Literal


class _RootCause(enum.Enum):
    INFRA_TRANSIENT = "infra_transient"  # same agent fails across iters
    PLAN_VS_SPEC = "plan_vs_spec"  # CRITICAL findings persist
    STRUCTURAL_DEFECT = "structural_defect"  # STRONG_NO_GO from >=1 agent
    SPEC_AMBIGUITY = "spec_ambiguity"  # confidence trending down


_ContextLit = Literal["checkpoint2", "pre-merge", "auto"]
_ActionLit = Literal["override", "retry", "abandon", "alternative"]


@dataclass(frozen=True)
class EscalationOption:
    letter: str  # 'a' | 'b' | 'c' | 'd'
    action: _ActionLit
    rationale: str  # shown in the menu after the action verb
    caveat: str = ""  # optional consequence / tradeoff line


@dataclass(frozen=True)
class EscalationContext:
    iterations: tuple[dict[str, Any], ...]  # per-iter verdict snapshots
    plan_id: str
    context: _ContextLit
    per_agent_verdicts: tuple[tuple[str, str], ...]  # (agent_name, verdict)
    findings: tuple[tuple[str, str], ...]  # (severity, text)
    root_cause: _RootCause


@dataclass(frozen=True)
class UserDecision:
    chosen_option: str
    action: _ActionLit
    reason: str
