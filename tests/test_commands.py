from conftest import ROOT, frontmatter

CMD = ROOT / "commands"


def test_sbtdd_command_invokes_skill():
    t = (CMD / "sbtdd.md").read_text(encoding="utf-8")
    assert "description:" in frontmatter(t)
    assert "sbtdd" in t.lower() and "skill" in t.lower()


def test_sbtdd_init_covers_all_scaffolding_steps():
    t = (CMD / "sbtdd-init.md").read_text(encoding="utf-8")
    for sig in ("Cargo.toml", "pyproject.toml", "CMakeLists.txt"):
        assert sig in t
    for entry in ("CLAUDE.local.md", "CLAUDE.md", ".claude/", "sbtdd/", "planning/"):
        assert entry in t
    for tmpl in ("CLAUDE.local.md.tmpl", "settings.json.tmpl",
                 "spec-behavior-base.tmpl.md", "verification/"):
        assert tmpl in t
    assert "idempotent" in t.lower() or "do not overwrite" in t.lower()
    assert "merge" in t.lower()
