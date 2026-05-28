from conftest import ROOT, frontmatter

SKILL = ROOT / "skills/sbtdd/SKILL.md"

# the only skills the orchestrator is allowed to delegate to
ALLOWED_DELEGATES = {
    "brainstorming", "writing-plans", "magi", "test-driven-development",
    "verification-before-completion", "systematic-debugging",
    "subagent-driven-development", "executing-plans", "using-git-worktrees",
    "dispatching-parallel-agents", "requesting-code-review", "receiving-code-review",
    "finishing-a-development-branch",
}


def _txt():
    return SKILL.read_text(encoding="utf-8")


def test_frontmatter_has_name_and_description():
    fm = frontmatter(_txt())
    assert "name: sbtdd" in fm
    assert "description:" in fm
    assert "SBTDD" in fm


def test_skill_describes_five_step_flow():
    t = _txt().lower()
    for step in ("preflight", "route", "execute", "gate", "loop"):
        assert step in t


def test_delegation_table_only_references_known_skills():
    t = _txt()
    for skill in ("brainstorming", "writing-plans", "magi",
                  "test-driven-development", "requesting-code-review",
                  "finishing-a-development-branch"):
        assert skill in t


def test_skill_links_all_four_references():
    t = _txt()
    for ref in ("routing.md", "tdd-cycle.md", "review-gates.md", "finalization.md"):
        assert ref in t


def test_preflight_routes_to_init_when_uninitialized():
    t = _txt()
    assert "sbtdd-init" in t
    assert "CLAUDE.local.md" in t


def test_plan_gate_lists_manual_review_before_magi():
    row = ""
    for line in _txt().splitlines():
        if line.lower().startswith("| plan gate"):
            row = line
            break
    assert row, "plan-gate delegation row not found in SKILL.md"
    low = row.lower()
    assert "checkpoint 1" in low and "checkpoint 2" in low
    assert "manual review" in low
    assert low.index("manual review") < low.index("magi"), \
        "manual review (Checkpoint 1) must be listed before magi in the plan-gate row"


def test_skill_md_points_to_magi_contract():
    """SKILL.md must carry the MAGI interactive-only contract pointer in
    the delegation table (Plan gate AND Pre-merge review rows) AND in the
    Gates section. The literal substring 'interactive-only' must appear
    at least 3 times; review-gates.md must be referenced."""
    t = _txt()
    low = t.lower()
    assert low.count("interactive-only") >= 3, (
        f"expected ≥3 'interactive-only' pointers in SKILL.md, "
        f"found {low.count('interactive-only')}"
    )
    assert "review-gates.md" in t, "SKILL.md must reference review-gates.md"
    gates_start = low.find("### 4. gates")
    assert gates_start >= 0, "'### 4. Gates' header not found in SKILL.md"
    gates_end = low.find("### 5.", gates_start)
    gates_section = low[gates_start:gates_end] if gates_end > 0 else low[gates_start:]
    assert "interactive-only" in gates_section, \
        "Gates section must mention 'interactive-only'"
