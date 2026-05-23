"""Structural-validation tests for skills/sbtdd/references/*.md."""
from conftest import ROOT

REF = ROOT / "skills/sbtdd/references"


def test_routing_present_with_state_detection_table():
    t = (REF / "routing.md").read_text(encoding="utf-8")
    for art in ("spec-behavior-base", "spec-behavior.md", "claude-plan-tdd-org",
                "claude-plan-tdd.md", "session-state.json"):
        assert art in t
    assert "authority" in t.lower()
    assert "drift" in t.lower()
    assert "abort" in t.lower() and "escalate" in t.lower()


def test_tdd_cycle_present_with_phase_rules_and_close():
    t = (REF / "tdd-cycle.md").read_text(encoding="utf-8")
    for phase in ("Red", "Green", "Refactor"):
        assert phase in t
    assert "verification-before-completion" in t
    assert "atomic commit" in t.lower()
    assert "session-state.json" in t
    assert "worktree" in t.lower()
    assert "§5" in t or "CLAUDE.local.md" in t


def test_review_gates_present_with_dual_loop_and_verdicts():
    t = (REF / "review-gates.md").read_text(encoding="utf-8")
    assert "requesting-code-review" in t
    assert "receiving-code-review" in t
    assert "magi" in t.lower()
    assert "clean to go" in t.lower()
    assert "GO WITH CAVEATS" in t
    for verdict in ("STRONG GO", "HOLD", "STRONG NO-GO"):
        assert verdict in t
    assert "3 iterations" in t.lower() or "three iterations" in t.lower()
