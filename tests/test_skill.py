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
