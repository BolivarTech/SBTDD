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

from magi_dispatch import MAGIVerdict


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


def _classify_root_cause(iterations: list[MAGIVerdict]) -> _RootCause:
    """Infer the dominant failure mode across iterations."""
    if any(v.verdict == "STRONG_NO_GO" for v in iterations):
        return _RootCause.STRUCTURAL_DEFECT
    degraded_count = sum(1 for v in iterations if v.degraded)
    if degraded_count >= 2 and degraded_count >= len(iterations) / 2:
        return _RootCause.INFRA_TRANSIENT
    critical_across = [
        any(str(f.get("severity", "")).upper() == "CRITICAL" for f in v.findings)
        for v in iterations
    ]
    if sum(critical_across) >= 2:
        return _RootCause.PLAN_VS_SPEC
    return _RootCause.SPEC_AMBIGUITY


def build_escalation_context(
    iterations: list[MAGIVerdict],
    plan_id: str,
    context: _ContextLit,
) -> EscalationContext:
    """Collect iter history + classify root cause."""
    snapshots = tuple(
        {
            "verdict": v.verdict,
            "degraded": v.degraded,
            "n_conditions": len(v.conditions),
            "n_findings": len(v.findings),
        }
        for v in iterations
    )
    per_agent: tuple[tuple[str, str], ...] = ()  # v0.2: MAGI does not expose per-agent breakdown
    findings = tuple(
        (str(f.get("severity", "INFO")).upper(), str(f.get("text", f)))
        for v in iterations
        for f in v.findings
    )
    return EscalationContext(
        iterations=snapshots,
        plan_id=plan_id,
        context=context,
        per_agent_verdicts=per_agent,
        findings=findings,
        root_cause=_classify_root_cause(iterations),
    )
