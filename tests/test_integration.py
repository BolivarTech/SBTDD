import json
from conftest import ROOT
from test_skill import ALLOWED_DELEGATES


def test_every_reference_linked_from_skill_exists():
    skill = (ROOT / "skills/sbtdd/SKILL.md").read_text(encoding="utf-8")
    for ref in ("routing.md", "tdd-cycle.md", "review-gates.md", "finalization.md"):
        assert ref in skill
        assert (ROOT / "skills/sbtdd/references" / ref).is_file()


def test_skill_delegates_only_to_known_skills():
    skill = (ROOT / "skills/sbtdd/SKILL.md").read_text(encoding="utf-8")
    # capture the skill name inside backticks, dropping any plugin: prefix
    # (e.g. `superpowers:brainstorming` -> brainstorming, `magi:magi` -> magi)
    import re
    cited = set(re.findall(r"`(?:[a-z-]+:)?([a-z][a-z-]+)`", skill))
    suspicious = {c for c in cited if c.endswith("-development") or c in
                  {"brainstorming", "writing-plans", "magi", "executing-plans"}}
    assert suspicious <= ALLOWED_DELEGATES


def test_init_templates_all_exist():
    init = (ROOT / "commands/sbtdd-init.md").read_text(encoding="utf-8")
    for tmpl in ("CLAUDE.local.md.tmpl", "settings.json.tmpl",
                 "spec-behavior-base.tmpl.md"):
        assert (ROOT / "templates" / tmpl).is_file()
    for stack in ("rust", "python", "cpp"):
        assert (ROOT / "templates/verification" / f"{stack}.md").is_file()


def test_manifest_parses():
    json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))


def test_referenced_rule_sections_exist_in_template():
    # drift guard: references point to CLAUDE.local.md rule sections by name;
    # those names must actually exist in the scaffolded template
    tmpl = (ROOT / "templates/CLAUDE.local.md.tmpl").read_text(encoding="utf-8")
    for section in ("Mandatory Code Standards", "session-state.json", "Commit"):
        assert section in tmpl
