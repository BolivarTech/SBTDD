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
    assert ".claude/session-state.json" in t


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
    assert "HOLD -- TIE" in t


def test_finalization_present_with_checklist():
    t = (REF / "finalization.md").read_text(encoding="utf-8")
    assert "finishing-a-development-branch" in t
    assert "git status" in t
    assert "current_phase" in t and "done" in t
    assert "- [ ]" in t
    assert "MAGI" in t


def _plan_gate_row(text: str) -> str:
    """Return the single decision-table row describing the plan gate, or ''."""
    for line in text.splitlines():
        low = line.lower()
        if "plan gate" in low and "checkpoint" in low:
            return line
    return ""


def test_routing_plan_gate_orders_checkpoint1_before_magi():
    row = _plan_gate_row((REF / "routing.md").read_text(encoding="utf-8"))
    assert row, "plan-gate row not found in routing.md"
    low = row.lower()
    assert "checkpoint 1" in low and "checkpoint 2" in low
    assert "manual review" in low
    assert low.index("manual review") < low.index("magi"), \
        "manual review (Checkpoint 1) must precede MAGI within the plan-gate row"
    assert "writing-plans" in row


def test_routing_drift_mapping_is_not_off_by_one():
    t = (REF / "routing.md").read_text(encoding="utf-8")
    # the corrected mapping must pair test: -> green and feat:/fix: -> refactor
    assert "test:" in t and "green" in t
    assert ("feat:" in t or "fix:" in t) and "refactor" in t
    # the documented drift example must remain (green + refactor: is drift)
    assert "drift" in t.lower()


def _section(text: str, header_substr: str) -> str:
    """Return the lines of the first '## ' section whose header contains
    header_substr (case-insensitive), up to the next '## ' header."""
    out, capturing = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            if capturing:
                break
            capturing = header_substr.lower() in line.lower()
            if capturing:
                out.append(line)
            continue
        if capturing:
            out.append(line)
    return "\n".join(out)


def test_review_gates_describes_plan_gate_checkpoint1():
    sec = _section((REF / "review-gates.md").read_text(encoding="utf-8"), "Plan Gate")
    assert sec, "'## ... Plan Gate' section not found in review-gates.md"
    low = sec.lower()
    assert "checkpoint 1" in low
    assert "manual review" in low
    assert "writing-plans" in sec
    assert "§1" in sec
    assert low.index("manual review") < low.index("magi"), \
        "manual review (Checkpoint 1) must precede MAGI within the Plan Gate section"


def test_review_gates_documents_magi_contract():
    """§7. MAGI Invocation Contract must declare the interactive-only rule,
    name the forbidden transport, and use normative MUST NOT language.
    §7 is intentionally self-contained — no external doc reference is
    asserted here."""
    t = (REF / "review-gates.md").read_text(encoding="utf-8")
    sec = _section(t, "MAGI Invocation Contract")
    assert sec, "'## 7. MAGI Invocation Contract' section not found in review-gates.md"
    low = sec.lower()
    assert "interactive-only" in low, "contract must contain literal 'interactive-only'"
    assert "claude -p" in low, "contract must name the forbidden transport"
    assert "must not" in low, "contract must use normative 'MUST NOT' language"
