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
