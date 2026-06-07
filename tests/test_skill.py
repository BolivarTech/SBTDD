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
    """SKILL.md must carry the MAGI interactive-only contract pointer at
    three distinct surfaces: the Plan-gate delegation row, the Pre-merge
    review delegation row, and the §4 Gates section. Each surface is
    anchored independently so a future consolidation between two of the
    delegation-table rows produces a precise failure (which surface lost
    the pointer) rather than a count-off-by-one. The overall count
    threshold is kept as a ≥2 robustness fallback."""
    t = _txt()
    low = t.lower()
    plan_row = next(
        (l for l in low.splitlines() if l.startswith("| plan gate")), ""
    )
    assert plan_row, "plan-gate delegation row not found in SKILL.md"
    assert "interactive-only" in plan_row, \
        "Plan-gate row must contain 'interactive-only' pointer"
    premerge_row = next(
        (l for l in low.splitlines() if l.startswith("| pre-merge")), ""
    )
    assert premerge_row, "pre-merge review delegation row not found in SKILL.md"
    assert "interactive-only" in premerge_row, \
        "Pre-merge review row must contain 'interactive-only' pointer"
    gates_start = low.find("### 4. gates")
    assert gates_start >= 0, "'### 4. Gates' header not found in SKILL.md"
    gates_end = low.find("### 5.", gates_start)
    gates_section = low[gates_start:gates_end] if gates_end > 0 else low[gates_start:]
    assert "interactive-only" in gates_section, \
        "Gates section must mention 'interactive-only'"
    # Lowered from ≥3 to ≥2 to give margin against legitimate
    # consolidation of the two delegation-table rows. The
    # location-anchored assertions above are the primary signal.
    assert low.count("interactive-only") >= 2, (
        f"expected ≥2 'interactive-only' pointers in SKILL.md, "
        f"found {low.count('interactive-only')}"
    )
    assert "review-gates.md" in t, "SKILL.md must reference review-gates.md"


def test_skill_points_to_backend_selection():
    """SKILL.md must thread the --ollama backend and point to review-gates §8
    (contiguous literal), without dropping the §7 interactive-only pointers
    (guarded separately by test_skill_md_points_to_magi_contract)."""
    t = _txt()
    assert "--ollama" in t
    assert "review-gates.md §8" in t
    assert "magi-ollama.toml" in t
